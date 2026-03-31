import unittest

from load_metrics import load_all
from core.execution_engine import ExecutionEngine
from core.registry import registry
from core.evaluator import StrategyEvaluator


class SmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        load_all()

    def test_registry_validates(self):
        registry.validate()

    def test_engine_runs_performance_category(self):
        import numpy as np

        engine = ExecutionEngine(fail_fast=False)
        returns = np.random.default_rng(42).normal(0.001, 0.02, 300)
        context = engine.run(
            data={"returns": returns},
            category="performance",
            registry=registry,
        )
        self.assertIsInstance(context.all_results(), dict)
        self.assertIsInstance(context.get_errors(), dict)
        self.assertIsNotNone(context.get_result("net_cagr"))
        self.assertIsNotNone(context.get_result("net_sortino"))
        self.assertIsNotNone(context.get_result("net_sharpe"))

    def test_strategy_evaluator_runs(self):
        trades = [
            {"strategy": "alpha", "net_pnl": 100.0, "gross_pnl": 110.0},
            {"strategy": "alpha", "net_pnl": -20.0, "gross_pnl": -18.0},
            {"strategy": "beta", "net_pnl": 50.0, "gross_pnl": 55.0},
            {"strategy": "beta", "net_pnl": 10.0, "gross_pnl": 11.0},
        ]

        evaluator = StrategyEvaluator(trades=trades, use_net=True, fail_fast=False)
        result = evaluator.full_evaluation(category="performance")

        self.assertIn("portfolio", result)
        self.assertIn("strategies", result)
        self.assertIsInstance(result["portfolio"], dict)
        self.assertIsInstance(result["strategies"], dict)

    def test_capital_metrics_non_none_with_strategies(self):
        import numpy as np

        rng = np.random.default_rng(7)
        strategies = {
            "alpha": rng.normal(0.001, 0.02, 600),
            "beta": rng.normal(0.0008, 0.018, 600),
            "gamma": rng.normal(0.0012, 0.022, 600),
        }
        engine = ExecutionEngine(fail_fast=False)
        context = engine.run(
            data={
                "strategies": strategies,
                "capital": 1_000_000,
                "total_capital": 1_000_000,
                "fractional_kelly": 0.5,
                "risk_per_trade": 0.01,
                "entry_price": 100,
                "stop_price": 98,
            },
            category="capital",
            registry=registry,
        )

        self.assertIsNotNone(context.get_result("risk_budgeting"))
        self.assertIsNotNone(context.get_result("kelly"))
        self.assertIsNotNone(context.get_result("capital_engine"))
        self.assertIsNotNone(context.get_result("position_sizer"))

    def test_portfolio_rejects_nested_strategy_payload(self):
        engine = ExecutionEngine(fail_fast=False)
        context = engine.run(
            data={
                "strategies": {
                    "alpha": {"returns": [0.01, -0.02, 0.03]},
                }
            },
            category="portfolio",
            registry=registry,
        )
        self.assertIsNone(context.get_result("portfolio_preprocessor"))
        self.assertIn("portfolio_preprocessor", context.get_errors())

    def test_stress_engine_runs_with_spread_matrix(self):
        import numpy as np

        rng = np.random.default_rng(21)
        t = 700
        strategies = {
            "alpha": rng.normal(0.001, 0.02, t),
            "beta": rng.normal(0.0008, 0.018, t),
            "gamma": rng.normal(0.0012, 0.022, t),
        }
        spread_matrix = np.abs(
            rng.normal(0.0001, 0.00005, size=(len(strategies), t))
        )

        engine = ExecutionEngine(fail_fast=False)
        context = engine.run(
            data={
                "strategies": strategies,
                "spread_matrix": spread_matrix,
                "capital": 1_000_000,
                "total_capital": 1_000_000,
            },
            category="stress",
            registry=registry,
        )

        self.assertIsNone(context.get_errors().get("stress_engine"))
        stress = context.get_result("stress_engine")
        self.assertIsInstance(stress, dict)
        self.assertIn("worst_case_dd", stress)

    def test_survival_engine_runs(self):
        import numpy as np

        rng = np.random.default_rng(33)
        t = 700
        strategies = {
            "alpha": rng.normal(0.001, 0.02, t),
            "beta": rng.normal(0.0008, 0.018, t),
            "gamma": rng.normal(0.0012, 0.022, t),
        }
        spread_matrix = np.abs(
            rng.normal(0.0001, 0.00005, size=(len(strategies), t))
        )

        engine = ExecutionEngine(fail_fast=False)
        context = engine.run(
            data={
                "strategies": strategies,
                "spread_matrix": spread_matrix,
                "capital": 1_000_000,
                "total_capital": 1_000_000,
            },
            category="survival",
            registry=registry,
        )

        self.assertIsNone(context.get_errors().get("survival_engine"))
        survival = context.get_result("survival_engine")
        self.assertIsInstance(survival, dict)
        self.assertIn("deployable_survival_score", survival)


if __name__ == "__main__":
    unittest.main()