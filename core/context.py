from __future__ import annotations

import time
import uuid
import copy
from typing import Any, Dict, Optional, Callable


class ContextVersionError(Exception):
    pass


class ContextMigrationError(Exception):
    pass


class ExecutionContext:
    """
    Institutional Execution Context

    Enhancements:
    - Deterministic serialization
    - Snapshot-safe restore
    - Schema versioning
    - Migration support
    - Crash recovery compatibility
    - Governance-ready
    """

    __slots__ = (
        "_data",
        "_results",
        "_cache",
        "_errors",
        "_metadata",
        "phase",
        "flags",
        "entity",
        "_version",
    )

    # Increment when structure changes
    SCHEMA_VERSION = 1

    # Optional migration registry
    _MIGRATIONS: Dict[int, Callable[[Dict[str, Any]], Dict[str, Any]]] = {}

    def __init__(
        self,
        data: Optional[Dict[str, Any]] = None,
        phase: str = "research",
        entity: Optional[Any] = None,
    ):

        self._data = data or {}
        self._results: Dict[str, Any] = {}
        self._cache: Dict[str, Any] = {}
        self._errors: Dict[str, str] = {}

        self.phase = phase
        self.flags: Dict[str, Any] = {}
        self.entity = entity

        self._metadata = {
            "run_id": str(uuid.uuid4()),
            "start_time": time.perf_counter(),
            "execution_time": None,
            "metric_count": 0,
        }

        self._version = self.SCHEMA_VERSION

    # ==========================================================
    # DATA ACCESS
    # ==========================================================

    @property
    def data(self) -> Dict[str, Any]:
        return self._data

    # ==========================================================
    # RESULT HANDLING
    # ==========================================================

    def set_result(self, name: str, value: Any):
        self._results[name] = value
        self._metadata["metric_count"] += 1

    def get_result(self, name: str):
        return self._results.get(name)

    def all_results(self):
        return copy.deepcopy(self._results)

    # ==========================================================
    # CACHE
    # ==========================================================

    def set_cache(self, key: str, value: Any):
        self._cache[key] = value

    def get_cache(self, key: str):
        return self._cache.get(key)

    # ==========================================================
    # FLAGS
    # ==========================================================

    def set_flag(self, key: str, value: Any):
        self.flags[key] = value

    def get_flag(self, key: str):
        return self.flags.get(key)

    # ==========================================================
    # ERROR HANDLING
    # ==========================================================

    def set_error(self, name: str, error: Exception):
        self._errors[name] = str(error)

    def get_errors(self):
        return copy.deepcopy(self._errors)

    # ==========================================================
    # FINALIZATION
    # ==========================================================

    def finalize(self):
        self._metadata["execution_time"] = (
            time.perf_counter() - self._metadata["start_time"]
        )

    def metadata(self):
        return copy.deepcopy(self._metadata)

    # ==========================================================
    # SNAPSHOT SERIALIZATION
    # ==========================================================

    def to_dict(self) -> Dict[str, Any]:
        """
        Deterministic snapshot serialization.
        Must only contain JSON-serializable structures.
        """

        return {
            "schema_version": self._version,
            "data": copy.deepcopy(self._data),
            "results": copy.deepcopy(self._results),
            "cache": copy.deepcopy(self._cache),
            "errors": copy.deepcopy(self._errors),
            "flags": copy.deepcopy(self.flags),
            "phase": self.phase,
            "metadata": copy.deepcopy(self._metadata),
        }

    # ==========================================================
    # SNAPSHOT RESTORE
    # ==========================================================

    def load_from_dict(self, state: Dict[str, Any]):

        if not isinstance(state, dict):
            raise ContextVersionError("Invalid snapshot format")

        snapshot_version = state.get("schema_version")

        if snapshot_version is None:
            raise ContextVersionError("Snapshot missing schema_version")

        if snapshot_version > self.SCHEMA_VERSION:
            raise ContextVersionError(
                "Snapshot version newer than current context"
            )

        # Apply migrations if necessary
        state = self._apply_migrations(state, snapshot_version)

        # Safe state replacement
        self._data = copy.deepcopy(state.get("data", {}))
        self._results = copy.deepcopy(state.get("results", {}))
        self._cache = copy.deepcopy(state.get("cache", {}))
        self._errors = copy.deepcopy(state.get("errors", {}))
        self.flags = copy.deepcopy(state.get("flags", {}))
        self.phase = state.get("phase", "research")
        self._metadata = copy.deepcopy(state.get("metadata", {}))
        self._version = self.SCHEMA_VERSION

    # ==========================================================
    # MIGRATION SYSTEM
    # ==========================================================

    @classmethod
    def register_migration(
        cls,
        from_version: int,
        migration_fn: Callable[[Dict[str, Any]], Dict[str, Any]],
    ):
        cls._MIGRATIONS[from_version] = migration_fn

    def _apply_migrations(
        self,
        state: Dict[str, Any],
        snapshot_version: int,
    ) -> Dict[str, Any]:

        current_version = snapshot_version

        while current_version < self.SCHEMA_VERSION:

            migration_fn = self._MIGRATIONS.get(current_version)

            if not migration_fn:
                raise ContextMigrationError(
                    f"No migration path from version {current_version}"
                )

            state = migration_fn(state)
            current_version += 1

        return state


# Backward-compatible alias for modules that still import `Context`.
Context = ExecutionContext
