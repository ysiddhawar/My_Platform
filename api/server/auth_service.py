from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from models.auth_user import AuthUser
from models.user_session import UserSession
from persistence_layer.session_repository import SessionRepository
from persistence_layer.user_repository import UserRepository


class AuthServiceError(Exception):
    pass


class AuthService:
    SESSION_DURATION_HOURS = 24

    def __init__(self, user_repository: UserRepository, session_repository: SessionRepository):
        self._user_repository = user_repository
        self._session_repository = session_repository

    def bootstrap_admin(
        self,
        username: str,
        password: str,
        account_ids: Optional[List[str]] = None,
    ) -> Dict:
        if self._user_repository.count() > 0:
            raise AuthServiceError("Bootstrap already completed")
        return self._create_user(
            username=username,
            password=password,
            account_ids=account_ids or ["*"],
            roles=["admin"],
            metadata={"bootstrap_admin": True},
        )

    def create_user(
        self,
        username: str,
        password: str,
        account_ids: Optional[List[str]] = None,
        roles: Optional[List[str]] = None,
        metadata: Optional[Dict] = None,
    ) -> Dict:
        return self._create_user(
            username=username,
            password=password,
            account_ids=account_ids or [],
            roles=roles or ["user"],
            metadata=metadata,
        )

    def _create_user(
        self,
        username: str,
        password: str,
        account_ids: List[str],
        roles: List[str],
        metadata: Optional[Dict] = None,
    ) -> Dict:
        normalized = username.strip().lower()
        if not normalized:
            raise AuthServiceError("username required")
        if len(password or "") < 8:
            raise AuthServiceError("password must be at least 8 characters")
        if self._user_repository.get_by_username(normalized) is not None:
            raise AuthServiceError("username already exists")

        password_salt = secrets.token_hex(16)
        password_hash = self._hash_password(password, password_salt)
        now = datetime.now(timezone.utc)
        user = AuthUser(
            username=normalized,
            password_hash=password_hash,
            password_salt=password_salt,
            account_ids=account_ids,
            roles=roles,
            metadata=metadata or {},
            created_at=now,
            updated_at=now,
        )
        self._user_repository.save(user)
        return {"user": self._public_user(user)}

    def login(self, username: str, password: str) -> Dict:
        user = self._user_repository.get_by_username(username.strip().lower())
        if user is None or not user.is_active:
            raise AuthServiceError("invalid credentials")
        candidate = self._hash_password(password, user.password_salt)
        if not secrets.compare_digest(candidate, user.password_hash):
            raise AuthServiceError("invalid credentials")

        session = UserSession(
            user_id=user.user_id,
            username=user.username,
            session_token=secrets.token_urlsafe(32),
            account_ids=user.account_ids,
            roles=user.roles,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=self.SESSION_DURATION_HOURS),
        )
        self._session_repository.save(session)
        return {
            "token": session.session_token,
            "session": session.to_dict(),
            "user": self._public_user(user),
        }

    def logout(self, session_token: str) -> Dict:
        session = self._session_repository.get_by_token(session_token)
        if session is None:
            raise AuthServiceError("session not found")
        revoked = UserSession(
            user_id=session.user_id,
            username=session.username,
            session_token=session.session_token,
            account_ids=session.account_ids,
            roles=session.roles,
            is_active=False,
            metadata=session.metadata,
            session_id=session.session_id,
            created_at=session.created_at,
            expires_at=session.expires_at,
            revoked_at=datetime.now(timezone.utc),
        )
        self._session_repository.save(revoked)
        return {"status": "logged_out"}

    def authenticate_token(self, session_token: str) -> Dict:
        session = self._session_repository.get_by_token(session_token)
        if session is None:
            raise AuthServiceError("invalid token")
        if not session.is_active or session.revoked_at is not None:
            raise AuthServiceError("session inactive")
        if session.expires_at and datetime.now(timezone.utc) > session.expires_at:
            raise AuthServiceError("session expired")
        user = self._user_repository.get(session.user_id)
        if user is None or not user.is_active:
            raise AuthServiceError("user inactive")
        return {"user": self._public_user(user), "session": session.to_dict()}

    def has_account_access(self, user: Dict, account_id: str) -> bool:
        account_ids = user.get("account_ids", [])
        roles = set(user.get("roles", []))
        if "admin" in roles or "*" in account_ids:
            return True
        return account_id in account_ids

    def is_admin(self, user: Dict) -> bool:
        return "admin" in set(user.get("roles", []))

    def _public_user(self, user: AuthUser) -> Dict:
        payload = user.to_dict()
        payload.pop("password_hash", None)
        payload.pop("password_salt", None)
        return payload

    def _hash_password(self, password: str, salt: str) -> str:
        return hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            120000,
        ).hex()
