from __future__ import annotations

from typing import Any, Dict, List, Optional, Callable
from threading import RLock
from datetime import datetime
import uuid

from models.execution_event import ExecutionEvent
from persistence_layer.storage_backend import StorageBackend


class EventStoreError(Exception):
    pass


class EventStore:
    """
    Institutional Event Sourcing Engine

    Responsibilities:
    - Append-only event log
    - Monotonic sequencing
    - Thread-safe persistence
    - Replay capability
    - Backend-agnostic storage
    - Compatible with ExecutionEventBus
    """

    def __init__(self, backend: StorageBackend):

        if not isinstance(backend, StorageBackend):
            raise EventStoreError("backend must implement StorageBackend")

        self._backend = backend
        self._lock = RLock()

        self._sequence_counter = self._initialize_sequence()

    # ==========================================================
    # SEQUENCE MANAGEMENT
    # ==========================================================

    def _initialize_sequence(self) -> int:
        """
        Initialize sequence counter from backend state.
        Ensures monotonic ordering across restarts.
        """
        events = self._backend.read_all()
        if not events:
            return 0
        return max(event.get("sequence_id", 0) for event in events)

    def _next_sequence(self) -> int:
        self._sequence_counter += 1
        return self._sequence_counter

    # ==========================================================
    # APPEND EVENT
    # ==========================================================

    def append(self, event: ExecutionEvent):

        if not isinstance(event, ExecutionEvent):
            raise EventStoreError("Only ExecutionEvent can be stored")

        with self._lock:

            record = self._serialize_event(event)
            record["sequence_id"] = self._next_sequence()

            self._backend.append(record)

    # ==========================================================
    # READ OPERATIONS
    # ==========================================================

    def read_all(self) -> List[ExecutionEvent]:

        records = self._backend.read_all()
        return [self._deserialize_event(r) for r in records]

    def read_by_type(self, event_type: str) -> List[ExecutionEvent]:

        records = self._backend.read_all()

        filtered = [
            r for r in records
            if r.get("event_type") == event_type
        ]

        return [self._deserialize_event(r) for r in filtered]

    def read_by_account(self, account_id: str) -> List[ExecutionEvent]:

        records = self._backend.read_all()

        filtered = [
            r for r in records
            if r.get("account_id") == account_id
        ]

        return [self._deserialize_event(r) for r in filtered]

    def load_events(self, account_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Recovery-compatible loader that returns plain dict records.
        """
        records = self._backend.read_all()
        if account_id is not None:
            records = [r for r in records if r.get("account_id") == account_id]

        normalized = []
        for r in records:
            normalized.append({
                "event_id": r.get("event_id"),
                "type": r.get("event_type"),
                "payload": r.get("metadata", {}),
                "account_id": r.get("account_id"),
                "sequence": r.get("sequence_id", 0),
                "sequence_id": r.get("sequence_id", 0),
                "timestamp": r.get("timestamp"),
            })
        return normalized

    # ==========================================================
    # REPLAY
    # ==========================================================

    def replay(
        self,
        handler: Callable[[ExecutionEvent], None],
        event_type: Optional[str] = None,
    ):
        """
        Replay stored events to handler.
        Can filter by event_type.
        """

        if not callable(handler):
            raise EventStoreError("handler must be callable")

        events = self.read_all()

        for event in sorted(
            events,
            key=lambda e: e.metadata.get("sequence_id", 0)
        ):
            if event_type and event.event_type != event_type:
                continue
            handler(event)

    # ==========================================================
    # SERIALIZATION
    # ==========================================================

    def _serialize_event(
        self,
        event: ExecutionEvent
    ) -> Dict[str, Any]:

        return {
            "event_id": getattr(event, "event_id", str(uuid.uuid4())),
            "event_type": event.event_type,
            "timestamp": event.timestamp.isoformat()
            if isinstance(event.timestamp, datetime)
            else event.timestamp,
            "metadata": event.metadata,
            "account_id": event.metadata.get("account_id")
            if isinstance(event.metadata, dict)
            else None,
        }

    def _deserialize_event(
        self,
        record: Dict[str, Any]
    ) -> ExecutionEvent:

        return ExecutionEvent(
            event_type=record["event_type"],
            timestamp=datetime.fromisoformat(record["timestamp"]),
            metadata=record.get("metadata"),
        )
