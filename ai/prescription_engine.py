from __future__ import annotations

from typing import Dict, Any, Optional

from models.ai_diagnosis import AIDiagnosis, DiagnosticFinding
from models.ai_prescription import (
    AIPrescription,
    PrescriptionInstruction,
)


class PrescriptionEngine:
    """
    AI Doctor Prescription Layer

    Responsibilities:
    - Convert structured AIDiagnosis into structured AIPrescription
    - Respect governance tier
    - Separate auto-applicable vs manual actions
    - Never override platform governance logic
    - Remain deterministic and auditable
    """

    # Governance-based risk caps (deterministic rules)
    GOVERNANCE_RISK_CAPS = {
        "survival": 0.25,
        "consistency": 0.5,
        "profitable": 1.0,
    }

    def generate(
        self,
        diagnosis: AIDiagnosis,
        current_config: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AIPrescription:
        """
        Main entry point.
        """

        if not isinstance(diagnosis, AIDiagnosis):
            raise TypeError("Invalid diagnosis object")

        diagnosis.validate()

        prescription = AIPrescription(
            diagnosis_id=diagnosis.diagnosis_id,
            metadata=metadata,
        )

        risk_tier = diagnosis.risk_tier or "survival"

        # ---------------------------------------------
        # Governance Risk Adjustment
        # ---------------------------------------------

        risk_cap = self.GOVERNANCE_RISK_CAPS.get(
            risk_tier,
            self.GOVERNANCE_RISK_CAPS["survival"],
        )

        current_risk = None
        if current_config:
            current_risk = current_config.get("risk_per_trade")

        if current_risk is None or current_risk > risk_cap:
            prescription.add_instruction(
                PrescriptionInstruction(
                    action_type="risk_adjustment",
                    title="Reduce risk per trade",
                    description=(
                        f"Your current risk exposure exceeds "
                        f"{risk_tier} tier recommendation. "
                        f"Adjust risk per trade to {risk_cap}%."
                    ),
                    parameter="risk_per_trade",
                    recommended_value=risk_cap,
                    current_value=current_risk,
                    auto_applicable=True,
                )
            )

        # ---------------------------------------------
        # Process Diagnostic Findings
        # ---------------------------------------------

        for finding in diagnosis.findings:

            self._map_finding_to_instruction(
                finding=finding,
                prescription=prescription,
                risk_tier=risk_tier,
                current_config=current_config,
            )

        prescription.validate()

        return prescription

    # -----------------------------------------------------
    # Finding → Instruction Mapping
    # -----------------------------------------------------

    def _map_finding_to_instruction(
        self,
        finding: DiagnosticFinding,
        prescription: AIPrescription,
        risk_tier: str,
        current_config: Optional[Dict[str, Any]],
    ):

        category = finding.category
        severity = finding.severity

        # ---------------------------------------------
        # Performance Issues
        # ---------------------------------------------

        if category == "performance" and severity in ("high", "critical"):
            prescription.add_instruction(
                PrescriptionInstruction(
                    action_type="strategy_restriction",
                    title="Restrict underperforming strategy",
                    description=(
                        "Performance metrics indicate persistent weakness. "
                        "Consider pausing or re-evaluating this strategy."
                    ),
                    parameter="strategy",
                    recommended_value="review_or_pause",
                    auto_applicable=False,
                )
            )

        # ---------------------------------------------
        # Risk Issues
        # ---------------------------------------------

        if category == "risk" and severity in ("high", "critical"):
            prescription.add_instruction(
                PrescriptionInstruction(
                    action_type="position_size_adjustment",
                    title="Reduce position size",
                    description=(
                        "Risk exposure is elevated relative to stability. "
                        "Reduce maximum position size."
                    ),
                    parameter="max_position_size",
                    recommended_value="reduce",
                    auto_applicable=True,
                )
            )

        # ---------------------------------------------
        # Behavioral Issues
        # ---------------------------------------------

        if category == "behavioral" and severity in ("medium", "high", "critical"):
            prescription.add_instruction(
                PrescriptionInstruction(
                    action_type="behavioral_reinforcement",
                    title="Strengthen checklist discipline",
                    description=(
                        "Detected behavioral inconsistency. "
                        "Reinforce checklist adherence before execution."
                    ),
                    parameter="checklist_enforcement",
                    recommended_value="strict",
                    auto_applicable=False,
                )
            )

        # ---------------------------------------------
        # Portfolio Fragility
        # ---------------------------------------------

        if category == "portfolio" and severity in ("high", "critical"):
            prescription.add_instruction(
                PrescriptionInstruction(
                    action_type="capital_reallocation",
                    title="Rebalance portfolio exposure",
                    description=(
                        "Portfolio correlation or fragility risk detected. "
                        "Adjust capital allocation to reduce concentration."
                    ),
                    parameter="portfolio_allocation",
                    recommended_value="rebalance",
                    auto_applicable=False,
                )
            )

        # ---------------------------------------------
        # Survival Risk
        # ---------------------------------------------

        if category == "survival" and severity in ("high", "critical"):
            prescription.add_instruction(
                PrescriptionInstruction(
                    action_type="execution_constraint",
                    title="Activate protective constraints",
                    description=(
                        "Account survival risk elevated. "
                        "Enable stricter capital throttle and kill-switch thresholds."
                    ),
                    parameter="protective_mode",
                    recommended_value=True,
                    auto_applicable=True,
                )
            )