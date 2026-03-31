import unittest
from datetime import datetime, timezone

from ai.behavioral_analyzer import BehavioralAnalyzer
from ai.diagnostic_orchestrator import DiagnosticOrchestrator
from core.context import Context
from models.missed_opportunity import MissedOpportunity
from models.trade import Trade
from models.trading_platform_session import TradingPlatformSession


def _closed_trade(
    *,
    account_id: str,
    broker_id: str,
    symbol: str,
    strategy_tag: str,
    setup_name: str,
    entry_time: datetime,
    entry_price: float,
    exit_time: datetime,
    exit_price: float,
) -> Trade:
    trade = Trade(
        account_id=account_id,
        broker_id=broker_id,
        symbol=symbol,
        market_type="forex",
        side="buy",
        strategy_tag=strategy_tag,
        setup_name=setup_name,
        entry_price=entry_price,
        quantity=10000,
        lot_size=1.0,
        leverage_used=10.0,
        stop_loss_at_entry=entry_price - 0.0050,
        target_at_entry=entry_price + 0.0100,
        entry_time=entry_time,
    )
    trade.close_trade(
        exit_price=exit_price,
        exit_time=exit_time,
        exit_reason="manual",
    )
    return trade


class Phase3TimeIntelligenceTests(unittest.TestCase):
    def setUp(self):
        self.context = Context()
        self.behavioral_analyzer = BehavioralAnalyzer()
        self.diagnostic_orchestrator = DiagnosticOrchestrator()

    def test_behavioral_analyzer_adds_time_and_missed_opportunity_intelligence(self):
        trades = [
            _closed_trade(
                account_id="ACC-1",
                broker_id="BRK-1",
                symbol="EURUSD",
                strategy_tag="fade",
                setup_name="Fade A",
                entry_time=datetime(2026, 3, 9, 9, 0, tzinfo=timezone.utc),
                entry_price=1.1000,
                exit_time=datetime(2026, 3, 9, 9, 30, tzinfo=timezone.utc),
                exit_price=1.0950,
            ),
            _closed_trade(
                account_id="ACC-1",
                broker_id="BRK-1",
                symbol="EURUSD",
                strategy_tag="fade",
                setup_name="Fade B",
                entry_time=datetime(2026, 3, 9, 10, 0, tzinfo=timezone.utc),
                entry_price=1.1000,
                exit_time=datetime(2026, 3, 9, 10, 30, tzinfo=timezone.utc),
                exit_price=1.0960,
            ),
            _closed_trade(
                account_id="ACC-1",
                broker_id="BRK-1",
                symbol="EURUSD",
                strategy_tag="breakout",
                setup_name="Breakout A",
                entry_time=datetime(2026, 3, 11, 15, 0, tzinfo=timezone.utc),
                entry_price=1.1000,
                exit_time=datetime(2026, 3, 11, 15, 20, tzinfo=timezone.utc),
                exit_price=1.1120,
            ),
            _closed_trade(
                account_id="ACC-1",
                broker_id="BRK-1",
                symbol="EURUSD",
                strategy_tag="breakout",
                setup_name="Breakout B",
                entry_time=datetime(2026, 3, 11, 15, 30, tzinfo=timezone.utc),
                entry_price=1.1010,
                exit_time=datetime(2026, 3, 11, 15, 50, tzinfo=timezone.utc),
                exit_price=1.1120,
            ),
        ]
        sessions = [
            TradingPlatformSession(
                account_id="ACC-1",
                broker_id="BRK-1",
                platform_name="mt5",
                opened_at=datetime(2026, 3, 9, 8, 0, tzinfo=timezone.utc),
                closed_at=datetime(2026, 3, 9, 12, 0, tzinfo=timezone.utc),
            ),
            TradingPlatformSession(
                account_id="ACC-1",
                broker_id="BRK-1",
                platform_name="mt5",
                opened_at=datetime(2026, 3, 10, 8, 0, tzinfo=timezone.utc),
                closed_at=datetime(2026, 3, 10, 12, 0, tzinfo=timezone.utc),
            ),
            TradingPlatformSession(
                account_id="ACC-1",
                broker_id="BRK-1",
                platform_name="mt5",
                opened_at=datetime(2026, 3, 11, 14, 0, tzinfo=timezone.utc),
                closed_at=datetime(2026, 3, 11, 15, 0, tzinfo=timezone.utc),
            ),
        ]
        missed_opportunities = [
            MissedOpportunity(
                account_id="ACC-1",
                broker_id="BRK-1",
                symbol="EURUSD",
                market_type="forex",
                side="buy",
                strategy_name="breakout",
                probability_bucket="60%",
                entry_price=1.1000,
                stop_loss_price=1.0950,
                target_price=1.1120,
                minimum_target_price=1.1060,
                observed_at=datetime(2026, 3, 11, 15, 40, tzinfo=timezone.utc),
            ),
            MissedOpportunity(
                account_id="ACC-1",
                broker_id="BRK-1",
                symbol="EURUSD",
                market_type="forex",
                side="buy",
                strategy_name="breakout",
                probability_bucket="60%",
                entry_price=1.1000,
                stop_loss_price=1.0950,
                target_price=1.1120,
                minimum_target_price=1.1060,
                observed_at=datetime(2026, 3, 11, 15, 50, tzinfo=timezone.utc),
            ),
        ]

        self.context.set_cache("trades", trades)
        self.context.set_cache("trading_platform_sessions", sessions)
        self.context.set_cache("missed_opportunities", missed_opportunities)

        analysis = self.behavioral_analyzer.analyze(self.context)

        self.assertIn("time_intelligence", analysis)
        self.assertIn("missed_opportunity_intelligence", analysis)

        time_titles = {item["title"] for item in analysis["time_intelligence"]["findings"]}
        missed_titles = {item["title"] for item in analysis["missed_opportunity_intelligence"]["findings"]}

        self.assertIn("Weak weekday cluster detected", time_titles)
        self.assertIn("High-performing window underused", time_titles)
        self.assertIn("Profitable strategy opportunity gap", missed_titles)
        self.assertIn("Missed setups occurring away from active platform time", missed_titles)

    def test_diagnostic_orchestrator_accepts_contextual_time_findings(self):
        structured_metrics = {
            "journal": {},
            "performance": {},
            "risk": {},
            "distributions": {},
            "regimes": {},
            "robustness": {},
            "portfolio": {},
            "capital": {},
            "risk_control": {},
            "stress": {},
            "survival": {},
        }

        diagnosis = self.diagnostic_orchestrator.run(
            structured_metrics=structured_metrics,
            governance_tier="consistency",
            time_intelligence={
                "findings": [
                    {
                        "category": "time",
                        "title": "Weak weekday cluster detected",
                        "description": "Monday is underperforming in the sample.",
                        "severity": "medium",
                        "metric_reference": "weakest_day",
                    }
                ],
                "strengths": [
                    {
                        "category": "time",
                        "title": "Strong trading hour identified",
                        "description": "15:00 is a strong window.",
                        "severity": "info",
                        "metric_reference": "strongest_hour",
                    }
                ],
            },
            missed_opportunity_intelligence={
                "findings": [
                    {
                        "category": "missed_opportunity",
                        "title": "Profitable strategy opportunity gap",
                        "description": "Breakout opportunities are being missed.",
                        "severity": "high",
                        "metric_reference": "missed_profitable_strategy",
                    }
                ],
                "strengths": [],
            },
        )

        finding_titles = {item.title for item in diagnosis.findings}
        strength_titles = {item.title for item in diagnosis.strengths}

        self.assertIn("Weak weekday cluster detected", finding_titles)
        self.assertIn("Profitable strategy opportunity gap", finding_titles)
        self.assertIn("Strong trading hour identified", strength_titles)

    def test_behavioral_lookback_limits_sessions_and_missed_opportunities_too(self):
        recent_trade = _closed_trade(
            account_id="ACC-2",
            broker_id="BRK-2",
            symbol="EURUSD",
            strategy_tag="breakout",
            setup_name="Breakout",
            entry_time=datetime(2026, 3, 12, 15, 0, tzinfo=timezone.utc),
            entry_price=1.1000,
            exit_time=datetime(2026, 3, 12, 15, 30, tzinfo=timezone.utc),
            exit_price=1.1100,
        )
        old_trade = _closed_trade(
            account_id="ACC-2",
            broker_id="BRK-2",
            symbol="EURUSD",
            strategy_tag="fade",
            setup_name="Fade",
            entry_time=datetime(2026, 3, 1, 9, 0, tzinfo=timezone.utc),
            entry_price=1.1000,
            exit_time=datetime(2026, 3, 1, 9, 30, tzinfo=timezone.utc),
            exit_price=1.0950,
        )
        old_session = TradingPlatformSession(
            account_id="ACC-2",
            broker_id="BRK-2",
            platform_name="mt5",
            opened_at=datetime(2026, 3, 1, 8, 0, tzinfo=timezone.utc),
            closed_at=datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc),
        )
        recent_session = TradingPlatformSession(
            account_id="ACC-2",
            broker_id="BRK-2",
            platform_name="mt5",
            opened_at=datetime(2026, 3, 12, 14, 0, tzinfo=timezone.utc),
            closed_at=datetime(2026, 3, 12, 16, 0, tzinfo=timezone.utc),
        )
        old_missed = MissedOpportunity(
            account_id="ACC-2",
            broker_id="BRK-2",
            symbol="EURUSD",
            market_type="forex",
            side="buy",
            strategy_name="fade",
            probability_bucket="60%",
            entry_price=1.1,
            stop_loss_price=1.095,
            target_price=1.112,
            minimum_target_price=1.106,
            observed_at=datetime(2026, 3, 1, 9, 45, tzinfo=timezone.utc),
        )
        recent_missed = MissedOpportunity(
            account_id="ACC-2",
            broker_id="BRK-2",
            symbol="EURUSD",
            market_type="forex",
            side="buy",
            strategy_name="breakout",
            probability_bucket="60%",
            entry_price=1.1,
            stop_loss_price=1.095,
            target_price=1.112,
            minimum_target_price=1.106,
            observed_at=datetime(2026, 3, 12, 15, 45, tzinfo=timezone.utc),
        )

        self.context.set_cache("trades", [old_trade, recent_trade])
        self.context.set_cache("trading_platform_sessions", [old_session, recent_session])
        self.context.set_cache("missed_opportunities", [old_missed, recent_missed])

        analysis = self.behavioral_analyzer.analyze(self.context, lookback=1)

        self.assertEqual(
            set(analysis["time_intelligence"]["features"]["session_daily_totals"].keys()),
            {"2026-03-12"},
        )
        self.assertEqual(
            analysis["missed_opportunity_intelligence"]["features"]["total_missed_opportunities"],
            1,
        )


if __name__ == "__main__":
    unittest.main()
