from __future__ import annotations

from typing import List, Dict, Any, Callable

from models.execution_event import ExecutionEvent
from models.strategy import Strategy
from models.account import Account
from models.discipline_report import DisciplineReport


class DisciplineRuleError(Exception):
    pass


class DisciplineRulesEngine:
    """
    Institutional Discipline Rules Engine

    Responsibilities:
    - Evaluate checklist compliance
    - Evaluate risk violations
    - Evaluate leverage violations
    - Evaluate exposure violations
    - Apply strict mode logic
    - Produce DisciplineReport

    This engine is deterministic and rule-based.
    AI does NOT decide rules here.
    """

    def __init__(self):

        self._custom_rules: List[Callable] = []

    # =====================================================
    # RULE REGISTRATION (EXTENSIBLE)
    # =====================================================

    def register_rule(self, rule_callable: Callable):
        """
        Allows external rule injection.
        Must accept (event, strategy, account)
        and return (rule_name, passed: bool, message: str)
        """
        if not callable(rule_callable):
            raise DisciplineRuleError("rule_callable must be callable")
        self._custom_rules.append(rule_callable)

    # =====================================================
    # MAIN ENTRY POINT
    # =====================================================

    def evaluate(
        self,
        event: ExecutionEvent,
        strategy: Strategy,
        account: Account
    ) -> DisciplineReport:

        rules_evaluated = []
        rules_passed = []
        rules_failed = []
        violations = []
        behavioral_flags = []

        # -------------------------------------------------
        # CHECKLIST VALIDATION
        # -------------------------------------------------

        checklist_result = strategy.validate_checklist(
            event.to_dict().get("selected_checklist", [])
        )

        missing_mandatory = checklist_result["missing_mandatory"]
        invalid_items = checklist_result["invalid_items"]

        if missing_mandatory:
            violations.append("Missing mandatory checklist items")
            behavioral_flags.append("Rule Skipping")

        if invalid_items:
            violations.append("Invalid checklist items selected")

        # -------------------------------------------------
        # RISK RULE
        # -------------------------------------------------

        rules_evaluated.append("risk_limit")

        if event.to_dict().get("risk_percent") is not None:
            if event.to_dict()["risk_percent"] > account.allowed_risk_percent:
                rules_failed.append("risk_limit")
                violations.append("Risk percent exceeds allowed level")
            else:
                rules_passed.append("risk_limit")

        # -------------------------------------------------
        # LEVERAGE RULE
        # -------------------------------------------------

        rules_evaluated.append("leverage_limit")

        if event.to_dict()["intended_leverage"] > account.max_leverage_allowed:
            rules_failed.append("leverage_limit")
            violations.append("Leverage exceeds allowed maximum")
        else:
            rules_passed.append("leverage_limit")

        # -------------------------------------------------
        # EXPOSURE RULE
        # -------------------------------------------------

        rules_evaluated.append("max_open_positions")

        if account.to_dict()["open_positions_count"] >= 10:
            rules_failed.append("max_open_positions")
            violations.append("Too many open positions")
        else:
            rules_passed.append("max_open_positions")

        # -------------------------------------------------
        # CUSTOM RULES
        # -------------------------------------------------

        for rule in self._custom_rules:
            name, passed, message = rule(event, strategy, account)
            rules_evaluated.append(name)
            if passed:
                rules_passed.append(name)
            else:
                rules_failed.append(name)
                violations.append(message)

        # -------------------------------------------------
        # STRICT MODE LOGIC
        # -------------------------------------------------

        strict_mode = event.strict_mode
        blocked = False

        if strict_mode and (missing_mandatory or rules_failed):
            blocked = True

        # -------------------------------------------------
        # DISCIPLINE SCORE
        # -------------------------------------------------

        total_rules = len(rules_evaluated) or 1
        discipline_score = (len(rules_passed) / total_rules) * 100

        violation_severity_score = min(len(violations) * 10, 100)

        summary = self._generate_summary(
            blocked,
            discipline_score,
            violations
        )

        recommended_actions = self._generate_recommendations(
            violations,
            missing_mandatory
        )

        # -------------------------------------------------
        # BUILD REPORT
        # -------------------------------------------------

        report = DisciplineReport(
            entity_type="execution_event",
            entity_id=event.to_dict()["event_id"],
            strategy_tag=strategy.name,
            setup_name=event.to_dict()["setup_name"],
            selected_checklist=event.to_dict()["selected_checklist"],
            mandatory_checklist=strategy.to_dict()["mandatory_checklist_items"],
            missing_mandatory=missing_mandatory,
            invalid_items=invalid_items,
            rules_evaluated=rules_evaluated,
            rules_passed=rules_passed,
            rules_failed=rules_failed,
            violations=violations,
            violation_severity_score=violation_severity_score,
            behavioral_flags=behavioral_flags,
            strict_mode=strict_mode,
            blocked=blocked,
            discipline_score=discipline_score,
            summary=summary,
            recommended_actions=recommended_actions,
        )

        return report

    # =====================================================
    # SUMMARY GENERATOR
    # =====================================================

    def _generate_summary(
        self,
        blocked: bool,
        discipline_score: float,
        violations: List[str]
    ) -> str:

        if blocked:
            return (
                f"Trade blocked due to rule violations. "
                f"Discipline score: {discipline_score:.1f}%"
            )

        if violations:
            return (
                f"Trade allowed with warnings. "
                f"Discipline score: {discipline_score:.1f}%"
            )

        return (
            f"Trade fully compliant. "
            f"Discipline score: {discipline_score:.1f}%"
        )

    # =====================================================
    # RECOMMENDATION GENERATOR
    # =====================================================

    def _generate_recommendations(
        self,
        violations: List[str],
        missing_mandatory: List[str]
    ) -> List[str]:

        recommendations = []

        if missing_mandatory:
            recommendations.append(
                "Ensure all mandatory checklist items are satisfied before entry."
            )

        for v in violations:
            if "Risk percent" in v:
                recommendations.append(
                    "Reduce position risk to allowed level."
                )
            if "Leverage" in v:
                recommendations.append(
                    "Reduce leverage to permitted maximum."
                )

        return recommendations