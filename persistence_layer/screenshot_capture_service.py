from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional

from models.screenshot_capture_request import ScreenshotCaptureRequest
from models.trade_attachment import AttachmentMarker, TradeAttachment
from persistence_layer.attachment_repository import AttachmentRepository
from persistence_layer.screenshot_capture_repository import ScreenshotCaptureRepository
from persistence_layer.trade_repository import TradeRepository


class ScreenshotCaptureService:
    def __init__(
        self,
        trade_repository: TradeRepository,
        attachment_repository: AttachmentRepository,
        capture_repository: ScreenshotCaptureRepository,
    ):
        self._trade_repository = trade_repository
        self._attachment_repository = attachment_repository
        self._capture_repository = capture_repository

    def request_for_trade(
        self,
        trade_id: str,
        requested_by: str = "system",
        trigger: str = "trade_closed",
        source_hint: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> Dict:
        trade = self._trade_repository.get_trade(trade_id)
        if trade is None:
            raise ValueError("Trade not found")
        trade_data = trade.to_dict()
        request = ScreenshotCaptureRequest(
            account_id=trade_data["account_id"],
            trade_id=trade_id,
            broker_id=trade_data.get("broker_id"),
            market_type=trade_data.get("market_type"),
            symbol=trade_data["symbol"],
            requested_by=requested_by,
            trigger=trigger,
            source_hint=source_hint,
            metadata={
                "entry_price": trade_data.get("entry_price"),
                "stop_loss_at_entry": trade_data.get("stop_loss_at_entry"),
                "target_at_entry": trade_data.get("target_at_entry"),
                "exit_price": trade_data.get("exit_price"),
                "close_classification": trade_data.get("close_classification"),
                **(metadata or {}),
            },
        )
        self._capture_repository.save(request)
        return request.to_dict()

    def ingest_capture(
        self,
        request_id: str,
        file_name: str,
        storage_path: str,
        source: str,
        content_type: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> Dict:
        request = self._capture_repository.get(request_id)
        if request is None:
            raise ValueError("Capture request not found")
        trade = self._trade_repository.get_trade(request.trade_id)
        if trade is None:
            raise ValueError("Trade not found")
        trade_data = trade.to_dict()
        markers = self._build_default_markers(trade_data)
        attachment = TradeAttachment(
            account_id=request.account_id,
            trade_id=request.trade_id,
            attachment_type="screenshot",
            file_name=file_name,
            storage_path=storage_path,
            source=source,
            broker_id=request.broker_id,
            market_type=request.market_type,
            content_type=content_type,
            description=description,
            is_auto_captured=True,
            markers=markers,
            metadata={"capture_request_id": request_id, **(metadata or {})},
        )
        self._attachment_repository.save(attachment)
        completed_request = ScreenshotCaptureRequest(
            account_id=request.account_id,
            trade_id=request.trade_id,
            broker_id=request.broker_id,
            market_type=request.market_type,
            symbol=request.symbol,
            status="completed",
            trigger=request.trigger,
            requested_by=request.requested_by,
            source_hint=request.source_hint,
            claimed_by=request.claimed_by,
            requested_at=request.requested_at,
            claimed_at=request.claimed_at,
            completed_at=datetime.now(timezone.utc),
            failure_reason=None,
            metadata=request.metadata,
            request_id=request.request_id,
        )
        self._capture_repository.save(completed_request)
        return {
            "request": completed_request.to_dict(),
            "attachment": attachment.to_dict(),
        }

    def mark_failed(self, request_id: str, reason: str) -> Dict:
        request = self._capture_repository.get(request_id)
        if request is None:
            raise ValueError("Capture request not found")
        failed_request = ScreenshotCaptureRequest(
            account_id=request.account_id,
            trade_id=request.trade_id,
            broker_id=request.broker_id,
            market_type=request.market_type,
            symbol=request.symbol,
            status="failed",
            trigger=request.trigger,
            requested_by=request.requested_by,
            source_hint=request.source_hint,
            claimed_by=request.claimed_by,
            requested_at=request.requested_at,
            claimed_at=request.claimed_at,
            completed_at=datetime.now(timezone.utc),
            failure_reason=reason,
            metadata=request.metadata,
            request_id=request.request_id,
        )
        self._capture_repository.save(failed_request)
        return failed_request.to_dict()

    def list_pending(self) -> List[Dict]:
        return [request.to_dict() for request in self._capture_repository.get_by_status("pending")]

    def claim_request(self, request_id: str, source_id: str) -> Dict:
        request = self._capture_repository.get(request_id)
        if request is None:
            raise ValueError("Capture request not found")
        if request.status not in {"pending", "claimed"}:
            raise ValueError("Capture request is not claimable")
        if request.claimed_by and request.claimed_by != source_id:
            raise ValueError("Capture request already claimed by another source")

        claimed_request = ScreenshotCaptureRequest(
            account_id=request.account_id,
            trade_id=request.trade_id,
            broker_id=request.broker_id,
            market_type=request.market_type,
            symbol=request.symbol,
            status="claimed",
            trigger=request.trigger,
            requested_by=request.requested_by,
            source_hint=request.source_hint,
            claimed_by=source_id,
            requested_at=request.requested_at,
            claimed_at=datetime.now(timezone.utc),
            completed_at=None,
            failure_reason=None,
            metadata=request.metadata,
            request_id=request.request_id,
        )
        self._capture_repository.save(claimed_request)
        return claimed_request.to_dict()

    def _build_default_markers(self, trade_data: Dict) -> List[AttachmentMarker]:
        markers = []
        if trade_data.get("entry_price") is not None:
            markers.append(AttachmentMarker(label="entry", price=trade_data["entry_price"], color="blue"))
        if trade_data.get("stop_loss_at_entry") is not None:
            markers.append(AttachmentMarker(label="stop_loss", price=trade_data["stop_loss_at_entry"], color="red"))
        if trade_data.get("target_at_entry") is not None:
            markers.append(AttachmentMarker(label="target", price=trade_data["target_at_entry"], color="green"))
        if trade_data.get("exit_price") is not None:
            markers.append(AttachmentMarker(label="close", price=trade_data["exit_price"], color="amber"))
        return markers
