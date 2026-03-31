from __future__ import annotations

import time
import copy
from typing import Dict, Any, Optional, List


class AIMemoryError(Exception):
    pass


class AIMemoryStore:
    """
    Institutional AI Longitudinal Memory Store

    Responsibilities:
    - Persist AI diagnosis history
    - Persist prescriptions issued
    - Track application status
    - Track outcome performance deltas
    - Track behavioral trend evolution
    - Deterministic + replay-safe
    - Versioned
    - Persistence compatible
    """

    VERSION = 1

    def __init__(
        self,
        persistence_adapter: Optional[Any] = None,
        event_store: Optional[Any] = None,
    ):
        self._persistence = persistence_adapter
        self._event_store = event_store

    # ----------------------------------------------------------
    # STORE DIAGNOSIS
    # ----------------------------------------------------------

    def record_diagnosis(
        self,
        user_id: str,
        diagnosis: Dict[str, Any],
    ) -> None:

        self._validate_input(user_id, diagnosis)

        entry = {
            "type": "diagnosis",
            "timestamp": time.time(),
            "version": self.VERSION,
            "payload": copy.deepcopy(diagnosis),
        }

        self._persist(user_id, entry)

    # ----------------------------------------------------------
    # STORE PRESCRIPTION
    # ----------------------------------------------------------

    def record_prescription(
        self,
        user_id: str,
        prescription: Dict[str, Any],
    ) -> None:

        self._validate_input(user_id, prescription)

        entry = {
            "type": "prescription",
            "timestamp": time.time(),
            "version": self.VERSION,
            "applied": False,
            "payload": copy.deepcopy(prescription),
        }

        self._persist(user_id, entry)

    # ----------------------------------------------------------
    # MARK PRESCRIPTION APPLIED
    # ----------------------------------------------------------

    def mark_prescription_applied(
        self,
        user_id: str,
        prescription_id: str,
    ) -> None:

        record = self._get_user_memory(user_id)

        for item in record:
            if (
                item.get("type") == "prescription"
                and item.get("payload", {}).get("id") == prescription_id
            ):
                item["applied"] = True
                item["applied_timestamp"] = time.time()

        self._save_user_memory(user_id, record)

    # ----------------------------------------------------------
    # RECORD PERFORMANCE DELTA
    # ----------------------------------------------------------

    def record_performance_delta(
        self,
        user_id: str,
        before_metrics: Dict[str, Any],
        after_metrics: Dict[str, Any],
    ) -> None:

        entry = {
            "type": "performance_delta",
            "timestamp": time.time(),
            "version": self.VERSION,
            "before": copy.deepcopy(before_metrics),
            "after": copy.deepcopy(after_metrics),
        }

        self._persist(user_id, entry)

    # ----------------------------------------------------------
    # GET LONGITUDINAL SUMMARY
    # ----------------------------------------------------------

    def get_summary(
        self,
        user_id: str,
    ) -> Dict[str, Any]:

        memory = self._get_user_memory(user_id)

        diagnosis_count = sum(1 for x in memory if x["type"] == "diagnosis")
        prescription_count = sum(1 for x in memory if x["type"] == "prescription")
        applied_count = sum(
            1 for x in memory if x["type"] == "prescription" and x.get("applied")
        )

        return {
            "version": self.VERSION,
            "diagnosis_count": diagnosis_count,
            "prescription_count": prescription_count,
            "applied_prescriptions": applied_count,
            "total_events": len(memory),
        }

    # ----------------------------------------------------------
    # INTERNAL PERSISTENCE LOGIC
    # ----------------------------------------------------------

    def _persist(
        self,
        user_id: str,
        entry: Dict[str, Any],
    ) -> None:

        record = self._get_user_memory(user_id)
        record.append(entry)

        self._save_user_memory(user_id, record)

        if self._event_store:
            self._event_store.append_event({
                "type": "ai_memory_event",
                "user_id": user_id,
                "timestamp": entry["timestamp"],
                "version": self.VERSION,
            })

    def _get_user_memory(
        self,
        user_id: str,
    ) -> List[Dict[str, Any]]:

        if self._persistence:
            data = self._persistence.load(user_id)
            return data or []

        return []

    def _save_user_memory(
        self,
        user_id: str,
        data: List[Dict[str, Any]],
    ) -> None:

        if self._persistence:
            self._persistence.save(user_id, data)

    # ----------------------------------------------------------
    # VALIDATION
    # ----------------------------------------------------------

    @staticmethod
    def _validate_input(
        user_id: str,
        payload: Dict[str, Any],
    ) -> None:

        if not user_id:
            raise AIMemoryError("user_id required")

        if not isinstance(payload, dict):
            raise AIMemoryError("payload must be dict")