from __future__ import annotations

from typing import Dict, Any, List, Optional
from copy import deepcopy
from datetime import datetime, timezone

from core.execution_engine import ExecutionEngine
from models.ai_prescription import AIPrescription
from models.execution_event import ExecutionEvent
from execution_tools.position_sizer import PositionSizer
from execution_tools.risk_line_manager import RiskLineManager
from execution_tools.slippage_guard import SlippageGuard


class PrescriptionExecutorError(Exception):
    pass


class PrescriptionExecutor:
    """
    Institutional Prescription Executor

    Responsibilities:
    - Validate user-confirmed prescription
    - Allow selective application (B)
    - Allow user-modified values (C)
    - Apply safely to execution tools
    - Emit execution event
    - Remain deterministic and auditable
    """

    def __init__(
        self,
        position_sizer: PositionSizer,
        risk_line_manager: RiskLineManager,
        slippage_guard: SlippageGuard,
        execution_engine: Optional[ExecutionEngine] = None,
    ):
        self.position_sizer = position_sizer
        self.risk_line_manager = risk_line_manager
        self.slippage_guard = slippage_guard
        self.execution_engine = execution_engine

    # ==========================================================
    # PUBLIC ENTRY
    # ==========================================================

    def apply_prescription(
        self,
        prescription: AIPrescription,
        selected_actions: List[str],
        user_overrides: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:

        if not isinstance(prescription, AIPrescription):
            raise PrescriptionExecutorError("Invalid prescription object")

        user_overrides = user_overrides or {}

        original_config = self._snapshot_config()

        applied_actions = []

        for action in prescription.actions:

            action_type = action.get("type")

            if action_type not in selected_actions:
                continue

            updated_action = deepcopy(action)

            # Apply user override if provided
            if action_type in user_overrides:
                updated_action.update(user_overrides[action_type])

            self._apply_action(updated_action)

            applied_actions.append(updated_action)

        new_config = self._snapshot_config()

        self._emit_execution_event(
            original_config=original_config,
            new_config=new_config,
            applied_actions=applied_actions,
            user_id=user_id,
        )

        return {
            "status": "success",
            "applied_actions": applied_actions,
            "previous_config": original_config,
            "updated_config": new_config,
        }

    # ==========================================================
    # INTERNAL ACTION HANDLER
    # ==========================================================

    def _apply_action(self, action: Dict[str, Any]):

        action_type = action.get("type")

        if action_type == "set_fixed_risk":
            self.position_sizer.update_config(
                max_risk_percent=action.get("recommended_risk_percent")
            )

        elif action_type == "reduce_risk":
            self.position_sizer.update_config(
                max_risk_percent=action.get("recommended_risk_percent")
            )

        elif action_type == "reduce_leverage":
            self.position_sizer.update_config(
                leverage_cap=action.get("leverage_cap", 1.0)
            )

        elif action_type == "capital_protection_mode":
            self.position_sizer.update_config(
                max_risk_percent=action.get("recommended_risk_percent", 0.25)
            )

        elif action_type == "reduce_correlation_exposure":
            self.risk_line_manager.update_config(
                correlation_exposure_cap=action.get("correlation_exposure_cap", 0.5)
            )

        elif action_type == "update_slippage_limit":
            self.slippage_guard.update_config(
                max_slippage_cost=action.get("max_slippage_cost")
            )

        elif action_type == "update_spread_limit":
            self.slippage_guard.update_config(
                max_spread=action.get("max_spread")
            )

        elif action_type == "update_trade_limits":
            self.position_sizer.update_config(
                max_number_of_trades=action.get("max_number_of_trades"),
                max_number_of_trades_per_symbol=action.get("max_number_of_trades_per_symbol"),
            )

        elif action_type == "update_volume_limits":
            self.position_sizer.update_config(
                max_volume=action.get("max_volume"),
                max_volume_per_symbol=action.get("max_volume_per_symbol"),
            )

        elif action_type == "update_drawdown_limits":
            self.risk_line_manager.update_config(
                max_daily_drawdown=action.get("max_daily_drawdown"),
                max_weekly_drawdown=action.get("max_weekly_drawdown"),
            )

        elif action_type == "cooldown_mode":
            self.risk_line_manager.update_config(
                cooldown_period=action.get("cooldown_period")
            )

        else:
            # Unknown action safely ignored
            return

    # ==========================================================
    # CONFIG SNAPSHOT
    # ==========================================================

    def _snapshot_config(self) -> Dict[str, Any]:

        return {
            "position_sizer": self.position_sizer.get_config(),
            "risk_line_manager": self.risk_line_manager.get_config(),
            "slippage_guard": self.slippage_guard.get_config(),
        }

    # ==========================================================
    # EVENT EMISSION
    # ==========================================================

    def _emit_execution_event(
        self,
        original_config: Dict[str, Any],
        new_config: Dict[str, Any],
        applied_actions: List[Dict[str, Any]],
        user_id: Optional[str],
    ):

        event = ExecutionEvent(
            event_type="AI_PRESCRIPTION_APPLIED",
            timestamp=datetime.now(timezone.utc),
            metadata={
                "original_config": original_config,
                "new_config": new_config,
                "applied_actions": applied_actions,
                "user_id": user_id,
            },
        )

        if self.execution_engine:
            self.execution_engine.process_event(event)
