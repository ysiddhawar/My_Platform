import numpy as np
from collections import defaultdict
from typing import List, Optional, Callable, Any
from core.execution_engine import ExecutionEngine
from core.registry import registry as default_registry


class StrategyEvaluator:
    """
    Platform-Ready Research Evaluator

    - Registry injected (no global)
    - Accepts full trade objects
    - Governance-compatible
    """

    def __init__(
        self,
        trades: List[dict],
        registry=None,
        use_net: bool = True,
        fail_fast: bool = False,
    ):

        self.trades = trades
        self.registry = registry or default_registry
        self.use_net = use_net
        self.engine = ExecutionEngine(fail_fast=fail_fast)

    # -------------------------------------------------
    # Helpers
    # -------------------------------------------------

    def _extract_returns(self, trades_subset):

        key = "net_pnl" if self.use_net else "gross_pnl"

        return np.array(
            [t.get(key, 0.0) for t in trades_subset],
            dtype=np.float64,
        )

    def _group_by_strategy(self):

        grouped = defaultdict(list)

        for trade in self.trades:
            strategy = trade.get("strategy", "UNKNOWN")
            grouped[strategy].append(trade)

        return grouped

    # -------------------------------------------------
    # Portfolio Evaluation
    # -------------------------------------------------

    def evaluate_portfolio(self, category: Optional[str] = None):

        returns = self._extract_returns(self.trades)

        if returns.size == 0:
            return {}

        context = self.engine.run(
            data={
                "returns": returns,
                "trades": self.trades,
            },
            registry=self.registry,
            category=category,
            phase="research",
            entity="portfolio",
        )

        return context.all_results()

    # -------------------------------------------------
    # Per Strategy Evaluation
    # -------------------------------------------------

    def evaluate_strategies(self, category: Optional[str] = None):

        grouped = self._group_by_strategy()
        results = {}

        for strategy_name, trades_subset in grouped.items():

            returns = self._extract_returns(trades_subset)

            if returns.size == 0:
                continue

            context = self.engine.run(
                data={
                    "returns": returns,
                    "trades": trades_subset,
                },
                registry=self.registry,
                category=category,
                phase="research",
                entity=strategy_name,
            )

            results[strategy_name] = context.all_results()

        return results

    # -------------------------------------------------
    # Full Evaluation
    # -------------------------------------------------

    def full_evaluation(self, category: Optional[str] = None):

        return {
            "portfolio": self.evaluate_portfolio(category),
            "strategies": self.evaluate_strategies(category),
        }


class Evaluator:
    """
    Minimal node evaluator used by replay/recovery components.
    """

    def evaluate_node(
        self,
        node: Callable[..., Any],
        context,
        payload: Optional[dict] = None,
    ):
        if not callable(node):
            raise TypeError("node must be callable")
        try:
            return node(context, payload)
        except TypeError:
            return node(context)
