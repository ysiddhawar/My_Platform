from __future__ import annotations

from typing import Dict, List, Any
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from models.discipline_report import DisciplineReport


class ViolationTrackerError(Exception):
    pass


class ViolationTracker:
    """
    Institutional Behavioral Violation Tracker

    Responsibilities:
    - Store violation history per account
    - Track frequency of violations
    - Detect escalation patterns
    - Provide structured behavioral analytics
    - Support strictness escalation logic
    """

    def __init__(self):

        # account_id -> list of violation entries
        self._violation_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    # =====================================================
    # RECORD VIOLATION
    # =====================================================

    def record(self, account_id: str, report: DisciplineReport):

        if not isinstance(account_id, str) or not account_id.strip():
            raise ViolationTrackerError("Invalid account_id")

        if not isinstance(report, DisciplineReport):
            raise ViolationTrackerError("report must be DisciplineReport")

        report_data = report.to_dict()

        if not report_data.get("violations"):
            return  # No violation, nothing to record

        entry = {
            "timestamp": report_data["created_at"],
            "violations": report_data["violations"],
            "discipline_score": report_data["discipline_score"],
            "behavioral_flags": report_data["behavioral_flags"],
            "blocked": report_data["blocked"],
        }

        self._violation_history[account_id].append(entry)

    # =====================================================
    # ANALYTICS
    # =====================================================

    def get_total_violations(self, account_id: str) -> int:

        history = self._violation_history.get(account_id, [])
        return sum(len(entry["violations"]) for entry in history)

    def get_recent_violations(
        self,
        account_id: str,
        lookback_minutes: int = 60
    ) -> int:

        history = self._violation_history.get(account_id, [])
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=lookback_minutes)

        count = 0

        for entry in history:
            if entry["timestamp"].astimezone(timezone.utc) >= cutoff:
                count += len(entry["violations"])

        return count

    def detect_escalation(
        self,
        account_id: str,
        threshold: int = 5,
        window_minutes: int = 120
    ) -> bool:
        """
        Detect rapid violation accumulation.
        """

        recent = self.get_recent_violations(
            account_id,
            lookback_minutes=window_minutes
        )

        return recent >= threshold

    def detect_chronic_rule_skipping(
        self,
        account_id: str,
        minimum_instances: int = 3
    ) -> bool:
        """
        Detect repeated 'Rule Skipping' behavioral flags.
        """

        history = self._violation_history.get(account_id, [])

        count = 0

        for entry in history:
            if "Rule Skipping" in entry.get("behavioral_flags", []):
                count += 1

        return count >= minimum_instances

    def behavioral_summary(self, account_id: str) -> Dict[str, Any]:

        history = self._violation_history.get(account_id, [])

        violation_counter = defaultdict(int)
        flag_counter = defaultdict(int)

        for entry in history:
            for v in entry.get("violations", []):
                violation_counter[v] += 1
            for f in entry.get("behavioral_flags", []):
                flag_counter[f] += 1

        return {
            "total_records": len(history),
            "violation_frequency": dict(violation_counter),
            "behavioral_flag_frequency": dict(flag_counter),
        }

    # =====================================================
    # RESET / CLEANUP
    # =====================================================

    def clear_account_history(self, account_id: str):

        if account_id in self._violation_history:
            del self._violation_history[account_id]

    def clear_all(self):
        self._violation_history.clear()
