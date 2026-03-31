from __future__ import annotations

from typing import Dict, Any, Optional

from models.ai_diagnosis import AIDiagnosis
from models.ai_diagnosis import DiagnosticFinding
from ai.metric_interpreter import MetricInterpreter
from ai.behavioral_interpreter import BehavioralInterpreter


class DiagnosticOrchestrator:
    """
    AI Doctor Brain (Policy-Driven + Adaptive)

    Responsibilities:
    - Accept structured metric output (Option B)
    - Accept adaptive percentile/zscore inputs
    - Ensure ALL metric categories are present
    - Aggregate metric + behavioral findings
    - Produce structured AIDiagnosis
    - Remain deterministic and auditable
    """

    REQUIRED_CATEGORIES = (
        "journal",
        "performance",
        "risk",
        "distributions",
        "regimes",
        "robustness",
        "portfolio",
        "capital",
        "risk_control",
        "stress",
        "survival",
    )

    def __init__(
        self,
        metric_interpreter: Optional[MetricInterpreter] = None,
        behavioral_interpreter: Optional[BehavioralInterpreter] = None,
    ):
        self.metric_interpreter = metric_interpreter or MetricInterpreter()
        self.behavioral_interpreter = (
            behavioral_interpreter or BehavioralInterpreter()
        )

    # -----------------------------------------------------
    # Public Interface
    # -----------------------------------------------------

    def run(
        self,
        structured_metrics: Dict[str, Dict[str, Any]],
        governance_tier: str,
        percentiles: Optional[Dict[str, float]] = None,
        zscores: Optional[Dict[str, float]] = None,
        behavioral_signals: Optional[Dict[str, Any]] = None,
        time_intelligence: Optional[Dict[str, Any]] = None,
        missed_opportunity_intelligence: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AIDiagnosis:

        self._validate_structured_metrics(structured_metrics)

        diagnosis = AIDiagnosis(
            risk_tier=governance_tier,
            metadata=metadata,
        )

        # ---------------------------------------------
        # Metric Interpretation (Policy-Driven)
        # ---------------------------------------------

        metric_findings = self.metric_interpreter.interpret(
            structured_metrics=structured_metrics,
            governance_tier=governance_tier,
            percentiles=percentiles,
            zscores=zscores,
        )

        for finding in metric_findings.get("weaknesses", []):
            diagnosis.add_finding(finding)

        for strength in metric_findings.get("strengths", []):
            diagnosis.add_strength(strength)

        # ---------------------------------------------
        # Behavioral Interpretation
        # ---------------------------------------------

        if behavioral_signals:
            behavioral_findings = self.behavioral_interpreter.interpret(
                behavioral_signals,
                percentiles=percentiles,
                zscores=zscores,
            )

            for finding in behavioral_findings.get("weaknesses", []):
                diagnosis.add_finding(finding)

            for strength in behavioral_findings.get("strengths", []):
                diagnosis.add_strength(strength)

        self._append_contextual_findings(diagnosis, time_intelligence)
        self._append_contextual_findings(diagnosis, missed_opportunity_intelligence)

        # ---------------------------------------------
        # Final Scoring + Validation
        # ---------------------------------------------

        diagnosis.compute_health_score()
        diagnosis.validate()

        return diagnosis

    def _append_contextual_findings(
        self,
        diagnosis: AIDiagnosis,
        intelligence: Optional[Dict[str, Any]],
    ) -> None:
        if not intelligence:
            return
        for finding in intelligence.get("findings", []):
            diagnosis.add_finding(self._coerce_finding(finding))
        for strength in intelligence.get("strengths", []):
            diagnosis.add_strength(self._coerce_finding(strength))

    def _coerce_finding(self, payload: Any) -> DiagnosticFinding:
        if isinstance(payload, DiagnosticFinding):
            return payload
        if not isinstance(payload, dict):
            raise TypeError("Contextual intelligence finding must be dict or DiagnosticFinding")
        return DiagnosticFinding(
            category=payload["category"],
            title=payload["title"],
            description=payload["description"],
            severity=payload["severity"],
            metric_reference=payload.get("metric_reference"),
            value=payload.get("value"),
            threshold=payload.get("threshold"),
            metadata=payload.get("metadata", {}),
        )

    # -----------------------------------------------------
    # Internal Validation
    # -----------------------------------------------------

    def _validate_structured_metrics(
        self,
        structured_metrics: Dict[str, Dict[str, Any]],
    ):

        if not isinstance(structured_metrics, dict):
            raise TypeError("structured_metrics must be dict")

        for category in self.REQUIRED_CATEGORIES:

            if category not in structured_metrics:
                raise ValueError(
                    f"Missing required metrics category: {category}"
                )

            if not isinstance(structured_metrics[category], dict):
                raise TypeError(
                    f"Category '{category}' must contain dict"
                )
