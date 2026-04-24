from __future__ import annotations

from collections import defaultdict
from statistics import median
from typing import Any, Dict, Iterable, List, Sequence

from ai.insight_scoring import make_recommendation, rank_findings, rank_recommendations
from ai.insights_models import InsightFinding, Recommendation


class RecommendationEngine:
    """
    Turns scored findings into concrete, implementation-ready recommendations.

    Section analyzers are still allowed to emit hand-authored recommendations,
    but this engine centralizes the final recommendation layer so output stays:
    - actionable
    - traceable to source insights
    - deduplicated
    - ranked by the importance of the triggering findings
    """

    def generate(self, *, context: Dict[str, Any], analyses: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        section_outputs: Dict[str, List[Recommendation]] = {}
        all_findings: List[InsightFinding] = []
        all_recommendations: List[Recommendation] = []
        all_source_bucket_lookup: Dict[str, str] = {}

        for section_name, analysis in analyses.items():
            findings = self._ranked_findings_for_section(analysis)
            all_findings.extend(findings)
            section_source_bucket_lookup = self._source_bucket_lookup(analysis)
            all_source_bucket_lookup.update(section_source_bucket_lookup)

            generated: List[Recommendation] = []
            for bucket in ("wrong", "why", "right"):
                ranked_bucket = rank_findings(analysis.get(bucket, []), limit=8)
                for finding in ranked_bucket:
                    generated.extend(self._recommend_for_finding(context=context, finding=finding, bucket=bucket))

            combined = list(analysis.get("recommendations", [])) + generated
            ranked = self._dedupe_and_rank(
                combined,
                findings=findings,
                limit=6,
                source_bucket_lookup=section_source_bucket_lookup,
            )
            section_outputs[section_name] = ranked
            all_recommendations.extend(combined)

        return {
            "sections": section_outputs,
            "summary": self._dedupe_and_rank(
                all_recommendations,
                findings=all_findings,
                limit=6,
                source_bucket_lookup=all_source_bucket_lookup,
                prefer_corrective=True,
            ),
        }

    def _ranked_findings_for_section(self, analysis: Dict[str, Any]) -> List[InsightFinding]:
        return rank_findings(
            analysis.get("wrong", []) + analysis.get("why", []) + analysis.get("right", []),
            limit=16,
        )

    def _dedupe_and_rank(
        self,
        recommendations: Sequence[Recommendation],
        *,
        findings: Sequence[InsightFinding],
        limit: int,
        source_bucket_lookup: Dict[str, str] | None = None,
        prefer_corrective: bool = False,
    ) -> List[Recommendation]:
        finding_lookup = {finding.id: finding for finding in findings}
        best_by_key: Dict[tuple[str, ...], Recommendation] = {}

        for recommendation in recommendations:
            key = tuple(sorted(recommendation.source_insight_ids)) or (recommendation.title.lower(),)
            current = best_by_key.get(key)
            if current is None:
                best_by_key[key] = recommendation
                continue
            if self._recommendation_quality(recommendation, finding_lookup) > self._recommendation_quality(
                current, finding_lookup
            ):
                best_by_key[key] = recommendation

        ranked = rank_recommendations(best_by_key.values(), limit=len(best_by_key), finding_lookup=finding_lookup)
        if not prefer_corrective:
            return ranked[:limit]

        corrective = [
            item for item in ranked if self._recommendation_kind(item, source_bucket_lookup or {}) == "corrective"
        ]
        supportive = [
            item for item in ranked if self._recommendation_kind(item, source_bucket_lookup or {}) != "corrective"
        ]
        return (corrective + supportive)[:limit]

    def _source_bucket_lookup(self, analysis: Dict[str, Any]) -> Dict[str, str]:
        lookup: Dict[str, str] = {}
        for bucket in ("wrong", "why", "right"):
            for finding in analysis.get(bucket, []):
                lookup[finding.id] = bucket
        return lookup

    def _recommendation_kind(self, recommendation: Recommendation, source_bucket_lookup: Dict[str, str]) -> str:
        source_buckets = {source_bucket_lookup.get(source_id) for source_id in recommendation.source_insight_ids}
        if "wrong" in source_buckets or "why" in source_buckets:
            return "corrective"
        if "right" in source_buckets:
            return "supportive"
        return "neutral"

    def _recommendation_quality(
        self,
        recommendation: Recommendation,
        finding_lookup: Dict[str, InsightFinding],
    ) -> float:
        source_priority = max(
            (finding_lookup[source_id].priority_score for source_id in recommendation.source_insight_ids if source_id in finding_lookup),
            default=0.0,
        )
        return (
            source_priority
            + len(recommendation.implementation) * 2.0
            + (6.0 if recommendation.expected_benefit else 0.0)
            + len(recommendation.action)
        )

    def _recommend_for_finding(
        self,
        *,
        context: Dict[str, Any],
        finding: InsightFinding,
        bucket: str,
    ) -> List[Recommendation]:
        if bucket == "right":
            return self._positive_recommendations(context=context, finding=finding)
        return self._corrective_recommendations(context=context, finding=finding)

    def _corrective_recommendations(
        self,
        *,
        context: Dict[str, Any],
        finding: InsightFinding,
    ) -> List[Recommendation]:
        title = finding.title.lower()
        categories = set(finding.categories)
        dimensions = set(finding.dimensions)
        tags = set(finding.behavior_tags)

        if "overtrading" in tags or ("frequency" in categories and "trade frequency" in title):
            avg_trades = self._average_trades_per_active_day(context.get("trades", []))
            cap = max(2, int(round(avg_trades * 0.6))) if avg_trades > 0 else 3
            return [
                make_recommendation(
                    title="Install a hard daily trade cap",
                    action=f"Limit yourself to {cap} trades per active day until expectancy improves for 4 straight weeks.",
                    why="Trade frequency is high relative to current quality control, so fewer trades should force better selectivity.",
                    implementation=[
                        f"Stop initiating new positions after trade {cap} each day, even if additional setups appear.",
                        "Only break the cap if one of those skipped trades is documented as an A+ setup in notes.",
                        "Review the next 20 active days and compare expectancy for capped days versus uncapped history.",
                    ],
                    source_findings=[finding],
                    expected_benefit="Cuts low-conviction trades and usually improves average trade quality without needing a strategy change.",
                )
            ]

        if "drawdown" in title or "risk_escalation" in tags:
            return [
                make_recommendation(
                    title="Throttle risk during drawdown pressure",
                    action="Reduce base risk by 25% after two consecutive losses and restore it only after one fully plan-compliant winner.",
                    why="Your current downside pressure makes normal sizing more expensive, both financially and psychologically.",
                    implementation=[
                        "Define your baseline risk per trade and a reduced-risk band before the session starts.",
                        "Trigger reduced risk automatically after the second straight loss or any day that closes red beyond plan.",
                        "Return to baseline risk only after a winning trade that followed checklist, sizing, and exit rules.",
                    ],
                    source_findings=[finding],
                    expected_benefit="Slows drawdown acceleration and keeps weak patches from forcing oversized recovery attempts.",
                )
            ]

        if "discipline_break" in tags or "loss streak" in title:
            reset_after = max(2, self._extract_first_int(finding, "loss streak", default=3))
            return [
                make_recommendation(
                    title="Pause after 3 straight losses",
                    action=f"After {reset_after} consecutive losses, stop trading for one setup cycle and resume at reduced size.",
                    why="Loss streaks usually worsen when rhythm is broken and the next trade becomes emotional instead of process-led.",
                    implementation=[
                        f"Pause new entries immediately after loss number {reset_after}.",
                        "Review the last streak trades for checklist misses, size drift, and early exits before resuming.",
                        "Restart with half size on the next valid setup, then return to full size only after a rule-compliant winner.",
                    ],
                    source_findings=[finding],
                    expected_benefit="Prevents small cold spells from turning into cascading drawdowns.",
                )
            ]

        if "strategy switching" in title or "fomo" in tags:
            return [
                make_recommendation(
                    title="Narrow the active playbook",
                    action="Trade only your top 2 validated setups for the next 15 sessions and tag every trade outside that list as a rule break.",
                    why="Frequent switching usually reduces familiarity and makes execution inconsistent.",
                    implementation=[
                        "Identify the two setups with the strongest expectancy or cleanest execution history.",
                        "Write them on your session plan before the open and reject setups outside that pair.",
                        "Review whether decision speed and post-trade grading improve when the playbook stays narrow.",
                    ],
                    source_findings=[finding],
                    expected_benefit="Improves repetition quality and reduces random setup drift.",
                )
            ]

        if "early exits" in title or "hesitation" in tags and "time" in dimensions:
            return [
                make_recommendation(
                    title="Stick to a written exit plan",
                    action="Define the exact exit trigger before entry and do not manually close the trade early unless that trigger prints.",
                    why="Your reward capture is likely being cut by reactive exits instead of plan-based exits.",
                    implementation=[
                        "Write target, stop, and one valid early-exit reason before placing the order.",
                        "If you exit early, log whether the allowed trigger was actually present.",
                        "At week end, compare average win size for ladder-followed trades versus manually managed trades.",
                    ],
                    source_findings=[finding],
                    expected_benefit="Improves average winner size and helps expectancy convert into realized P&L.",
                )
            ]

        if "missed" in title or "hesitation" in tags:
            top_setup = self._evidence_value(finding, "top missed setup") or "your highest-friction setup"
            return [
                make_recommendation(
                    title="Add an execute-or-skip trigger checklist",
                    action=f"Build a one-page trigger checklist for {top_setup} and require an explicit execute-or-skip decision each time it appears.",
                    why="You are seeing valid setups but not converting enough of them into actual trades.",
                    implementation=[
                        "Pick one frequently missed setup first instead of trying to fix all missed opportunities at once.",
                        "List 3 objective entry conditions and 1 acceptable skip condition for that setup.",
                        "When the setup appears, mark execute or skip in real time and review the misses every Friday.",
                    ],
                    source_findings=[finding],
                    expected_benefit="Converts recognized edge into realized trades without increasing random activity.",
                )
            ]

        if "weekday" in title or "day" in dimensions:
            weakest_day = self._evidence_value(finding, "highest-risk weekday") or self._weekday_from_title(finding.title)
            weakest_day = weakest_day or self._weakest_weekday(context.get("calendar_summaries", [])) or "that weekday"
            return [
                make_recommendation(
                    title="Apply a weekday-specific quality filter",
                    action=f"Trade 20-30% smaller on {weakest_day} and only take A-grade setups there for the next month.",
                    why="Your data shows edge quality is not uniform across weekdays, so the weak day needs tighter standards.",
                    implementation=[
                        f"Mark {weakest_day} as a restricted-risk day in your plan.",
                        "Skip B-grade and late-session trades on that weekday until the numbers stabilize.",
                        "Compare weekday expectancy after 4 weeks before restoring normal size.",
                    ],
                    source_findings=[finding],
                    expected_benefit="Reduces repeated loss clusters while preserving capital for stronger trading windows.",
                )
            ]

        if "session-time" in title or ("session" in dimensions and "time" in dimensions):
            limit_minutes = self._suggest_session_limit(context.get("platform_sessions", []))
            return [
                make_recommendation(
                    title="Set a hard session-time stop",
                    action=f"Cap active platform time at {limit_minutes} minutes on normal days unless the session is still inside a pre-defined A+ setup window.",
                    why="Longer sessions are showing signs of fatigue or degraded selectivity.",
                    implementation=[
                        "Define your maximum normal session length before the open.",
                        "When the cap is reached, continue only if one written A+ setup condition is still active.",
                        "Track whether the last hour of screen time improves or hurts next-week expectancy.",
                    ],
                    source_findings=[finding],
                    expected_benefit="Improves focus quality and reduces fatigue-driven trades late in the day.",
                )
            ]

        if "setup performance changes materially by symbol" in title:
            strong_pair = self._evidence_value(finding, "strongest setup-symbol pair")
            weak_pair = self._evidence_value(finding, "weakest setup-symbol pair")
            return [
                make_recommendation(
                    title="Only trade setups on symbols where they already work",
                    action=f"Reduce exposure to {weak_pair or 'weak setup-symbol combinations'} and reallocate review time toward {strong_pair or 'your strongest pair'}.",
                    why="The same setup is not equally strong across symbols, so treating every symbol the same is diluting edge.",
                    implementation=[
                        "Create an approved setup-symbol matrix using your last 20-30 closed trades.",
                        "Block new trades in weak pairs unless they rebuild a positive sample.",
                        "Review pair performance weekly and only expand after the weak pair posts a stable positive expectancy.",
                    ],
                    source_findings=[finding],
                    expected_benefit="Focuses risk on proven combinations and removes hidden edge decay.",
                )
            ]

        if "profit factor below 1" in title or ("strategy" in categories and "execution" in categories):
            return [
                make_recommendation(
                    title="Raise the minimum trade-quality threshold",
                    action="Require every trade to meet a stricter quality gate before entry until profit factor recovers above your acceptable band.",
                    why="Losses are currently outweighing gains, so the fastest fix is usually selective participation rather than more activity.",
                    implementation=[
                        "Add one more confirmation requirement to your entry checklist for the next 15 sessions.",
                        "Skip any setup that does not meet the full quality gate, even if it is familiar.",
                        "Measure whether skipped trades are mostly low-quality losers or missed winners before keeping the stricter filter.",
                    ],
                    source_findings=[finding],
                    expected_benefit="Improves payoff quality and can move the system back toward positive profitability faster than broad strategy changes.",
                )
            ]

        return []

    def _positive_recommendations(
        self,
        *,
        context: Dict[str, Any],
        finding: InsightFinding,
    ) -> List[Recommendation]:
        title = finding.title.lower()
        categories = set(finding.categories)
        tags = set(finding.behavior_tags)

        if "checklist" in title or "consistency" in tags:
            return [
                make_recommendation(
                    title="Protect your best execution habit",
                    action="Keep checklist compliance mandatory and review one high-quality trade each week to preserve that discipline edge.",
                    why="Strong checklist adherence is a process advantage you do not want to dilute while fixing weaker areas.",
                    implementation=[
                        "Save one example each week of a trade that followed the full checklist and plan.",
                        "Use it as the benchmark when reviewing losing trades or rushed entries.",
                        "Do not loosen checklist rules while you are optimizing other parts of the system.",
                    ],
                    source_findings=[finding],
                    expected_benefit="Helps you improve performance without sacrificing the discipline already working in your favor.",
                )
            ]

        if "expectancy is positive" in title or "risk-adjusted return baseline is healthy" in title:
            return [
                make_recommendation(
                    title="Scale only from your strongest baseline",
                    action="Keep current core strategy behavior intact and test changes around the edges, not in the middle of what is already working.",
                    why="You already have a positive baseline, so the goal is to protect it while removing weak pockets.",
                    implementation=[
                        "Freeze one version of your current rules as the baseline playbook.",
                        "Test only one improvement at a time, such as weekday filtering or smaller size after losses.",
                        "Accept a change only if expectancy and drawdown both improve over a meaningful sample.",
                    ],
                    source_findings=[finding],
                    expected_benefit="Preserves existing edge while making future improvements easier to validate.",
                )
            ]

        if "strength day" in title or ("strategy" in categories and "day" in finding.dimensions):
            strong_day = self._weekday_from_title(finding.title) or self._strongest_weekday(context.get("calendar_summaries", []))
            return [
                make_recommendation(
                    title="Lean into your strongest trading window carefully",
                    action=f"Use {strong_day or 'your best weekday'} as the benchmark day for execution review and reserve your highest-conviction setups for that window first.",
                    why="You already have a time window where your edge expresses more clearly.",
                    implementation=[
                        "Review what is different on the strong day: session timing, setup quality, and trade count.",
                        "Replicate those conditions on weaker days before adding more trades.",
                        "Avoid increasing size just because the day is strong; use it first as a model for cleaner execution.",
                    ],
                    source_findings=[finding],
                    expected_benefit="Helps you transfer strong behaviors into weaker periods without forcing unnecessary risk expansion.",
                )
            ]

        if "edge pair" in title or "setup" in finding.dimensions and "symbol" in finding.dimensions:
            edge_pair = self._evidence_value(finding, "strongest setup-symbol pair")
            return [
                make_recommendation(
                    title="Build around the cleanest edge pair",
                    action=f"Keep tracking {edge_pair or 'your strongest setup-symbol pair'} separately and use it as the reference standard for expansion decisions.",
                    why="Your best edge pair is already showing evidence of repeatability.",
                    implementation=[
                        "Create a separate performance note or tag for the strongest pair.",
                        "Compare every new setup or symbol idea against that pair before allocating equal risk.",
                        "Expand only when a new pair shows comparable quality across a meaningful sample.",
                    ],
                    source_findings=[finding],
                    expected_benefit="Protects your highest-quality edge from being diluted by weaker ideas.",
                )
            ]

        return []

    def _average_trades_per_active_day(self, trades: Sequence[Dict[str, Any]]) -> float:
        trades_by_day: Dict[str, int] = defaultdict(int)
        for trade in trades:
            day_key = (
                trade.get("entry_date")
                or (str(trade.get("entry_time"))[:10] if trade.get("entry_time") else None)
                or trade.get("exit_date")
            )
            if day_key:
                trades_by_day[str(day_key)] += 1
        if not trades_by_day:
            return 0.0
        return sum(trades_by_day.values()) / len(trades_by_day)

    def _suggest_session_limit(self, sessions: Sequence[Dict[str, Any]]) -> int:
        minutes: List[float] = []
        for session in sessions:
            value = session.get("duration_minutes")
            if value is None:
                value = session.get("minutes_within_day")
            try:
                minutes.append(float(value))
            except (TypeError, ValueError):
                continue
        if not minutes:
            return 180
        baseline = median(minutes)
        return max(90, int(round(baseline * 0.85)))

    def _weekday_from_title(self, title: str) -> str | None:
        for weekday in ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"):
            if weekday.lower() in title.lower():
                return weekday
        return None

    def _weakest_weekday(self, calendar_summaries: Sequence[Dict[str, Any]]) -> str | None:
        averages = self._weekday_averages(calendar_summaries)
        if not averages:
            return None
        return min(averages, key=averages.get)

    def _strongest_weekday(self, calendar_summaries: Sequence[Dict[str, Any]]) -> str | None:
        averages = self._weekday_averages(calendar_summaries)
        if not averages:
            return None
        return max(averages, key=averages.get)

    def _weekday_averages(self, calendar_summaries: Sequence[Dict[str, Any]]) -> Dict[str, float]:
        buckets: Dict[str, List[float]] = defaultdict(list)
        for item in calendar_summaries:
            raw_day = item.get("day")
            if not raw_day:
                continue
            try:
                weekday = str(raw_day)
                if len(weekday) >= 10 and "-" in weekday:
                    from datetime import datetime

                    weekday = datetime.fromisoformat(str(raw_day)).strftime("%A")
            except ValueError:
                continue
            buckets[weekday].append(float(item.get("pnl") or 0.0))
        return {key: sum(values) / len(values) for key, values in buckets.items() if values}

    def _evidence_value(self, finding: InsightFinding, label_fragment: str) -> str | None:
        fragment = label_fragment.lower()
        for item in finding.evidence:
            if fragment in item.label.lower():
                return item.value
        return None

    def _extract_first_int(self, finding: InsightFinding, label_fragment: str, *, default: int) -> int:
        value = self._evidence_value(finding, label_fragment)
        if not value:
            return default
        digits = "".join(char for char in value if char.isdigit())
        if not digits:
            return default
        return int(digits)
