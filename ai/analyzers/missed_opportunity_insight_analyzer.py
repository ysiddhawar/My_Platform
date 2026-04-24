from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List

from ai.insight_scoring import build_evidence, make_finding, make_recommendation
from ai.insights_models import InsightDrilldown, InsightFinding, Recommendation


class MissedOpportunityInsightAnalyzer:
    def analyze(self, context: Dict[str, Any]) -> Dict[str, List[Any]]:
        missed = context.get("missed_opportunities", [])
        closed = context.get("closed_trades", [])
        sample_size = max(1, len(missed) + len(closed))

        wrong: List[InsightFinding] = []
        why: List[InsightFinding] = []
        right: List[InsightFinding] = []
        recommendations: List[Recommendation] = []

        missed_ratio = len(missed) / max(1, len(closed))
        high_missed_finding = None
        if missed and missed_ratio > 0.25:
            top_strategy, top_count = self._top_key(missed, "strategy_name")
            high_missed_finding = make_finding(
                title="A large portion of valid setups are being missed",
                explanation="Missed opportunities are high relative to executed closed trades, which suggests edge capture slippage.",
                categories=["execution", "consistency", "strategy"],
                dimensions=["setup", "symbol", "session"],
                behavior_tags=["hesitation"],
                sample_size=sample_size,
                impact_score=min(1.0, missed_ratio),
                evidence=build_evidence(
                    [
                        ("Missed opportunities", str(len(missed))),
                        ("Closed trades", str(len(closed))),
                        ("Missed ratio", f"{missed_ratio:.2f}"),
                        ("Most missed strategy", f"{top_strategy} ({top_count})"),
                    ]
                ),
                impact_description="Improving execution of qualified setups can increase return capture without forcing more random trades.",
                drilldown=InsightDrilldown(
                    view="missed-opportunities",
                    missed_opportunity_search_text=top_strategy,
                ),
            )
            wrong.append(high_missed_finding)

        if missed:
            top_symbol, top_symbol_count = self._top_key(missed, "symbol")
            concentration_ratio = top_symbol_count / max(1, len(missed))
            if top_symbol_count >= 3 and concentration_ratio >= 0.30:
                why.append(
                    make_finding(
                        title="Missed opportunities are concentrated in a few symbols/setups",
                        explanation="Concentration suggests specific execution friction instead of random misses.",
                        categories=["execution", "strategy"],
                        dimensions=["symbol", "setup", "market"],
                        behavior_tags=["hesitation", "fomo"],
                        sample_size=sample_size,
                        impact_score=min(1.0, concentration_ratio),
                        evidence=build_evidence(
                            [
                                ("Top missed symbol", f"{top_symbol} ({top_symbol_count})"),
                                ("Unique missed symbols", str(len({str(item.get('symbol') or 'Unknown') for item in missed}))),
                                ("Concentration ratio", f"{concentration_ratio:.2f}"),
                            ]
                        ),
                        impact_description="Targeted fixes on the highest-friction symbols can quickly reduce missed-edge leakage.",
                        drilldown=InsightDrilldown(
                            view="missed-opportunities",
                            missed_opportunity_search_text=top_symbol,
                        ),
                    )
                )

        if missed and missed_ratio <= 0.15:
            right.append(
                make_finding(
                    title="Missed setup ratio is currently controlled",
                    explanation="Relative to closed trades, missed opportunities are staying in a manageable range.",
                    categories=["consistency", "execution"],
                    dimensions=["setup", "session"],
                    behavior_tags=["consistency"],
                    sample_size=sample_size,
                    impact_score=0.35,
                    evidence=build_evidence(
                        [
                            ("Missed opportunities", str(len(missed))),
                            ("Missed ratio", f"{missed_ratio:.2f}"),
                        ]
                    ),
                    impact_description="Maintaining this ratio protects your realized edge from avoidable leakage.",
                )
            )

        if high_missed_finding is not None:
            recommendations.append(
                make_recommendation(
                    title="Deploy a pre-session execution shortlist",
                    action="Create a fixed 3-setup priority list each session and force an explicit execute/skip decision for each trigger.",
                    why="A high missed ratio indicates setup recognition is not translating into execution.",
                    implementation=[
                        "Before session start, list three highest-conviction setup+symbol combinations.",
                        "For each trigger, log execute or skip with one reason.",
                        "Review missed profitable triggers weekly and convert repeated reasons into rules.",
                    ],
                    source_findings=[high_missed_finding],
                    expected_benefit="Higher edge capture without increasing overtrading pressure.",
                )
            )

        return {
            "wrong": wrong,
            "why": why,
            "right": right,
            "recommendations": recommendations,
        }

    def _top_key(self, rows: List[Dict[str, Any]], key: str) -> tuple[str, int]:
        counter = Counter(str(row.get(key) or "Unknown") for row in rows)
        if not counter:
            return ("Unknown", 0)
        item, count = counter.most_common(1)[0]
        return item, count
