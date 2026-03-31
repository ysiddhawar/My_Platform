from __future__ import annotations

import queue
from typing import Any, Dict, Optional

from connectors.broker_adapter import BaseBrokerAdapter, NormalizedEventBuilder


class SimulatedBrokerAdapter(BaseBrokerAdapter):
    def __init__(self, broker_id: str):
        super().__init__()
        self._broker_id = broker_id
        self._queue: "queue.Queue[Dict[str, Any]]" = queue.Queue()

    def push_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        payload = dict(payload)
        payload.setdefault("broker_id", self._broker_id)
        self._queue.put({"event_type": event_type, "payload": payload})

    def _connect_impl(self):
        return None

    def _disconnect_impl(self):
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break

    def _poll_event(self) -> Optional[Dict[str, Any]]:
        try:
            return self._queue.get(timeout=0.1)
        except queue.Empty:
            return None

    def _normalize_event(self, raw_event: Dict[str, Any]) -> Dict[str, Any]:
        event_type = raw_event.get("event_type") or raw_event.get("type")
        if not event_type:
            raise ValueError("Simulated broker event missing event_type")
        payload = raw_event.get("payload", {})
        if not isinstance(payload, dict):
            raise ValueError("Simulated broker payload must be dict")
        return NormalizedEventBuilder.build_event(event_type=event_type, payload=payload)
