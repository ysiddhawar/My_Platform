from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List


@dataclass(frozen=True)
class AuthUser:
    username: str
    password_hash: str
    password_salt: str
    account_ids: List[str] = field(default_factory=list)
    roles: List[str] = field(default_factory=lambda: ["user"])
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    user_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "username": self.username,
            "password_hash": self.password_hash,
            "password_salt": self.password_salt,
            "account_ids": list(self.account_ids),
            "roles": list(self.roles),
            "is_active": self.is_active,
            "metadata": dict(self.metadata),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "AuthUser":
        return cls(
            username=payload["username"],
            password_hash=payload["password_hash"],
            password_salt=payload["password_salt"],
            account_ids=payload.get("account_ids", []),
            roles=payload.get("roles", ["user"]),
            is_active=payload.get("is_active", True),
            metadata=payload.get("metadata", {}),
            user_id=payload.get("user_id", str(uuid.uuid4())),
            created_at=datetime.fromisoformat(payload["created_at"]) if payload.get("created_at") else datetime.now(timezone.utc),
            updated_at=datetime.fromisoformat(payload["updated_at"]) if payload.get("updated_at") else datetime.now(timezone.utc),
        )
