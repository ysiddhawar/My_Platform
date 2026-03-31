from __future__ import annotations

from typing import Dict, List, Any
from threading import RLock
import copy

from persistence_layer.storage_backend import StorageBackend, StorageBackendError


class MemoryBackend(StorageBackend):
    """
    In-Memory Storage Backend (Development / Testing)

    Guarantees:
    - Append-only semantics
    - Ordered retrieval
    - Thread-safe writes
    - Defensive copy on read
    - Deterministic behavior
    """

    def __init__(self):
        super().__init__()
        self._records: List[Dict[str, Any]] = []

    # ==========================================================
    # APPEND (ATOMIC)
    # ==========================================================

    def append(self, record: Dict[str, Any]) -> None:

        if not isinstance(record, dict):
            raise StorageBackendError("Record must be dict")

        with self._lock:

            # Defensive copy to prevent external mutation
            record_copy = copy.deepcopy(record)

            # Enforce append-only
            self._records.append(record_copy)

    # ==========================================================
    # READ ALL (ORDERED)
    # ==========================================================

    def read_all(self) -> List[Dict[str, Any]]:

        with self._lock:

            # Return deep copy to prevent mutation
            return copy.deepcopy(self._records)

    # ==========================================================
    # CLEAR (TEST ONLY)
    # ==========================================================

    def clear(self) -> None:

        with self._lock:
            self._records.clear()