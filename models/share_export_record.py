from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class ShareExportRecord:
    account_id: str
    record_type: str
    target_type: str
    target_id: str
    format: str
    status: str
    storage_path: Optional[str] = None
    share_token: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "account_id": self.account_id,
            "record_type": self.record_type,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "format": self.format,
            "status": self.status,
            "storage_path": self.storage_path,
            "share_token": self.share_token,
            "metadata": dict(self.metadata),
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "ShareExportRecord":
        return cls(
            account_id=payload["account_id"],
            record_type=payload["record_type"],
            target_type=payload["target_type"],
            target_id=payload["target_id"],
            format=payload["format"],
            status=payload["status"],
            storage_path=payload.get("storage_path"),
            share_token=payload.get("share_token"),
            metadata=payload.get("metadata", {}),
            record_id=payload.get("record_id", str(uuid.uuid4())),
            created_at=datetime.fromisoformat(payload["created_at"]) if payload.get("created_at") else datetime.now(timezone.utc),
        )
