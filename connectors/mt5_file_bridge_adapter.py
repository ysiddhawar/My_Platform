from __future__ import annotations

import json
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from connectors.broker_adapter import BaseBrokerAdapter, NormalizedEventBuilder


class MT5FileBridgeAdapter(BaseBrokerAdapter):
    """
    Polls a filesystem inbox written by an external MT5 EA/desktop bridge.

    Expected raw event shape:
    {
      "event_type": "PRE_TRADE_REQUEST" | "TRADE_FILLED" | "TRADE_CLOSED",
      "payload": {...}
    }

    Alternate legacy fields accepted:
    - "type"
    - flat payload without nested "payload"
    """

    def __init__(
        self,
        broker_id: str,
        inbox_dir: str,
        archive_dir: Optional[str] = None,
        outbox_dir: Optional[str] = None,
        poll_interval_seconds: float = 0.25,
    ):
        super().__init__()
        self._broker_id = broker_id
        self._inbox_dir = Path(inbox_dir)
        self._archive_dir = Path(archive_dir) if archive_dir else self._inbox_dir / "processed"
        self._outbox_dir = Path(outbox_dir) if outbox_dir else self._inbox_dir.parent / "outbox"
        self._poll_interval_seconds = max(float(poll_interval_seconds), 0.05)
        self._last_event_at: Optional[str] = None
        self._last_event_type: Optional[str] = None
        self._last_event_file: Optional[str] = None
        self._last_command_at: Optional[str] = None
        self._last_command_file: Optional[str] = None

    def _connect_impl(self):
        self._inbox_dir.mkdir(parents=True, exist_ok=True)
        self._archive_dir.mkdir(parents=True, exist_ok=True)
        self._outbox_dir.mkdir(parents=True, exist_ok=True)

    def _disconnect_impl(self):
        return None

    def _poll_event(self) -> Optional[Dict[str, Any]]:
        for path in sorted(self._inbox_dir.glob("*.json")):
            if not path.is_file():
                continue
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                archived_path = self._archive_dir / path.name
                shutil.move(str(path), str(archived_path))
                self._last_event_at = datetime.now(timezone.utc).isoformat()
                self._last_event_type = str(payload.get("event_type") or payload.get("type") or "unknown")
                self._last_event_file = path.name
                return payload
            except Exception:
                failed_path = self._archive_dir / f"failed_{int(time.time() * 1000)}_{path.name}"
                try:
                    shutil.move(str(path), str(failed_path))
                except Exception:
                    pass
        time.sleep(self._poll_interval_seconds)
        return None

    def _normalize_event(self, raw_event: Dict[str, Any]) -> Dict[str, Any]:
        event_type = raw_event.get("event_type") or raw_event.get("type")
        if not event_type:
            raise ValueError("MT5 bridge event missing event_type")

        payload = raw_event.get("payload")
        if payload is None:
            payload = {k: v for k, v in raw_event.items() if k not in {"event_type", "type"}}
        if not isinstance(payload, dict):
            raise ValueError("MT5 bridge payload must be dict")

        payload = dict(payload)
        payload.setdefault("broker_id", self._broker_id)
        return NormalizedEventBuilder.build_event(event_type=event_type, payload=payload)

    def supports_order_ticket_submission(self) -> bool:
        return True

    def submit_order_ticket(self, ticket: Dict[str, Any]) -> Dict[str, Any]:
        self._outbox_dir.mkdir(parents=True, exist_ok=True)
        client_ticket_id = str(ticket.get("client_ticket_id") or ticket.get("prepared_ticket_id") or f"ticket_{int(time.time() * 1000)}")
        filename = f"order_ticket_{client_ticket_id}.json"
        temp_path = self._outbox_dir / f".{filename}.tmp"
        final_path = self._outbox_dir / filename
        command = {
            "command_type": "OPEN_ORDER_TICKET",
            "bridge_contract_version": "2026-04-17",
            "submitted_at": datetime.now(timezone.utc).isoformat(),
            "payload": ticket,
        }
        temp_path.write_text(json.dumps(command, ensure_ascii=True, indent=2), encoding="utf-8")
        temp_path.replace(final_path)
        self._last_command_at = datetime.now(timezone.utc).isoformat()
        self._last_command_file = final_path.name
        return {
            "provider": self._broker_id,
            "status": "submitted_to_broker_bridge",
            "supported": True,
            "message": "MT5 bridge ticket written. The MT5 EA should open or prefill the broker order window using this request.",
            "outbox_dir": str(self._outbox_dir),
            "command_file": str(final_path),
            "client_ticket_id": client_ticket_id,
        }

    def get_health_snapshot(self) -> Dict[str, Any]:
        inbox_files = sorted(self._inbox_dir.glob("*.json")) if self._inbox_dir.exists() else []
        outbox_files = sorted(self._outbox_dir.glob("*.json")) if self._outbox_dir.exists() else []
        archive_files = sorted(self._archive_dir.glob("*.json")) if self._archive_dir.exists() else []
        newest_inbox = max((path.stat().st_mtime for path in inbox_files), default=None)
        newest_outbox = max((path.stat().st_mtime for path in outbox_files), default=None)
        newest_archive = max((path.stat().st_mtime for path in archive_files), default=None)
        return {
            "connected": self.is_connected(),
            "status": "connected" if self.is_connected() else "disconnected",
            "inbox_pending_count": len(inbox_files),
            "outbox_pending_count": len(outbox_files),
            "archive_file_count": len(archive_files),
            "last_event_at": self._last_event_at,
            "last_event_type": self._last_event_type,
            "last_event_file": self._last_event_file,
            "last_command_at": self._last_command_at,
            "last_command_file": self._last_command_file,
            "latest_inbox_mtime": datetime.fromtimestamp(newest_inbox, timezone.utc).isoformat() if newest_inbox else None,
            "latest_outbox_mtime": datetime.fromtimestamp(newest_outbox, timezone.utc).isoformat() if newest_outbox else None,
            "latest_archive_mtime": datetime.fromtimestamp(newest_archive, timezone.utc).isoformat() if newest_archive else None,
            "bridge_alive": self.is_connected(),
        }

    @property
    def inbox_dir(self) -> str:
        return str(self._inbox_dir)

    @property
    def archive_dir(self) -> str:
        return str(self._archive_dir)

    @property
    def outbox_dir(self) -> str:
        return str(self._outbox_dir)
