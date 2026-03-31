from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from models.share_export_record import ShareExportRecord
from persistence_layer.attachment_repository import AttachmentRepository
from persistence_layer.export_repository import ExportRepository
from persistence_layer.note_repository import NoteRepository
from persistence_layer.rating_repository import RatingRepository
from persistence_layer.tag_repository import TagRepository
from persistence_layer.trade_repository import TradeRepository


class ShareLinkService:
    def __init__(
        self,
        trade_repository: TradeRepository,
        attachment_repository: AttachmentRepository,
        note_repository: NoteRepository,
        tag_repository: TagRepository,
        rating_repository: RatingRepository,
        export_repository: ExportRepository,
    ):
        self._trade_repository = trade_repository
        self._attachment_repository = attachment_repository
        self._note_repository = note_repository
        self._tag_repository = tag_repository
        self._rating_repository = rating_repository
        self._export_repository = export_repository

    def create_share_link(
        self,
        account_id: str,
        target_type: str,
        target_id: str,
        expires_in_hours: int = 168,
        include_notes: bool = True,
        include_attachments: bool = True,
    ) -> Dict[str, Any]:
        if target_type not in {"trade", "account"}:
            raise ValueError("Unsupported share target type")

        if expires_in_hours <= 0:
            raise ValueError("expires_in_hours must be positive")

        payload = self._build_shared_payload(
            account_id=account_id,
            target_type=target_type,
            target_id=target_id,
            include_notes=include_notes,
            include_attachments=include_attachments,
        )
        expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)
        record = ShareExportRecord(
            account_id=account_id,
            record_type="share_link",
            target_type=target_type,
            target_id=target_id,
            format="share_snapshot",
            status="active",
            share_token=secrets.token_urlsafe(24),
            metadata={
                "expires_at": expires_at.isoformat(),
                "shared_payload": payload,
                "include_notes": include_notes,
                "include_attachments": include_attachments,
                "share_scope": "read_only",
            },
        )
        self._export_repository.save(record)
        return {
            "share_export": self._public_record(record),
            "share_url_path": f"/share-export/shared/{record.share_token}",
        }

    def resolve_share_link(self, share_token: str) -> Dict[str, Any]:
        record = self._export_repository.get_by_share_token(share_token)
        if record is None:
            raise ValueError("Share link not found")

        if record.status == "revoked":
            raise PermissionError("Share link has been revoked")

        expires_at_raw = record.metadata.get("expires_at")
        if expires_at_raw:
            expires_at = datetime.fromisoformat(expires_at_raw)
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) > expires_at:
                expired_record = ShareExportRecord(
                    account_id=record.account_id,
                    record_type=record.record_type,
                    target_type=record.target_type,
                    target_id=record.target_id,
                    format=record.format,
                    status="expired",
                    storage_path=record.storage_path,
                    share_token=record.share_token,
                    metadata={**record.metadata, "expired_at": datetime.now(timezone.utc).isoformat()},
                    record_id=record.record_id,
                    created_at=record.created_at,
                )
                self._export_repository.save(expired_record)
                raise PermissionError("Share link has expired")

        return {
            "share_export": self._public_record(record),
            "shared_payload": record.metadata.get("shared_payload", {}),
        }

    def revoke_share_link(self, record_id: str) -> Dict[str, Any]:
        record = self._export_repository.get(record_id)
        if record is None:
            raise ValueError("Share record not found")

        revoked = ShareExportRecord(
            account_id=record.account_id,
            record_type=record.record_type,
            target_type=record.target_type,
            target_id=record.target_id,
            format=record.format,
            status="revoked",
            storage_path=record.storage_path,
            share_token=record.share_token,
            metadata={**record.metadata, "revoked_at": datetime.now(timezone.utc).isoformat()},
            record_id=record.record_id,
            created_at=record.created_at,
        )
        self._export_repository.save(revoked)
        return {"share_export": self._public_record(revoked)}

    def list_share_links(self, account_id: str, target_type: Optional[str] = None) -> Dict[str, Any]:
        records = self._export_repository.get_by_record_type(account_id, "share_link")
        if target_type:
            records = [record for record in records if record.target_type == target_type]
        return {"share_exports": [self._public_record(record) for record in records]}

    def _build_shared_payload(
        self,
        account_id: str,
        target_type: str,
        target_id: str,
        include_notes: bool,
        include_attachments: bool,
    ) -> Dict[str, Any]:
        if target_type == "trade":
            trade = self._trade_repository.get_trade(target_id)
            if trade is None:
                raise ValueError("Trade not found")
            trade_payload = trade.to_dict()
            if trade_payload.get("account_id") != account_id:
                raise ValueError("Trade does not belong to account")
            rating = self._rating_repository.get_for_trade(target_id)
            return {
                "target_type": "trade",
                "trade": trade_payload,
                "attachments": [
                    attachment.to_dict()
                    for attachment in (self._attachment_repository.get_by_trade(target_id) if include_attachments else [])
                ],
                "notes": [
                    note.to_dict()
                    for note in (self._note_repository.get_by_trade(target_id) if include_notes else [])
                ],
                "tags": [
                    tag.to_dict() for tag in self._tag_repository.list_for_trade(target_id)
                ],
                "rating": rating.to_dict() if rating else None,
            }

        trades = self._trade_repository.get_trades_by_account(account_id)
        return {
            "target_type": "account",
            "account_id": account_id,
            "trades": [trade.to_dict() for trade in trades],
            "attachments": [
                attachment.to_dict()
                for attachment in (self._attachment_repository.get_by_account(account_id) if include_attachments else [])
            ],
            "notes": [
                note.to_dict()
                for note in (self._note_repository.get_by_account(account_id) if include_notes else [])
            ],
            "tags": [tag.to_dict() for tag in self._tag_repository.list_by_account(account_id)],
            "ratings": [
                rating.to_dict() for rating in self._rating_repository.get_by_account(account_id)
            ],
        }

    def _public_record(self, record: ShareExportRecord) -> Dict[str, Any]:
        payload = record.to_dict()
        metadata = dict(payload.get("metadata", {}))
        metadata.pop("shared_payload", None)
        payload["metadata"] = metadata
        return payload
