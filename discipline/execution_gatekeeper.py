from __future__ import annotations

from typing import Dict, Any, Optional

from models.execution_event import ExecutionEvent
from models.strategy import Strategy
from models.account import Account
from models.trade import Trade
from models.discipline_report import DisciplineReport
from models.decision_report import DecisionReport

from discipline.rules_engine import DisciplineRulesEngine
from discipline.strictness_controller import StrictnessController


class ExecutionGatekeeperError(Exception):
    pass


class ExecutionGatekeeper:
    """
    Institutional Execution Gatekeeper

    Responsibilities:
    - Orchestrate discipline evaluation
    - Apply strictness logic
    - Prevent unauthorized trade execution
    - Create Trade snapshot only if approved
    - Maintain deterministic governance pipeline
    """

    def __init__(
        self,
        rules_engine: Optional[DisciplineRulesEngine] = None,
        strictness_controller: Optional[StrictnessController] = None,
    ):

        self._rules_engine = rules_engine or DisciplineRulesEngine()
        self._strictness_controller = (
            strictness_controller or StrictnessController()
        )

    # =====================================================
    # MAIN ENTRY
    # =====================================================

    def process(
        self,
        event: ExecutionEvent,
        strategy: Strategy,
        account: Account,
    ) -> Dict[str, Any]:
        """
        Full governance pipeline:

        Returns:
            {
                "approved": bool,
                "trade": Optional[Trade],
                "discipline_report": DisciplineReport,
                "decision_report": DecisionReport
            }
        """

        if not account.is_active:
            raise ExecutionGatekeeperError("Account is inactive.")

        # -------------------------------------------------
        # STEP 1: DISCIPLINE RULES
        # -------------------------------------------------

        discipline_report: DisciplineReport = (
            self._rules_engine.evaluate(event, strategy, account)
        )

        # -------------------------------------------------
        # STEP 2: STRICTNESS CONTROLLER
        # -------------------------------------------------

        decision_report: DecisionReport = (
            self._strictness_controller.evaluate(
                event,
                account,
                discipline_report
            )
        )

        # -------------------------------------------------
        # STEP 3: FINAL APPROVAL CHECK
        # -------------------------------------------------

        if not decision_report.approved:
            return {
                "approved": False,
                "trade": None,
                "discipline_report": discipline_report,
                "decision_report": decision_report,
            }

        # -------------------------------------------------
        # STEP 4: TRADE SNAPSHOT CREATION
        # -------------------------------------------------

        trade = self._create_trade_from_event(
            event,
            strategy,
            account,
        )

        # -------------------------------------------------
        # STEP 5: ACCOUNT UPDATE
        # -------------------------------------------------

        account.increment_position(
            strategy_tag=strategy.name,
            exposure=trade.to_dict().get("risk_amount") or 0.0
        )

        return {
            "approved": True,
            "trade": trade,
            "discipline_report": discipline_report,
            "decision_report": decision_report,
        }

    def is_trade_allowed(self, trade_request: Dict[str, Any]) -> bool:
        if not isinstance(trade_request, dict):
            return False
        if not trade_request.get("discipline_mode_enabled", False):
            return True
        required = (
            trade_request.get("strategy_setup") or trade_request.get("setup_name"),
            trade_request.get("probability_bucket"),
            trade_request.get("selected_checklist"),
        )
        return all(required)

    # =====================================================
    # TRADE CREATION
    # =====================================================

    def _create_trade_from_event(
        self,
        event: ExecutionEvent,
        strategy: Strategy,
        account: Account,
    ) -> Trade:

        event_data = event.to_dict()

        trade = Trade(
            account_id=event_data["account_id"],
            broker_id=event_data["broker_id"],
            symbol=event_data["symbol"],
            market_type=event_data["market_type"],
            side=event_data["side"],
            strategy_tag=strategy.name,
            setup_name=event_data["setup_name"],
            entry_price=event_data["intended_entry_price"],
            quantity=event_data["intended_quantity"],
            lot_size=event_data["intended_lot_size"],
            leverage_used=event_data["intended_leverage"],
            stop_loss_at_entry=event_data["intended_stop_loss"],
            target_at_entry=event_data["intended_target"],
            slippage_at_entry=0.0,
            fees=0.0,
            commission=0.0,
            swaps=0.0,
            checklist_before=event_data["selected_checklist"],
            probability_bucket=event_data.get("probability_bucket"),
            pre_trade_capture=event_data.get("metadata", {}).get("pre_trade_capture")
            or event_data.get("pre_trade_capture"),
            post_trade_capture=event_data.get("post_trade_capture"),
            line_history=event_data.get("metadata", {}).get("line_history")
            or event_data.get("line_history"),
            minimum_target_price=event_data.get("metadata", {}).get("minimum_target_price")
            or event_data.get("minimum_target_price"),
            minimum_target_reward=event_data.get("metadata", {}).get("minimum_target_reward")
            or event_data.get("minimum_target_reward"),
            notes=event_data.get("metadata", {}).get("notes") or event_data.get("notes"),
            volatility_regime_at_entry=event_data.get("volatility_regime"),
            equity_at_entry=event_data.get("equity_snapshot"),
            drawdown_at_entry=event_data.get("drawdown_snapshot"),
            open_positions_count=event_data.get("open_positions_count"),
            correlation_exposure_snapshot=event_data.get(
                "correlation_exposure_snapshot"
            ),
        )

        return trade
