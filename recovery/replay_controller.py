from __future__ import annotations

from typing import List, Dict, Any, Optional
from threading import RLock

from core.context import ExecutionContext
from core.evaluator import Evaluator
from core.dependency_graph import DependencyGraph


class ReplayControllerError(Exception):
    pass


class ReplayController:
    """
    Institutional Replay Controller

    Responsibilities:
    - Deterministic state rebuild
    - Snapshot + event replay
    - Governance-safe execution
    - Partial replay support
    - Account-filtered replay
    """

    def __init__(
        self,
        evaluator: Evaluator,
        dependency_graph: DependencyGraph,
    ):
        self._evaluator = evaluator
        self._graph = dependency_graph
        self._lock = RLock()

    # ==========================================================
    # PUBLIC ENTRY
    # ==========================================================

    def replay(
        self,
        snapshot: Optional[Dict[str, Any]],
        events: List[Dict[str, Any]],
        phase: str = "recovery",
        entity: Optional[Any] = None,
        account_filter: Optional[str] = None,
    ) -> ExecutionContext:

        with self._lock:

            # --------------------------------------------------
            # 1️⃣ Initialize Context
            # --------------------------------------------------

            base_data = {}

            if snapshot:
                base_data = snapshot.get("state", {})

            context = ExecutionContext(
                data=base_data,
                phase=phase,
                entity=entity,
            )

            # --------------------------------------------------
            # 2️⃣ Sort Events Deterministically
            # --------------------------------------------------

            sorted_events = sorted(
                events,
                key=lambda e: e.get("sequence", 0)
            )

            # --------------------------------------------------
            # 3️⃣ Replay Events
            # --------------------------------------------------

            for event in sorted_events:

                if account_filter:
                    if event.get("account_id") != account_filter:
                        continue

                self._apply_event(context, event)

            # --------------------------------------------------
            # 4️⃣ Finalize Context
            # --------------------------------------------------

            context.finalize()

            return context

    # ==========================================================
    # INTERNAL EVENT APPLICATION
    # ==========================================================

    def _apply_event(
        self,
        context: ExecutionContext,
        event: Dict[str, Any],
    ):

        event_type = event.get("type")
        payload = event.get("payload", {})

        if not event_type:
            raise ReplayControllerError("Event missing type")

        # ------------------------------------------------------
        # Dispatch via dependency graph
        # ------------------------------------------------------

        try:
            nodes = self._graph.get_nodes_for_event(event_type)

            for node in nodes:
                self._evaluator.evaluate_node(node, context, payload)

        except Exception as e:
            raise ReplayControllerError(
                f"Replay failed on event {event_type}: {str(e)}"
            )