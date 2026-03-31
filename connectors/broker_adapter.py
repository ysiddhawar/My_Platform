from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Any, Callable, Optional
from threading import RLock, Thread
from datetime import datetime, timezone
import uuid
import time


class BrokerAdapterError(Exception):
    pass


# ==========================================================
# NORMALIZED EVENT BUILDER
# ==========================================================

class NormalizedEventBuilder:
    """
    Converts broker-specific payloads into platform-normalized events.
    """

    @staticmethod
    def build_event(
        event_type: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:

        return {
            "event_id": str(uuid.uuid4()),
            "type": event_type,
            "timestamp": datetime.now(timezone.utc),
            "payload": payload,
        }


# ==========================================================
# ABSTRACT BASE ADAPTER
# ==========================================================

class BaseBrokerAdapter(ABC):
    """
    Institutional Broker Adapter Interface

    Responsibilities:
    - Connect / disconnect safely
    - Stream broker events
    - Normalize payload
    - Emit events to platform
    """

    def __init__(self):
        self._lock = RLock()
        self._connected = False
        self._event_callback: Optional[Callable[[Dict[str, Any]], None]] = None
        self._stream_thread: Optional[Thread] = None

    # ------------------------------------------------------
    # CALLBACK REGISTRATION
    # ------------------------------------------------------

    def register_event_callback(
        self,
        callback: Callable[[Dict[str, Any]], None]
    ):
        self._event_callback = callback

    # ------------------------------------------------------
    # CONNECTION LIFECYCLE
    # ------------------------------------------------------

    def connect(self):

        with self._lock:

            if self._connected:
                return

            self._connect_impl()
            self._connected = True

            self._start_stream_loop()

    def disconnect(self):

        with self._lock:

            if not self._connected:
                return

            self._connected = False
            self._disconnect_impl()

    def is_connected(self) -> bool:
        return self._connected

    # ------------------------------------------------------
    # STREAM LOOP
    # ------------------------------------------------------

    def _start_stream_loop(self):

        def stream():

            while self._connected:
                try:
                    raw_event = self._poll_event()

                    if raw_event:
                        normalized = self._normalize_event(raw_event)
                        if self._event_callback:
                            self._event_callback(normalized)

                except Exception:
                    time.sleep(1)  # backoff

        self._stream_thread = Thread(
            target=stream,
            daemon=True
        )
        self._stream_thread.start()

    # ------------------------------------------------------
    # ABSTRACT METHODS (BROKER SPECIFIC)
    # ------------------------------------------------------

    @abstractmethod
    def _connect_impl(self):
        pass

    @abstractmethod
    def _disconnect_impl(self):
        pass

    @abstractmethod
    def _poll_event(self) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def _normalize_event(self, raw_event: Dict[str, Any]) -> Dict[str, Any]:
        pass


# ==========================================================
# ADAPTER REGISTRY
# ==========================================================

class BrokerAdapterRegistry:
    """
    Broker Adapter Factory + Registry
    """

    def __init__(self):
        self._registry: Dict[str, BaseBrokerAdapter] = {}

    def register(self, broker_id: str, adapter: BaseBrokerAdapter):

        if broker_id in self._registry:
            raise BrokerAdapterError("Broker already registered")

        self._registry[broker_id] = adapter

    def get(self, broker_id: str) -> BaseBrokerAdapter:

        if broker_id not in self._registry:
            raise BrokerAdapterError("Broker not registered")

        return self._registry[broker_id]

    def list_brokers(self):
        return list(self._registry.keys())

    def unregister(self, broker_id: str) -> None:
        self._registry.pop(broker_id, None)
