from __future__ import annotations

import json
import shutil
import time
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
        poll_interval_seconds: float = 0.25,
    ):
        super().__init__()
        self._broker_id = broker_id
        self._inbox_dir = Path(inbox_dir)
        self._archive_dir = Path(archive_dir) if archive_dir else self._inbox_dir / "processed"
        self._poll_interval_seconds = max(float(poll_interval_seconds), 0.05)

    def _connect_impl(self):
        self._inbox_dir.mkdir(parents=True, exist_ok=True)
        self._archive_dir.mkdir(parents=True, exist_ok=True)

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
