from __future__ import annotations

import base64
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from models.screenshot_capture_request import ScreenshotCaptureRequest
from models.screenshot_capture_source import ScreenshotCaptureSource
from persistence_layer.screenshot_capture_repository import ScreenshotCaptureRepository
from persistence_layer.screenshot_capture_service import ScreenshotCaptureService
from persistence_layer.screenshot_capture_source_repository import ScreenshotCaptureSourceRepository


class ScreenshotSourceIntegrationService:
    def __init__(
        self,
        source_repository: ScreenshotCaptureSourceRepository,
        capture_repository: ScreenshotCaptureRepository,
        capture_service: ScreenshotCaptureService,
    ):
        self._source_repository = source_repository
        self._capture_repository = capture_repository
        self._capture_service = capture_service

    def register_source(
        self,
        source_name: str,
        source_type: str,
        account_ids: Optional[List[str]] = None,
        broker_ids: Optional[List[str]] = None,
        market_types: Optional[List[str]] = None,
        capabilities: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        source = ScreenshotCaptureSource(
            source_name=source_name,
            source_type=source_type,
            account_ids=account_ids or [],
            broker_ids=broker_ids or [],
            market_types=market_types or [],
            capabilities=capabilities or {},
        )
        self._source_repository.save(source)
        return {"source": source.to_dict()}

    def heartbeat(self, source_id: str, status: str = "active") -> Dict[str, Any]:
        source = self._source_repository.get(source_id)
        if source is None:
            raise ValueError("Capture source not found")
        updated = ScreenshotCaptureSource(
            source_name=source.source_name,
            source_type=source.source_type,
            status=status,
            account_ids=source.account_ids,
            broker_ids=source.broker_ids,
            market_types=source.market_types,
            capabilities=source.capabilities,
            source_id=source.source_id,
            created_at=source.created_at,
            last_seen_at=datetime.now(timezone.utc),
        )
        self._source_repository.save(updated)
        return {"source": updated.to_dict()}

    def list_sources(self, status: Optional[str] = None) -> Dict[str, Any]:
        return {"sources": [source.to_dict() for source in self._source_repository.list_all(status=status)]}

    def claim_next(self, source_id: str) -> Dict[str, Any]:
        source = self._source_repository.get(source_id)
        if source is None:
            raise ValueError("Capture source not found")
        if source.status != "active":
            raise ValueError("Capture source is not active")

        pending = self._capture_repository.get_by_status("pending")
        for request in pending:
            if self._source_matches_request(source, request):
                claimed = self._capture_service.claim_request(request.request_id, source_id)
                return {"capture_request": claimed}
        return {"capture_request": None}

    def submit_capture(
        self,
        source_id: str,
        request_id: str,
        file_name: str,
        storage_path: str,
        content_type: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        source = self._source_repository.get(source_id)
        if source is None:
            raise ValueError("Capture source not found")
        request = self._capture_repository.get(request_id)
        if request is None:
            raise ValueError("Capture request not found")
        if request.claimed_by and request.claimed_by != source_id:
            raise ValueError("Capture request is claimed by another source")

        enriched_metadata = {
            "submitted_by_source_id": source_id,
            "submitted_by_source_type": source.source_type,
            **(metadata or {}),
        }
        return self._capture_service.ingest_capture(
            request_id=request_id,
            file_name=file_name,
            storage_path=storage_path,
            source=source.source_type,
            content_type=content_type,
            description=description,
            metadata=enriched_metadata,
        )

    def submit_capture_bytes(
        self,
        source_id: str,
        request_id: str,
        file_name: str,
        content_base64: str,
        storage_dir: str = "capture_uploads",
        content_type: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        file_bytes = base64.b64decode(content_base64.encode("utf-8"), validate=True)
        output_dir = Path(storage_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        storage_path = output_dir / f"{request_id}_{file_name}"
        storage_path.write_bytes(file_bytes)
        return self.submit_capture(
            source_id=source_id,
            request_id=request_id,
            file_name=file_name,
            storage_path=str(storage_path),
            content_type=content_type,
            description=description,
            metadata={
                "uploaded_via": "base64",
                **(metadata or {}),
            },
        )

    def fail_capture(self, source_id: str, request_id: str, reason: str) -> Dict[str, Any]:
        source = self._source_repository.get(source_id)
        if source is None:
            raise ValueError("Capture source not found")
        request = self._capture_repository.get(request_id)
        if request is None:
            raise ValueError("Capture request not found")
        if request.claimed_by and request.claimed_by != source_id:
            raise ValueError("Capture request is claimed by another source")
        return {"capture_request": self._capture_service.mark_failed(request_id=request_id, reason=reason)}

    def _source_matches_request(
        self,
        source: ScreenshotCaptureSource,
        request: ScreenshotCaptureRequest,
    ) -> bool:
        if request.source_hint and request.source_hint != source.source_type:
            return False
        if source.account_ids and request.account_id not in source.account_ids:
            return False
        if source.broker_ids and request.broker_id not in source.broker_ids:
            return False
        if source.market_types and request.market_type not in source.market_types:
            return False
        return True
