from __future__ import annotations

import uuid
import time
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional


# ---------------------------------------------------------
# Severity Levels (Deterministic – No AI Guessing Here)
# ---------------------------------------------------------

SEVERITY_LEVELS = ("info", "low", "medium", "high", "critical")


def _validate_severity(level: str) -> str:
    if level not in SEVERITY_LEVELS:
        raise ValueError(f"Invalid severity level: {level}")
    return level


# ---------------------------------------------------------
# Diagnostic Finding (Atomic Unit)
# ---------------------------------------------------------

@dataclass(frozen=True)
class DiagnosticFinding:
    """
    Represents a single structured finding.

    Example:
        - Low Sharpe ratio
        - High tail risk
        - Strategy drift detected
        - Overtrading behavior
    """

    category: str
    title: str
    description: str
    severity: str
    metric_reference: Optional[str] = None
    value: Optional[Any] = None
    threshold: Optional[Any] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        object.__setattr__(self, "severity", _validate_severity(self.severity))

        if not self.category:
            raise ValueError("DiagnosticFinding must have category")

        if not self.title:
            raise ValueError("DiagnosticFinding must have title")

        if not self.description:
            raise ValueError("DiagnosticFinding must have description")


# ---------------------------------------------------------
# Aggregated Diagnosis Object
# ---------------------------------------------------------

class AIDiagnosis:
    """
    Institutional-grade diagnostic container.

    This object:
    - Aggregates findings across layers
    - Tracks risk tier classification
    - Tracks behavioral instability flags
    - Stores system health score
    - Remains deterministic and auditable
    """

    __slots__ = (
        "_diagnosis_id",
        "_created_at",
        "_findings",
        "_strengths",
        "_risk_tier",
        "_health_score",
        "_metadata",
    )

    def __init__(
        self,
        risk_tier: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self._diagnosis_id = str(uuid.uuid4())
        self._created_at = time.time()
        self._findings: List[DiagnosticFinding] = []
        self._strengths: List[DiagnosticFinding] = []
        self._risk_tier = risk_tier
        self._health_score: Optional[float] = None
        self._metadata = metadata or {}

    # -----------------------------------------------------
    # Add Findings
    # -----------------------------------------------------

    def add_finding(self, finding: DiagnosticFinding):
        if not isinstance(finding, DiagnosticFinding):
            raise TypeError("Invalid finding type")
        self._findings.append(finding)

    def add_strength(self, finding: DiagnosticFinding):
        if not isinstance(finding, DiagnosticFinding):
            raise TypeError("Invalid strength type")
        self._strengths.append(finding)

    # -----------------------------------------------------
    # Health Scoring (Deterministic Calculation)
    # -----------------------------------------------------

    def compute_health_score(self):
        """
        Converts severity distribution into a normalized health score.
        Fully deterministic.
        """

        if not self._findings:
            self._health_score = 100.0
            return self._health_score

        severity_weight = {
            "info": 0,
            "low": 1,
            "medium": 3,
            "high": 6,
            "critical": 10,
        }

        total_penalty = sum(
            severity_weight[f.severity] for f in self._findings
        )

        raw_score = max(0.0, 100.0 - total_penalty)
        self._health_score = round(raw_score, 2)

        return self._health_score

    # -----------------------------------------------------
    # Risk Tier Classification (Governed Layer)
    # -----------------------------------------------------

    def set_risk_tier(self, tier: str):
        if not tier:
            raise ValueError("Risk tier cannot be empty")
        self._risk_tier = tier

    # -----------------------------------------------------
    # Accessors
    # -----------------------------------------------------

    @property
    def diagnosis_id(self) -> str:
        return self._diagnosis_id

    @property
    def created_at(self) -> float:
        return self._created_at

    @property
    def findings(self) -> List[DiagnosticFinding]:
        return list(self._findings)

    @property
    def strengths(self) -> List[DiagnosticFinding]:
        return list(self._strengths)

    @property
    def risk_tier(self) -> Optional[str]:
        return self._risk_tier

    @property
    def health_score(self) -> Optional[float]:
        return self._health_score

    @property
    def metadata(self) -> Dict[str, Any]:
        return dict(self._metadata)

    def severity_distribution(self) -> Dict[str, int]:
        counts = {level: 0 for level in SEVERITY_LEVELS}
        for finding in self._findings:
            counts[finding.severity] = counts.get(finding.severity, 0) + 1
        return counts

    # -----------------------------------------------------
    # Structured Export (Platform Compatible)
    # -----------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "diagnosis_id": self._diagnosis_id,
            "created_at": self._created_at,
            "risk_tier": self._risk_tier,
            "health_score": self._health_score,
            "findings": [
                {
                    "category": f.category,
                    "title": f.title,
                    "description": f.description,
                    "severity": f.severity,
                    "metric_reference": f.metric_reference,
                    "value": f.value,
                    "threshold": f.threshold,
                    "metadata": f.metadata,
                }
                for f in self._findings
            ],
            "strengths": [
                {
                    "category": s.category,
                    "title": s.title,
                    "description": s.description,
                    "severity": s.severity,
                    "metric_reference": s.metric_reference,
                    "value": s.value,
                    "threshold": s.threshold,
                    "metadata": s.metadata,
                }
                for s in self._strengths
            ],
            "metadata": self._metadata,
        }

    # -----------------------------------------------------
    # Integrity Validation
    # -----------------------------------------------------

    def validate(self):
        """
        Ensures structural consistency before AI prescription layer.
        """

        if self._health_score is None:
            self.compute_health_score()

        if not isinstance(self._findings, list):
            raise RuntimeError("Findings container corrupted")

        for f in self._findings:
            if not isinstance(f, DiagnosticFinding):
                raise RuntimeError("Invalid finding detected")

        return True
