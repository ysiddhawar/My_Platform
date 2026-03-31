from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from execution_tools.position_sizer import PositionSizer
from models.missed_opportunity import MissedOpportunity
from persistence_layer.missed_opportunity_repository import MissedOpportunityRepository


class MissedOpportunityCaptureServiceError(Exception):
    pass


class MissedOpportunityCaptureService:
    def __init__(
        self,
        repository: MissedOpportunityRepository,
        position_sizer: PositionSizer,
    ):
        self._repository = repository
        self._position_sizer = position_sizer

    def capture(
        self,
        account_id: str,
        broker_id: str,
        symbol: str,
        market_type: str,
        side: str,
        strategy_name: str,
        probability_bucket: str,
        entry_price: float,
        stop_loss_price: float,
        target_price: float,
        account_balance: float,
        observed_at: Optional[datetime] = None,
        timezone_name: str = 'UTC',
        exit_price: Optional[float] = None,
        exit_at: Optional[datetime] = None,
        exit_reason: Optional[str] = None,
        checklist_items: Optional[List[str]] = None,
        notes: Optional[str] = None,
        instrument_overrides: Optional[Dict[str, Any]] = None,
        cost_overrides: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not strategy_name:
            raise MissedOpportunityCaptureServiceError('strategy_name is required')
        if not probability_bucket:
            raise MissedOpportunityCaptureServiceError('probability_bucket is required')

        plan = self._position_sizer.preview_position_plan(
            account_balance=account_balance,
            symbol=symbol,
            market_type=market_type,
            side=side,
            entry_price=entry_price,
            stop_loss_price=stop_loss_price,
            target_price=target_price,
            probability_bucket=probability_bucket,
            explicit_costs=cost_overrides,
            instrument_overrides=instrument_overrides,
        )

        merged_metadata = dict(metadata or {})
        merged_metadata['position_plan'] = plan
        opportunity = MissedOpportunity(
            account_id=account_id,
            broker_id=broker_id,
            symbol=symbol,
            market_type=market_type,
            side=side,
            strategy_name=strategy_name,
            probability_bucket=probability_bucket,
            entry_price=entry_price,
            stop_loss_price=stop_loss_price,
            target_price=target_price,
            minimum_target_price=plan.get('minimum_target_price'),
            observed_at=observed_at or datetime.now(timezone.utc),
            timezone_name=timezone_name,
            exit_price=exit_price,
            exit_at=exit_at,
            exit_reason=exit_reason,
            checklist_items=list(checklist_items or []),
            notes=notes,
            metadata=merged_metadata,
        )
        self._repository.save_opportunity(opportunity)
        return opportunity.to_dict()
