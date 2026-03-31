from __future__ import annotations

from typing import Optional, Dict, Any
from threading import RLock

from persistence_layer.event_store import EventStore
from persistence_layer.snapshot_store import SnapshotStore
from persistence_layer.config_repository import ConfigRepository

from recovery.integrity_checker import IntegrityChecker
from recovery.replay_controller import ReplayController
from recovery.recovery_policy import RecoveryPolicy, RecoveryDecision


class RecoveryEngineError(Exception):
    pass


class RecoveryEngine:
    """
    Institutional Recovery Engine

    Responsibilities:
    - Load snapshot
    - Load event stream
    - Validate integrity
    - Apply recovery policy
    - Rebuild execution context
    - Rehydrate active config
    - Resume execution safely
    """

    def __init__(
        self,
        event_store: EventStore,
        snapshot_store: SnapshotStore,
        config_repository: ConfigRepository,
        replay_controller: ReplayController,
        integrity_checker: IntegrityChecker,
        recovery_policy: RecoveryPolicy,
        execution_orchestrator,
    ):
        self._event_store = event_store
        self._snapshot_store = snapshot_store
        self._config_repository = config_repository
        self._replay_controller = replay_controller
        self._integrity_checker = integrity_checker
        self._recovery_policy = recovery_policy
        self._execution_orchestrator = execution_orchestrator

        self._lock = RLock()

    # ==========================================================
    # PUBLIC ENTRY
    # ==========================================================

    def recover(
        self,
        account_id: Optional[str] = None,
    ) -> Dict[str, Any]:

        with self._lock:

            # --------------------------------------------------
            # 1️⃣ Load Snapshot
            # --------------------------------------------------

            snapshot = self._snapshot_store.load_latest_snapshot(account_id)

            # --------------------------------------------------
            # 2️⃣ Load Events
            # --------------------------------------------------

            events = self._event_store.load_events(account_id)

            # --------------------------------------------------
            # 3️⃣ Load Active Config
            # --------------------------------------------------

            active_config = None
            if account_id:
                active_config = self._config_repository.get_active_config(account_id)

            # --------------------------------------------------
            # 4️⃣ Integrity Check
            # --------------------------------------------------

            integrity_report = self._integrity_checker.validate(
                events=events,
                snapshot=snapshot,
                active_config=active_config,
                account_state=snapshot.get("state") if snapshot else None,
            )

            # --------------------------------------------------
            # 5️⃣ Apply Recovery Policy
            # --------------------------------------------------

            decision: RecoveryDecision = self._recovery_policy.evaluate(
                integrity_report=integrity_report,
                snapshot_available=bool(snapshot),
                active_config=active_config,
            )

            # --------------------------------------------------
            # 6️⃣ Replay State
            # --------------------------------------------------

            context = None

            if decision.allow_replay:

                if decision.require_full_replay:
                    snapshot = None  # force full rebuild

                context = self._replay_controller.replay(
                    snapshot=snapshot,
                    events=events,
                    phase="recovery",
                    entity=None,
                    account_filter=account_id,
                )

            # --------------------------------------------------
            # 7️⃣ Rehydrate Config
            # --------------------------------------------------

            if decision.allow_execution and active_config:
                self._execution_orchestrator.update_config(active_config)

            # --------------------------------------------------
            # 8️⃣ Resume Execution
            # --------------------------------------------------

            if decision.allow_execution:
                self._execution_orchestrator.resume()
            else:
                self._execution_orchestrator.enter_safe_mode()

            # --------------------------------------------------
            # 9️⃣ Return Recovery Summary
            # --------------------------------------------------

            return {
                "integrity_valid": integrity_report.is_valid,
                "integrity_errors": integrity_report.errors,
                "integrity_warnings": integrity_report.warnings,
                "recovery_mode": self._recovery_policy.mode,
                "execution_allowed": decision.allow_execution,
                "read_only_mode": decision.read_only_mode,
                "reason": decision.reason,
                "context_metadata": context.metadata() if context else None,
            }