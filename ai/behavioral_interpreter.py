from __future__ import annotations

from typing import Dict, Any, Optional

from models.ai_diagnosis import DiagnosticFinding


class BehavioralInterpreterError(Exception):
    pass


class BehavioralInterpreter:
    """
    Adaptive Behavioral Signal Interpreter

    Responsibilities:
    - Detect statistical behavioral anomalies
    - Compare current behavior vs historical baseline
    - Use percentile / zscore inputs
    - Produce structured anomaly signals
    - NEVER assign psychological labels directly
    """

    REQUIRED_SIGNALS = (
        "loss_streak_length",
        "risk_drift",
        "strategy_switch_frequency",
        "discipline_score_trend",
        "violation_frequency",
        "position_size_volatility",
        "trade_frequency",
    )

    def interpret(
        self,
        signals: Dict[str, Any],
        percentiles: Optional[Dict[str, float]] = None,
        zscores: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:

        if not isinstance(signals, dict):
            raise BehavioralInterpreterError("signals must be dict")

        anomalies = []
        severity_score = 0.0
        weaknesses = []
        strengths = []

        percentiles = percentiles or {}
        zscores = zscores or {}

        # ---------------------------------------------
        # Risk Escalation Anomaly
        # ---------------------------------------------

        risk_drift = signals.get("risk_drift")
        risk_drift_pct = percentiles.get("risk_drift")

        if risk_drift_pct is not None and risk_drift_pct > 0.90:
            anomalies.append({
                "type": "risk_escalation_anomaly",
                "value": risk_drift,
                "percentile": risk_drift_pct,
            })
            weaknesses.append(
                DiagnosticFinding(
                    category="behavior",
                    title="Risk drift detected",
                    description="Recent trade risk is trending above the trader's historical baseline.",
                    severity="medium",
                    metric_reference="risk_drift",
                    value=risk_drift,
                    threshold=0.90,
                )
            )
            severity_score += 20

        # ---------------------------------------------
        # Strategy Switching Instability
        # ---------------------------------------------

        switch_pct = percentiles.get("strategy_switch_frequency")

        if switch_pct is not None and switch_pct > 0.85:
            anomalies.append({
                "type": "strategy_instability",
                "percentile": switch_pct,
            })
            weaknesses.append(
                DiagnosticFinding(
                    category="behavior",
                    title="Strategy switching instability",
                    description="Setup selection is changing faster than the recent baseline, which often signals execution drift.",
                    severity="medium",
                    metric_reference="strategy_switch_frequency",
                    value=switch_pct,
                    threshold=0.85,
                )
            )
            severity_score += 15

        # ---------------------------------------------
        # Discipline Volatility
        # ---------------------------------------------

        discipline_z = zscores.get("discipline_score_trend")

        if discipline_z is not None and discipline_z < -2.0:
            anomalies.append({
                "type": "discipline_degradation",
                "zscore": discipline_z,
            })
            weaknesses.append(
                DiagnosticFinding(
                    category="behavior",
                    title="Discipline score degrading",
                    description="Recent discipline quality is materially weaker than the prior baseline.",
                    severity="high",
                    metric_reference="discipline_score_trend",
                    value=discipline_z,
                    threshold=-2.0,
                )
            )
            severity_score += 20

        # ---------------------------------------------
        # Violation Clustering
        # ---------------------------------------------

        violation_pct = percentiles.get("violation_frequency")

        if violation_pct is not None and violation_pct > 0.90:
            anomalies.append({
                "type": "violation_cluster",
                "percentile": violation_pct,
            })
            weaknesses.append(
                DiagnosticFinding(
                    category="behavior",
                    title="Rule violations clustering",
                    description="Trade rule deviations are clustering above the historical baseline.",
                    severity="medium",
                    metric_reference="violation_frequency",
                    value=violation_pct,
                    threshold=0.90,
                )
            )
            severity_score += 15

        # ---------------------------------------------
        # Position Size Instability
        # ---------------------------------------------

        size_vol_pct = percentiles.get("position_size_volatility")

        if size_vol_pct is not None and size_vol_pct > 0.90:
            anomalies.append({
                "type": "position_sizing_instability",
                "percentile": size_vol_pct,
            })
            weaknesses.append(
                DiagnosticFinding(
                    category="behavior",
                    title="Position sizing instability",
                    description="Position size is fluctuating more than usual, which can indicate execution inconsistency.",
                    severity="medium",
                    metric_reference="position_size_volatility",
                    value=size_vol_pct,
                    threshold=0.90,
                )
            )
            severity_score += 15

        # ---------------------------------------------
        # Loss Cluster Intensity
        # ---------------------------------------------

        loss_pct = percentiles.get("loss_streak_length")

        if loss_pct is not None and loss_pct > 0.95:
            anomalies.append({
                "type": "loss_cluster_anomaly",
                "percentile": loss_pct,
            })
            weaknesses.append(
                DiagnosticFinding(
                    category="behavior",
                    title="Loss cluster anomaly",
                    description="Loss streak intensity is in the extreme tail of recent behavior.",
                    severity="high",
                    metric_reference="loss_streak_length",
                    value=loss_pct,
                    threshold=0.95,
                )
            )
            severity_score += 20

        if signals.get("early_exit_rate", 0.0) > 0.30:
            weaknesses.append(
                DiagnosticFinding(
                    category="behavior",
                    title="Early exits detected",
                    description="Positions are being closed before target or stop more often than expected.",
                    severity="high",
                    metric_reference="early_exit_rate",
                    value=signals.get("early_exit_rate"),
                    threshold=0.30,
                )
            )

        checklist_rate = signals.get("checklist_compliance_rate")
        if checklist_rate is not None and checklist_rate < 0.8:
            weaknesses.append(
                DiagnosticFinding(
                    category="behavior",
                    title="Checklist incompleteness",
                    description="Mandatory criteria are not being fully selected on a consistent basis.",
                    severity="medium",
                    metric_reference="checklist_compliance_rate",
                    value=checklist_rate,
                    threshold=0.8,
                )
            )
        elif checklist_rate is not None and checklist_rate >= 0.95:
            strengths.append(
                DiagnosticFinding(
                    category="behavior",
                    title="Checklist discipline strong",
                    description="Mandatory setup criteria are being completed consistently.",
                    severity="info",
                    metric_reference="checklist_compliance_rate",
                    value=checklist_rate,
                    threshold=0.95,
                )
            )

        setup_drift = signals.get("setup_drift_rate")
        if setup_drift is not None and setup_drift > 0.20:
            weaknesses.append(
                DiagnosticFinding(
                    category="behavior",
                    title="Pre/post setup drift",
                    description="Post-trade review differs from pre-trade intent often enough to signal setup classification drift.",
                    severity="medium",
                    metric_reference="setup_drift_rate",
                    value=setup_drift,
                    threshold=0.20,
                )
            )

        # ---------------------------------------------
        # Normalize Score
        # ---------------------------------------------

        severity_score = min(severity_score, 100.0)

        return {
            "behavioral_anomalies": anomalies,
            "behavioral_risk_score": severity_score,
            "confidence_score": round(min(1.0, severity_score / 100.0), 2),
            "weaknesses": weaknesses,
            "strengths": strengths,
        }
