from __future__ import annotations

import uuid
from typing import Optional, Dict, Any, List


class StrategyValidationError(Exception):
    pass


class Strategy:
    """
    Institutional-Grade Strategy Definition Model

    Represents a formal strategy contract.

    Used by:
    - Discipline layer
    - Acceptance engine
    - AI interpretation layer
    - Capital governance layer
    - Execution gatekeeper
    """

    __slots__ = (
        "_strategy_id",
        "_name",
        "_description",
        "_market_types",
        "_checklist_items",
        "_mandatory_checklist_items",
        "_risk_profile",
        "_acceptance_rules",
        "_rejection_rules",
        "_level_classification_rules",
        "_default_risk_percent",
        "_max_risk_percent",
        "_is_active",
        "_metadata",
    )

    # =====================================================
    # INITIALIZATION
    # =====================================================

    def __init__(
        self,
        name: str,
        description: str,
        market_types: List[str],
        checklist_items: List[str],
        mandatory_checklist_items: Optional[List[str]] = None,
        risk_profile: Optional[Dict[str, Any]] = None,
        acceptance_rules: Optional[Dict[str, Any]] = None,
        rejection_rules: Optional[Dict[str, Any]] = None,
        level_classification_rules: Optional[Dict[str, Any]] = None,
        default_risk_percent: float = 1.0,
        max_risk_percent: float = 2.0,
        is_active: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ):

        self._strategy_id = str(uuid.uuid4())

        self._name = self._validate_non_empty(name, "name")
        self._description = self._validate_non_empty(description, "description")

        self._market_types = self._validate_string_list(
            market_types, "market_types"
        )

        self._checklist_items = self._validate_string_list(
            checklist_items, "checklist_items"
        )

        self._mandatory_checklist_items = (
            self._validate_string_list(
                mandatory_checklist_items, "mandatory_checklist_items"
            )
            if mandatory_checklist_items
            else []
        )

        self._risk_profile = risk_profile or {}
        self._acceptance_rules = acceptance_rules or {}
        self._rejection_rules = rejection_rules or {}
        self._level_classification_rules = level_classification_rules or {}

        self._default_risk_percent = self._validate_positive(
            default_risk_percent, "default_risk_percent"
        )

        self._max_risk_percent = self._validate_positive(
            max_risk_percent, "max_risk_percent"
        )

        if self._default_risk_percent > self._max_risk_percent:
            raise StrategyValidationError(
                "default_risk_percent cannot exceed max_risk_percent"
            )

        self._is_active = bool(is_active)
        self._metadata = metadata or {}

    # =====================================================
    # VALIDATION UTILITIES
    # =====================================================

    def _validate_non_empty(self, value: str, field: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise StrategyValidationError(f"{field} must be non-empty string")
        return value.strip()

    def _validate_string_list(self, value: List[str], field: str) -> List[str]:
        if not isinstance(value, list):
            raise StrategyValidationError(f"{field} must be a list")
        cleaned = []
        for item in value:
            if not isinstance(item, str) or not item.strip():
                raise StrategyValidationError(
                    f"{field} must contain non-empty strings"
                )
            cleaned.append(item.strip())
        return cleaned

    def _validate_positive(self, value: float, field: str) -> float:
        if not isinstance(value, (int, float)) or value <= 0:
            raise StrategyValidationError(f"{field} must be positive")
        return float(value)

    # =====================================================
    # CHECKLIST LOGIC
    # =====================================================

    def validate_checklist(self, selected_items: List[str]) -> Dict[str, Any]:
        """
        Validates selected checklist items.

        Returns:
            {
                "missing_mandatory": [...],
                "invalid_items": [...],
                "is_valid": bool
            }
        """

        selected_items = selected_items or []

        missing_mandatory = [
            item
            for item in self._mandatory_checklist_items
            if item not in selected_items
        ]

        invalid_items = [
            item
            for item in selected_items
            if item not in self._checklist_items
        ]

        is_valid = len(missing_mandatory) == 0

        return {
            "missing_mandatory": missing_mandatory,
            "invalid_items": invalid_items,
            "is_valid": is_valid,
        }

    # =====================================================
    # GOVERNANCE RULE ACCESS
    # =====================================================

    @property
    def acceptance_rules(self) -> Dict[str, Any]:
        return dict(self._acceptance_rules)

    @property
    def rejection_rules(self) -> Dict[str, Any]:
        return dict(self._rejection_rules)

    @property
    def level_classification_rules(self) -> Dict[str, Any]:
        return dict(self._level_classification_rules)

    @property
    def default_risk_percent(self) -> float:
        return self._default_risk_percent

    @property
    def max_risk_percent(self) -> float:
        return self._max_risk_percent

    @property
    def name(self) -> str:
        return self._name

    @property
    def checklist_items(self) -> List[str]:
        return list(self._checklist_items)

    @property
    def mandatory_checklist_items(self) -> List[str]:
        return list(self._mandatory_checklist_items)

    @property
    def strategy_id(self) -> str:
        return self._strategy_id

    @property
    def is_active(self) -> bool:
        return self._is_active

    # =====================================================
    # ACTIVATION CONTROL
    # =====================================================

    def deactivate(self):
        self._is_active = False

    def activate(self):
        self._is_active = True

    # =====================================================
    # EXPORT
    # =====================================================

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy_id": self._strategy_id,
            "name": self._name,
            "description": self._description,
            "market_types": self._market_types,
            "checklist_items": self._checklist_items,
            "mandatory_checklist_items": self._mandatory_checklist_items,
            "risk_profile": self._risk_profile,
            "acceptance_rules": self._acceptance_rules,
            "rejection_rules": self._rejection_rules,
            "level_classification_rules": self._level_classification_rules,
            "default_risk_percent": self._default_risk_percent,
            "max_risk_percent": self._max_risk_percent,
            "is_active": self._is_active,
            "metadata": self._metadata,
        }

    def __repr__(self):
        state = "ACTIVE" if self._is_active else "INACTIVE"
        return f"<Strategy {self._name} {state}>"
