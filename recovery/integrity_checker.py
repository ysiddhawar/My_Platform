from __future__ import annotations

from typing import Dict, Any, List, Optional
from dataclasses import dataclass


class IntegrityError(Exception):
    pass


@dataclass
class IntegrityReport:
    is_valid: bool
    errors: List[str]
    warnings: List[str]


class IntegrityChecker:
    """
    Institutional Integrity Checker

    Responsibilities:
    - Validate event sequence continuity
    - Validate snapshot consistency
    - Validate config version alignment
    - Validate account state coherence
    - Prevent unsafe recovery execution
    """

    # ==========================================================
    # PUBLIC ENTRY
    # ==========================================================

    def validate(
        self,
        events: List[Dict[str, Any]],
        snapshot: Optional[Dict[str, Any]],
        active_config: Optional[Dict[str, Any]],
        account_state: Optional[Dict[str, Any]],
    ) -> IntegrityReport:

        errors: List[str] = []
        warnings: List[str] = []

        # ------------------------------------------------------
        # 1️⃣ EVENT SEQUENCE VALIDATION
        # ------------------------------------------------------

        if events:
            seq_numbers: list[int] = [e["sequence"] for e in events if "sequence" in e]

            if not seq_numbers:
                errors.append("Events missing sequence field")

            else:
                expected = list(range(min(seq_numbers), max(seq_numbers) + 1))
                if sorted(seq_numbers) != expected:
                    errors.append("Event sequence gap detected")

        # ------------------------------------------------------
        # 2️⃣ SNAPSHOT VALIDATION
        # ------------------------------------------------------

        if snapshot:
            if "schema_version" not in snapshot:
                errors.append("Snapshot missing schema_version")

            if "state" not in snapshot:
                errors.append("Snapshot missing state payload")

        # ------------------------------------------------------
        # 3️⃣ CONFIG VALIDATION
        # ------------------------------------------------------

        if active_config:
            if not isinstance(active_config, dict):
                errors.append("Active config corrupted")

            if "max_risk_percent" in active_config:
                if active_config["max_risk_percent"] <= 0:
                    errors.append("Invalid max_risk_percent in config")

        else:
            warnings.append("No active config found")

        # ------------------------------------------------------
        # 4️⃣ ACCOUNT STATE VALIDATION
        # ------------------------------------------------------

        if account_state:
            if account_state.get("equity", 0) < 0:
                errors.append("Negative equity detected")

            if account_state.get("balance", 0) < 0:
                errors.append("Negative balance detected")

        else:
            warnings.append("No account state found")

        # ------------------------------------------------------
        # FINAL DECISION
        # ------------------------------------------------------

        is_valid = len(errors) == 0

        return IntegrityReport(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
        )