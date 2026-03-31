import unittest
from datetime import datetime, timezone

from ai.behavioral_analyzer import BehavioralAnalyzer
from ai.coaching_engine import CoachingEngine
from api.journal.router import behavioral_snapshot
from api.server.api_registry import api_registry
from core.context import Context
from models.ai_diagnosis import AIDiagnosis, DiagnosticFinding
from models.trade import Trade


def _trade_with_strategy(account_id: str, strategy_tag: str, entry_hour: int) -> Trade:
    trade = Trade(
        account_id=account_id,
        broker_id="BRK-AUDIT",
        symbol="EURUSD",
        market_type="forex",
        side="buy",
        strategy_tag=strategy_tag,
        setup_name=f"{strategy_tag} setup",
        entry_price=1.1000,
        quantity=10000,
        lot_size=1.0,
        leverage_used=10.0,
        stop_loss_at_entry=1.0950,
        target_at_entry=1.1120,
        entry_time=datetime(2026, 3, 14, entry_hour, 0, tzinfo=timezone.utc),
    )
    trade.close_trade(
        exit_price=1.1100,
        exit_time=datetime(2026, 3, 14, entry_hour, 30, tzinfo=timezone.utc),
        exit_reason="target",
    )
    return trade


class FinalBackendAuditFixTests(unittest.TestCase):
    def test_diagnosis_exposes_severity_distribution(self):
        diagnosis = AIDiagnosis(risk_tier="consistency")
        diagnosis.add_finding(
            DiagnosticFinding(
                category="time",
                title="Weak weekday cluster detected",
                description="Monday is weak.",
                severity="medium",
            )
        )
        diagnosis.add_finding(
            DiagnosticFinding(
                category="missed_opportunity",
                title="Profitable strategy opportunity gap",
                description="Breakout misses are high.",
                severity="high",
            )
        )

        distribution = diagnosis.severity_distribution()
        self.assertEqual(distribution["medium"], 1)
        self.assertEqual(distribution["high"], 1)
        self.assertEqual(distribution["critical"], 0)

    def test_coaching_engine_handles_behavior_category(self):
        diagnosis = AIDiagnosis(risk_tier="consistency")
        diagnosis.add_finding(
            DiagnosticFinding(
                category="behavior",
                title="Risk drift detected",
                description="Risk is trending up.",
                severity="medium",
                metric_reference="risk_drift",
            )
        )
        diagnosis.compute_health_score()

        prescription = CoachingEngine().generate_prescription(
            diagnosis=diagnosis,
            structured_metrics={},
            governance_tier="consistency",
        )

        instruction_types = [instruction.action_type for instruction in prescription.instructions]
        self.assertIn("behavioral_reinforcement", instruction_types)

    def test_behavioral_analyzer_detects_strategy_switch_frequency_from_trade_payload(self):
        context = Context()
        context.set_cache(
            "trades",
            [
                _trade_with_strategy("ACC-STRAT", "breakout", 9),
                _trade_with_strategy("ACC-STRAT", "fade", 10),
                _trade_with_strategy("ACC-STRAT", "fade", 11),
            ],
        )

        analysis = BehavioralAnalyzer().analyze(context=context)
        self.assertGreater(analysis["signals"]["strategy_switch_frequency"], 0.0)

    def test_behavioral_snapshot_does_not_mutate_shared_registry_context(self):
        original_trades = ["sentinel-trade"]
        original_sessions = ["sentinel-session"]
        original_missed = ["sentinel-missed"]
        api_registry.context.set_cache("trades", list(original_trades))
        api_registry.context.set_cache("trading_platform_sessions", list(original_sessions))
        api_registry.context.set_cache("missed_opportunities", list(original_missed))

        user = {"account_ids": ["ACC-SHARED"], "roles": ["user"]}
        original_trade_repo = api_registry.trade_repository
        original_session_repo = api_registry.trading_platform_session_repository
        original_missed_repo = api_registry.missed_opportunity_repository

        class _EmptyTradeRepo:
            def get_trades_by_account(self, account_id):
                return []

        class _EmptySessionRepo:
            def list_by_account(self, account_id):
                return []

        class _EmptyMissedRepo:
            def list_by_account(self, account_id):
                return []

        api_registry.trade_repository = _EmptyTradeRepo()
        api_registry.trading_platform_session_repository = _EmptySessionRepo()
        api_registry.missed_opportunity_repository = _EmptyMissedRepo()
        try:
            behavioral_snapshot(account_id="ACC-SHARED", lookback=None, user=user)
        finally:
            api_registry.trade_repository = original_trade_repo
            api_registry.trading_platform_session_repository = original_session_repo
            api_registry.missed_opportunity_repository = original_missed_repo

        self.assertEqual(api_registry.context.get_cache("trades"), original_trades)
        self.assertEqual(api_registry.context.get_cache("trading_platform_sessions"), original_sessions)
        self.assertEqual(api_registry.context.get_cache("missed_opportunities"), original_missed)


if __name__ == "__main__":
    unittest.main()
