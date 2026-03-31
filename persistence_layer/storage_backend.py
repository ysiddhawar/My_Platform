from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from threading import RLock


class StorageBackendError(Exception):
    pass


class StorageBackend(ABC):
    """
    Institutional Storage Backend Interface

    Contract Requirements:
    - Append-only semantics
    - Atomic append operation
    - Thread-safe behavior
    - Ordered retrieval
    - No mutation of existing records
    - Deterministic read consistency

    All concrete backends MUST:
    - Guarantee record durability (within backend constraints)
    - Preserve insertion order
    - Avoid partial writes
    """

    def __init__(self):
        self._lock = RLock()

    # ==========================================================
    # CORE REQUIRED METHODS
    # ==========================================================

    @abstractmethod
    def append(self, record: Dict[str, Any]) -> None:
        """
        Persist a single record atomically.

        Must:
        - Never modify existing records
        - Never reorder records
        - Raise exception on failure
        """
        raise NotImplementedError

    @abstractmethod
    def read_all(self) -> List[Dict[str, Any]]:
        """
        Return all records in insertion order.

        Must:
        - Preserve ordering
        - Return deep-safe copies if necessary
        """
        raise NotImplementedError

    # ==========================================================
    # OPTIONAL EXTENSION METHODS
    # ==========================================================

    def read_filtered(
        self,
        *,
        event_type: Optional[str] = None,
        account_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Optional optimized filtering.
        Default implementation uses read_all().
        Backends may override for performance.
        """

        records = self.read_all()

        if event_type:
            records = [
                r for r in records
                if r.get("event_type") == event_type
            ]

        if account_id:
            records = [
                r for r in records
                if r.get("account_id") == account_id
            ]

        return records

    # ==========================================================
    # MAINTENANCE
    # ==========================================================

    def clear(self) -> None:
        """
        Optional destructive operation.
        Not required for production backends.
        Mainly for testing.
        """
        raise StorageBackendError(
            "Clear operation not supported by this backend."
        )