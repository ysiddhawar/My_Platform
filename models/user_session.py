from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class UserSession:
    user_id: str
    username: str
    session_token: str
    account_ids: List[str] = field(default_factory=list)
    roles: List[str] = field(default_factory=list)
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "username": self.username,
            "session_token": self.session_token,
            "account_ids": list(self.account_ids),
            "roles": list(self.roles),
            "is_active": self.is_active,
            "metadata": dict(self.metadata),
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "UserSession":
        return cls(
            user_id=payload["user_id"],
            username=payload["username"],
            session_token=payload["session_token"],
            account_ids=payload.get("account_ids", []),
            roles=payload.get("roles", []),
            is_active=payload.get("is_active", True),
            metadata=payload.get("metadata", {}),
            session_id=payload.get("session_id", str(uuid.uuid4())),
            created_at=datetime.fromisoformat(payload["created_at"]) if payload.get("created_at") else datetime.now(timezone.utc),
            expires_at=datetime.fromisoformat(payload["expires_at"]) if payload.get("expires_at") else None,
            revoked_at=datetime.fromisoformat(payload["revoked_at"]) if payload.get("revoked_at") else None,
        )
