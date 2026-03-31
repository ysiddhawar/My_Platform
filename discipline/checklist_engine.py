from __future__ import annotations

from typing import List, Dict, Any, Optional


class ChecklistEngineError(Exception):
    pass


class ChecklistEngine:
    """
    Institutional Checklist Validation Engine

    Responsibilities:
    - Validate pre-trade checklist
    - Validate post-trade checklist
    - Merge global + strategy-specific checklist
    - Detect missing mandatory items
    - Detect invalid items
    - Detect over-selection corruption
    - Produce structured validation output

    This engine is deterministic and rule-based.
    """

    def __init__(
        self,
        global_mandatory: Optional[List[str]] = None,
        global_optional: Optional[List[str]] = None,
    ):

        self._global_mandatory = self._sanitize_list(global_mandatory)
        self._global_optional = self._sanitize_list(global_optional)

    # =====================================================
    # PUBLIC API
    # =====================================================

    def validate_pre_trade(
        self,
        selected_items: List[str],
        strategy_mandatory: Optional[List[str]] = None,
        strategy_optional: Optional[List[str]] = None,
    ) -> Dict[str, Any]:

        return self._validate(
            selected_items=selected_items,
            strategy_mandatory=strategy_mandatory,
            strategy_optional=strategy_optional,
        )

    def validate_post_trade(
        self,
        selected_items: List[str],
        strategy_mandatory: Optional[List[str]] = None,
        strategy_optional: Optional[List[str]] = None,
    ) -> Dict[str, Any]:

        return self._validate(
            selected_items=selected_items,
            strategy_mandatory=strategy_mandatory,
            strategy_optional=strategy_optional,
        )

    # =====================================================
    # CORE VALIDATION LOGIC
    # =====================================================

    def _validate(
        self,
        selected_items: List[str],
        strategy_mandatory: Optional[List[str]],
        strategy_optional: Optional[List[str]],
    ) -> Dict[str, Any]:

        selected = self._sanitize_list(selected_items)
        strategy_mandatory = self._sanitize_list(strategy_mandatory)
        strategy_optional = self._sanitize_list(strategy_optional)

        all_mandatory = set(self._global_mandatory + strategy_mandatory)
        all_optional = set(self._global_optional + strategy_optional)

        allowed_items = all_mandatory.union(all_optional)

        missing_mandatory = list(all_mandatory - set(selected))
        invalid_items = [item for item in selected if item not in allowed_items]

        duplicate_items = self._detect_duplicates(selected_items)

        completeness_score = self._calculate_completeness(
            selected,
            all_mandatory,
            all_optional
        )

        return {
            "selected_items": selected,
            "mandatory_items": list(all_mandatory),
            "optional_items": list(all_optional),
            "missing_mandatory": missing_mandatory,
            "invalid_items": invalid_items,
            "duplicate_items": duplicate_items,
            "completeness_score": completeness_score,
        }

    # =====================================================
    # HELPERS
    # =====================================================

    def _sanitize_list(self, items: Optional[List[str]]) -> List[str]:

        if not items:
            return []

        if not isinstance(items, list):
            raise ChecklistEngineError("Checklist must be list")

        clean = []

        for item in items:
            if not isinstance(item, str):
                raise ChecklistEngineError("Checklist items must be string")
            stripped = item.strip()
            if stripped:
                clean.append(stripped)

        return clean

    def _detect_duplicates(self, items: List[str]) -> List[str]:

        seen = set()
        duplicates = set()

        for item in items:
            if item in seen:
                duplicates.add(item)
            seen.add(item)

        return list(duplicates)

    def _calculate_completeness(
        self,
        selected: List[str],
        mandatory: set,
        optional: set
    ) -> float:

        if not mandatory and not optional:
            return 100.0

        score = 0.0

        if mandatory:
            satisfied = len(mandatory.intersection(selected))
            score += (satisfied / len(mandatory)) * 70.0

        if optional:
            satisfied_optional = len(optional.intersection(selected))
            score += (satisfied_optional / len(optional)) * 30.0

        return round(score, 2)