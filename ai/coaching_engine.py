from __future__ import annotations

from typing import List, Dict, Any, Optional

from models.ai_diagnosis import AIDiagnosis, DiagnosticFinding
from models.ai_prescription import AIPrescription, PrescriptionInstruction
from models.ai_followup_report import AIFollowupReport


class CoachingEngineError(Exception):
    pass


class CoachingEngine:
    """
    Institutional Coaching Engine

    Responsibilities:
    - Convert AIDiagnosis into structured AIPrescription
    - Respect governance tiers (survival / consistency / profitable)
    - Never invent thresholds
    - Never override policy engine
    - Produce auto-apply compatible instructions
    - Track follow-up compliance logic

    This module DOES NOT:
    - Compute metrics
    - Detect anomalies
    - Enforce kill switches
    """

    # ==========================================================
    # PUBLIC ENTRY
    # ==========================================================

    def generate_prescription(
        self,
        diagnosis: AIDiagnosis,
        structured_metrics: Dict[str, Dict[str, Any]],
        governance_tier: str,
        previous_prescription: Optional[AIPrescription] = None,
    ) -> AIPrescription:

        if not isinstance(diagnosis, AIDiagnosis):
            raise CoachingEngineError("diagnosis must be AIDiagnosis")

        actions: List[Dict[str, Any]] = []
        narrative_sections: List[str] = []

        # ----------------------------------------------
        # 1️⃣ METRIC-BASED ACTIONS
        # ----------------------------------------------

        for finding in diagnosis.findings:

            action = self._map_finding_to_action(
                finding,
                governance_tier,
                structured_metrics,
            )

            if action:
                actions.append(action)

        # ----------------------------------------------
        # 2️⃣ BEHAVIORAL ACTIONS
        # ----------------------------------------------

        for finding in diagnosis.findings:
            if finding.category in {"behavioral", "behavior"}:
                behavior_action = self._behavioral_adjustment(finding)
                if behavior_action:
                    actions.append(behavior_action)

        # ----------------------------------------------
        # 3️⃣ CAPITAL TIER GOVERNANCE ADJUSTMENT
        # ----------------------------------------------

        capital_adjustment = self._capital_tier_adjustment(
            governance_tier,
            structured_metrics
        )

        if capital_adjustment:
            actions.append(capital_adjustment)

        # ----------------------------------------------
        # 4️⃣ BUILD NARRATIVE
        # ----------------------------------------------

        narrative_sections.append(
            self._build_summary(diagnosis, governance_tier)
        )

        # ----------------------------------------------
        # 5️⃣ CREATE PRESCRIPTION OBJECT
        # ----------------------------------------------

        prescription = AIPrescription(
            diagnosis_id=diagnosis.diagnosis_id,
            metadata={
                "governance_tier": governance_tier,
                "narrative": "\n\n".join(narrative_sections),
            },
        )
        for action in actions:
            instruction = self._instruction_from_action(action)
            if instruction is not None:
                prescription.add_instruction(instruction)

        return prescription

    # ==========================================================
    # INTERNAL LOGIC
    # ==========================================================

    def _map_finding_to_action(
        self,
        finding: DiagnosticFinding,
        governance_tier: str,
        metrics: Dict[str, Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:

        category = finding.category

        # -------------------------------
        # Performance instability
        # -------------------------------

        if category == "performance" and finding.severity in ("high", "critical"):
            return {
                "type": "reduce_risk",
                "recommended_risk_percent": self._tier_risk_limit(governance_tier),
                "auto_applicable": True,
            }

        # -------------------------------
        # Survival risk
        # -------------------------------

        if category == "survival":
            return {
                "type": "capital_protection_mode",
                "recommended_risk_percent": 0.25,
                "auto_applicable": True,
            }

        # -------------------------------
        # Portfolio concentration
        # -------------------------------

        if category == "portfolio":
            return {
                "type": "reduce_correlation_exposure",
                "auto_applicable": False,
            }

        # -------------------------------
        # Stress fragility
        # -------------------------------

        if category == "stress":
            return {
                "type": "reduce_leverage",
                "auto_applicable": True,
            }

        return None

    # ==========================================================
    # BEHAVIORAL ADJUSTMENTS
    # ==========================================================

    def _behavioral_adjustment(
        self,
        finding: DiagnosticFinding
    ) -> Optional[Dict[str, Any]]:

        return {
            "type": "behavioral_correction",
            "focus_area": finding.metric_reference,
            "auto_applicable": False,
        }

    def _instruction_from_action(
        self,
        action: Dict[str, Any],
    ) -> Optional[PrescriptionInstruction]:
        action_type = action.get("type")
        if not action_type:
            return None

        mapped_type = {
            "reduce_risk": "risk_adjustment",
            "set_fixed_risk": "risk_adjustment",
            "capital_protection_mode": "regime_constraint",
            "reduce_correlation_exposure": "capital_reallocation",
            "reduce_leverage": "position_size_adjustment",
            "adaptive_position_sizing": "position_size_adjustment",
            "behavioral_correction": "behavioral_reinforcement",
        }.get(action_type)
        if mapped_type is None:
            return None

        return PrescriptionInstruction(
            action_type=mapped_type,
            title=self._action_title(action),
            description=self._action_description(action),
            parameter=action.get("focus_area"),
            recommended_value=action.get("recommended_risk_percent"),
            applies_to=action.get("focus_area"),
            auto_applicable=bool(action.get("auto_applicable", False)),
            metadata=dict(action),
        )

    def _action_title(self, action: Dict[str, Any]) -> str:
        action_type = action.get("type")
        return {
            "reduce_risk": "Reduce risk per trade",
            "set_fixed_risk": "Set fixed risk limit",
            "capital_protection_mode": "Enter capital protection mode",
            "reduce_correlation_exposure": "Reduce correlated exposure",
            "reduce_leverage": "Lower leverage pressure",
            "adaptive_position_sizing": "Use adaptive position sizing",
            "behavioral_correction": "Apply behavioral correction",
        }.get(action_type, "Apply corrective action")

    def _action_description(self, action: Dict[str, Any]) -> str:
        action_type = action.get("type")
        if action_type in {"reduce_risk", "set_fixed_risk"}:
            return f"Adjust risk to {action.get('recommended_risk_percent')}% until the profile stabilizes."
        if action_type == "capital_protection_mode":
            return "Tighten execution constraints to protect capital during elevated structural risk."
        if action_type == "reduce_correlation_exposure":
            return "Reduce overlapping exposure so correlated positions do not amplify downside."
        if action_type == "reduce_leverage":
            return "Lower effective leverage to keep stress and execution fragility under control."
        if action_type == "adaptive_position_sizing":
            return "Use adaptive position sizing so capital deployment reflects changing conditions."
        if action_type == "behavioral_correction":
            return f"Focus corrective attention on {action.get('focus_area') or 'behavioral execution'}."
        return "Apply a corrective adjustment."

    # ==========================================================
    # CAPITAL TIER LOGIC
    # ==========================================================

    def _capital_tier_adjustment(
        self,
        governance_tier: str,
        metrics: Dict[str, Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:

        if governance_tier == "survival":
            return {
                "type": "set_fixed_risk",
                "recommended_risk_percent": 0.25,
                "auto_applicable": True,
            }

        if governance_tier == "consistency":
            return {
                "type": "set_fixed_risk",
                "recommended_risk_percent": 0.5,
                "auto_applicable": True,
            }

        if governance_tier == "profitable":
            return {
                "type": "adaptive_position_sizing",
                "auto_applicable": True,
            }

        return None

    # ==========================================================
    # TIER RISK LIMIT
    # ==========================================================

    def _tier_risk_limit(self, governance_tier: str) -> float:

        if governance_tier == "survival":
            return 0.25

        if governance_tier == "consistency":
            return 0.5

        if governance_tier == "profitable":
            return 1.0

        return 0.25

    # ==========================================================
    # SUMMARY BUILDER
    # ==========================================================

    def _build_summary(
        self,
        diagnosis: AIDiagnosis,
        governance_tier: str,
    ) -> str:

        if not diagnosis.findings:
            return (
                "Performance profile appears stable. "
                "Continue executing with discipline."
            )

        severity_counts = diagnosis.severity_distribution()

        return (
            f"Current governance tier: {governance_tier}. "
            f"Detected {severity_counts.get('high', 0)} high-severity "
            f"and {severity_counts.get('critical', 0)} critical structural risks. "
            "Risk control adjustments recommended."
        )
