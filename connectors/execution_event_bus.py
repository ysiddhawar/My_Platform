from __future__ import annotations

from typing import Callable, Dict, List, Any
from threading import RLock, Thread
import queue
import traceback


class ExecutionEventBusError(Exception):
    pass


class ExecutionEventBus:
    """
    Institutional Event-Driven Backbone

    Responsibilities:
    - Thread-safe event emission
    - Subscriber isolation
    - Async dispatch
    - Wildcard support
    - Failure containment
    - Platform-wide compatibility
    """

    def __init__(self):

        self._lock = RLock()

        # event_type -> [subscribers]
        self._subscribers: Dict[str, List[Callable[[Any], None]]] = {}

        # global subscribers (wildcard)
        self._global_subscribers: List[Callable[[Any], None]] = []

        # async dispatch queue
        self._event_queue: queue.Queue = queue.Queue()

        self._running = True
        self._start_dispatch_loop()

    # ==========================================================
    # SUBSCRIPTION MANAGEMENT
    # ==========================================================

    def subscribe(
        self,
        event_type: str,
        handler: Callable[[Any], None],
    ):

        if not callable(handler):
            raise ExecutionEventBusError("Handler must be callable")

        with self._lock:
            self._subscribers.setdefault(event_type, []).append(handler)

    def subscribe_all(
        self,
        handler: Callable[[Any], None],
    ):
        if not callable(handler):
            raise ExecutionEventBusError("Handler must be callable")

        with self._lock:
            self._global_subscribers.append(handler)

    def unsubscribe(
        self,
        event_type: str,
        handler: Callable[[Any], None],
    ):
        with self._lock:
            handlers = self._subscribers.get(event_type, [])
            if handler in handlers:
                handlers.remove(handler)

    # ==========================================================
    # EVENT EMISSION
    # ==========================================================

    def emit(self, event: Any):

        if event is None:
            raise ExecutionEventBusError("Cannot emit None event")

        self._event_queue.put(event)

    # ==========================================================
    # ASYNC DISPATCH LOOP
    # ==========================================================

    def _start_dispatch_loop(self):

        def dispatch():

            while self._running:

                event = self._event_queue.get()

                try:
                    self._dispatch_event(event)
                except Exception:
                    # Hard containment
                    traceback.print_exc()

                finally:
                    self._event_queue.task_done()

        Thread(target=dispatch, daemon=True).start()

    def _dispatch_event(self, event: Any):

        event_type = getattr(event, "event_type", None)

        with self._lock:
            specific_handlers = list(
                self._subscribers.get(event_type, [])
            )
            global_handlers = list(self._global_subscribers)

        # Dispatch specific handlers
        for handler in specific_handlers:
            self._safe_execute(handler, event)

        # Dispatch wildcard handlers
        for handler in global_handlers:
            self._safe_execute(handler, event)

    # ==========================================================
    # SAFE EXECUTION WRAPPER
    # ==========================================================

    def _safe_execute(
        self,
        handler: Callable[[Any], None],
        event: Any,
    ):
        try:
            handler(event)
        except Exception:
            # Subscriber failure must never break system
            traceback.print_exc()

    # ==========================================================
    # SHUTDOWN
    # ==========================================================

    def shutdown(self):

        self._running = False