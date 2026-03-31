from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from visualization.performance_dashboard import PerformanceDashboard
from visualization.portfolio_dashboard import PortfolioDashboard


router = APIRouter(prefix="/visualization", tags=["visualization"])


class PerformanceDashboardRequest(BaseModel):
    timestamps: List[Any]
    equity_curve: List[float]
    drawdown: List[float]
    rolling_sharpe: List[float]


class PortfolioDashboardRequest(BaseModel):
    timestamps: List[Any]
    portfolio_values: List[float]
    symbols: List[str]
    exposures: List[float]
    assets: List[str]
    correlation_matrix: List[List[float]]


class DashboardResponse(BaseModel):
    dashboard: Dict[str, Any]


class ChartCatalogResponse(BaseModel):
    charts: List[Dict[str, Any]]
    metric_groups: Dict[str, List[Dict[str, Any]]]
    top_widgets: List[Dict[str, Any]]
    group_visuals: Dict[str, List[Dict[str, Any]]]


class DashboardChartContractsRequest(BaseModel):
    account_id: str
    overview: Dict[str, Any]
    metrics: Dict[str, Any]
    filters: Dict[str, Any] = {}


class DashboardChartContractsResponse(BaseModel):
    groups: Dict[str, List[Dict[str, Any]]]


def _num(value: Any) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def _num_list(value: Any) -> List[float]:
    if not isinstance(value, list):
        return []
    output: List[float] = []
    for item in value:
        try:
            output.append(float(item))
        except Exception:
            continue
    return output


def _build_labeled_series(values: List[float], prefix: str, key: str) -> List[Dict[str, Any]]:
    return [{"label": f"{prefix}{index + 1}", key: value} for index, value in enumerate(values)]


def _extract_scalar(metric: Any) -> float:
    if isinstance(metric, (int, float)):
        return float(metric)
    if isinstance(metric, dict):
        for candidate in [
            "stability_score",
            "survival_score",
            "fragility_score",
            "ruin_probability",
            "max_safe_leverage",
            "capital_multiplier",
            "allocated_capital",
            "risk_amount",
            "model_size",
            "latest_volatility",
            "jarque_bera_score",
            "alpha",
            "threshold",
            "degrees_of_freedom",
            "fit_quality",
            "positive_sample_ratio",
            "average_correlation",
            "fragility_index",
            "systemic_fragility_score",
            "top_weight",
            "throttle_level",
            "worst_liquidity_drag",
            "stressed_correlation",
            "worst_case_drawdown",
            "tail_scenario_loss",
            "worst_regime_path",
            "max_spread",
            "impact_drag",
            "drawdown_p95",
            "capital_decay_rate",
            "recommended_fraction",
            "allocated_books",
        ]:
            if candidate in metric:
                return _num(metric[candidate])
        for value in metric.values():
            if isinstance(value, (int, float)):
                return float(value)
    return 0.0


@router.post("/performance-dashboard", response_model=DashboardResponse)
def build_performance_dashboard(request: PerformanceDashboardRequest):
    try:
        dashboard = PerformanceDashboard()
        dashboard.build_equity_curve(request.timestamps, request.equity_curve)
        dashboard.build_drawdown_curve(request.timestamps, request.drawdown)
        dashboard.build_rolling_sharpe(request.timestamps, request.rolling_sharpe)
        return DashboardResponse(dashboard=dashboard.export())
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/portfolio-dashboard", response_model=DashboardResponse)
def build_portfolio_dashboard(request: PortfolioDashboardRequest):
    try:
        dashboard = PortfolioDashboard()
        dashboard.build_portfolio_value_trend(request.timestamps, request.portfolio_values)
        dashboard.build_portfolio_exposure(request.symbols, request.exposures)
        dashboard.build_correlation_heatmap(request.assets, request.correlation_matrix)
        return DashboardResponse(dashboard=dashboard.export())
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/chart-catalog", response_model=ChartCatalogResponse)
def get_chart_catalog():
    charts = [
        {"chart_type": "bar", "best_for": ["comparisons", "rankings", "cost breakdowns"]},
        {"chart_type": "pie", "best_for": ["composition", "allocation", "win-loss share"]},
        {"chart_type": "radar", "best_for": ["multi-factor profiles", "robustness", "survival posture"]},
        {"chart_type": "timeseries", "best_for": ["equity", "rolling metrics", "trend over time"]},
        {"chart_type": "heatmap", "best_for": ["correlation matrices", "regime transitions", "time buckets"]},
        {"chart_type": "histogram", "best_for": ["return distribution", "tail behavior", "outlier density"]},
    ]
    metric_groups = {
        "Journal Metrics": [
            {"metric": "trade_count", "chart_type": "bar"},
            {"metric": "win_rate", "chart_type": "pie"},
            {"metric": "cost_summary", "chart_type": "bar"},
            {"metric": "adjusted_pnl", "chart_type": "timeseries"},
        ],
        "Performance Metrics": [
            {"metric": "equity_curve", "chart_type": "timeseries"},
            {"metric": "rolling_sharpe", "chart_type": "timeseries"},
            {"metric": "sharpe", "chart_type": "bar"},
        ],
        "Risk Metrics": [
            {"metric": "rolling_volatility", "chart_type": "timeseries"},
            {"metric": "rolling_drawdown", "chart_type": "timeseries"},
            {"metric": "value_at_risk", "chart_type": "bar"},
        ],
        "Distribution Metrics": [
            {"metric": "normality_test", "chart_type": "histogram"},
            {"metric": "skewness", "chart_type": "bar"},
            {"metric": "student_t_fit", "chart_type": "histogram"},
        ],
        "Regime Metrics": [
            {"metric": "regime_transition_matrix", "chart_type": "heatmap"},
            {"metric": "regime_breakdown", "chart_type": "bar"},
        ],
        "Portfolio Metrics": [
            {"metric": "correlation", "chart_type": "heatmap"},
            {"metric": "risk_contribution", "chart_type": "bar"},
            {"metric": "risk_parity", "chart_type": "pie"},
        ],
        "Stress Metrics": [
            {"metric": "stress_scenarios", "chart_type": "bar"},
            {"metric": "regime_path_generator", "chart_type": "timeseries"},
        ],
        "Survival Metrics": [
            {"metric": "survival_score", "chart_type": "radar"},
            {"metric": "risk_of_ruin", "chart_type": "bar"},
        ],
    }
    top_widgets = [
        {"key": "trades", "label": "Total Completed Trades", "helper": "All records in the current filtered view."},
        {"key": "net_pnl", "label": "Net Return $", "helper": "After all costs."},
        {"key": "win_rate", "label": "Wins Percent", "helper": "Closed trades only."},
        {"key": "platform_time", "label": "Platform Time", "helper": "Tracked session time."},
        {"key": "missed_opportunities", "label": "Missed Opportunities", "helper": "Recorded but unexecuted setups."},
        {"key": "expectancy", "label": "Expectancy", "helper": "Higher is better."},
        {"key": "profit_factor", "label": "Profit Factor", "helper": "Above 1 is healthier."},
        {"key": "avg_win", "label": "Avg Win", "helper": "Average profit on winning trades."},
        {"key": "avg_loss", "label": "Avg Loss", "helper": "Average loss on losing trades."},
        {"key": "avg_win_hold", "label": "Avg Win Hold", "helper": "Average time in winning trades."},
        {"key": "avg_loss_hold", "label": "Avg Loss Hold", "helper": "Average time in losing trades."},
        {"key": "top_win", "label": "Top Win", "helper": "Best closed trade."},
        {"key": "top_loss", "label": "Top Loss", "helper": "Worst closed trade."},
        {"key": "win_streak", "label": "Win Streak", "helper": "Longest consecutive wins."},
        {"key": "loss_streak", "label": "Loss Streak", "helper": "Longest consecutive losses."},
        {"key": "avg_daily_volume", "label": "Avg Daily Vol", "helper": "Average daily traded size."},
        {"key": "avg_size", "label": "Avg Size", "helper": "Average quantity per trade."},
        {"key": "pre_trade_coverage", "label": "Pre-Trade Coverage", "helper": "Trades with pre-trade capture."},
        {"key": "post_trade_coverage", "label": "Post-Trade Coverage", "helper": "Trades with post-trade capture."},
        {"key": "checklist_coverage", "label": "Checklist Coverage", "helper": "Trades with checklist selections."},
        {"key": "rule_violations", "label": "Rule Violations", "helper": "Tracked violations."},
        {"key": "probability_coverage", "label": "Probability Coverage", "helper": "Trades tagged with probability bucket."},
        {"key": "decision_readiness", "label": "Decision Readiness", "helper": "Trades with setup/strategy data."},
    ]
    group_visuals = {
        "Journal Metrics": [
            {"title": "Trade Distribution", "chart_type": "pie"},
            {"title": "Cost Breakdown", "chart_type": "bar"},
            {"title": "Net PnL Curve", "chart_type": "timeseries"},
        ],
        "Performance Metrics": [
            {"title": "Equity Curve", "chart_type": "timeseries"},
            {"title": "Rolling Sharpe", "chart_type": "timeseries"},
            {"title": "Outcome Mix", "chart_type": "pie"},
        ],
        "Risk Metrics": [
            {"title": "Volatility Curves", "chart_type": "timeseries"},
            {"title": "Drawdown Curve", "chart_type": "timeseries"},
            {"title": "Risk Shape", "chart_type": "radar"},
        ],
        "Distribution Metrics": [
            {"title": "Return Distribution", "chart_type": "histogram"},
            {"title": "Distribution Shape", "chart_type": "bar"},
        ],
        "Regime Metrics": [
            {"title": "Regime Distribution", "chart_type": "bar"},
            {"title": "Transition Heatmap", "chart_type": "heatmap"},
        ],
        "Portfolio Metrics": [
            {"title": "Correlation Heatmap", "chart_type": "heatmap"},
            {"title": "Portfolio Allocation", "chart_type": "pie"},
            {"title": "Risk Contribution", "chart_type": "bar"},
        ],
        "Stress Metrics": [
            {"title": "Stress Envelope", "chart_type": "bar"},
            {"title": "Stress Profile", "chart_type": "radar"},
        ],
        "Survival Metrics": [
            {"title": "Survival Profile", "chart_type": "radar"},
            {"title": "Survival Snapshot", "chart_type": "bar"},
        ],
    }
    return ChartCatalogResponse(charts=charts, metric_groups=metric_groups, top_widgets=top_widgets, group_visuals=group_visuals)


@router.post("/dashboard-contracts", response_model=DashboardChartContractsResponse)
def build_dashboard_contracts(request: DashboardChartContractsRequest):
    trades = request.overview.get("trades", []) if isinstance(request.overview, dict) else []
    metrics = request.metrics if isinstance(request.metrics, dict) else {}
    closed = [trade for trade in trades if trade.get("is_closed")]
    wins = [trade for trade in closed if _num(trade.get("net_pnl")) > 0]
    losses = [trade for trade in closed if _num(trade.get("net_pnl")) < 0]
    returns = [
        (_num(trade.get("net_pnl")) / 100000.0)
        for trade in closed
        if trade.get("net_pnl") is not None
    ]

    cost_summary = metrics.get("cost_summary", {}) if isinstance(metrics.get("cost_summary"), dict) else {}
    adjusted_pnl = metrics.get("adjusted_pnl", {}) if isinstance(metrics.get("adjusted_pnl"), dict) else {}
    equity_curve = metrics.get("equity_curve", []) if isinstance(metrics.get("equity_curve"), list) else []
    rolling_sharpe = _num_list(metrics.get("rolling_sharpe"))
    rolling_vol = _num_list(metrics.get("rolling_volatility"))
    adaptive_rolling_vol = _num_list((metrics.get("adaptive_rolling_volatility") or {}).get("series")) if isinstance(metrics.get("adaptive_rolling_volatility"), dict) else []
    rolling_drawdown = _num_list(metrics.get("rolling_drawdown"))
    regime_labeling = metrics.get("regime_labeling", {}) if isinstance(metrics.get("regime_labeling"), dict) else {}
    regime_matrix = (metrics.get("regime_transition_matrix") or {}).get("matrix", []) if isinstance(metrics.get("regime_transition_matrix"), dict) else []
    correlation = metrics.get("correlation", []) if isinstance(metrics.get("correlation"), list) else []

    strategy_count = int(_num((metrics.get("portfolio_preprocessor") or {}).get("strategy_count"))) if isinstance(metrics.get("portfolio_preprocessor"), dict) else 0
    labels = [f"Book {index + 1}" for index in range(max(strategy_count, len(correlation), 1))]
    equal_weight = round(1 / len(labels), 4) if labels else 1.0

    groups: Dict[str, List[Dict[str, Any]]] = {
        "Journal Metrics": [
            {
                "title": "Trade Distribution",
                "chart_type": "pie",
                "points": [
                    {"name": "Wins", "value": len(wins)},
                    {"name": "Losses", "value": len(losses)},
                    {"name": "Open", "value": max(0, len(trades) - len(closed))},
                ],
            },
            {
                "title": "Cost Breakdown",
                "chart_type": "bar",
                "points": [
                    {"metric": "Brokerage", "value": _num(cost_summary.get("total_brokerage"))},
                    {"metric": "Slippage", "value": _num(cost_summary.get("total_slippage"))},
                    {"metric": "Swaps", "value": _num(cost_summary.get("total_swaps"))},
                    {"metric": "Total Cost", "value": _num(cost_summary.get("total_cost"))},
                ],
            },
            {
                "title": "Net PnL Curve",
                "chart_type": "timeseries",
                "points": _build_labeled_series(_num_list(adjusted_pnl.get("cumulative_net_curve")), "T", "net"),
                "series": [{"key": "net", "color": "#0f766e", "name": "Cumulative Net"}],
            },
        ],
        "Performance Metrics": [
            {
                "title": "Equity Curve",
                "chart_type": "timeseries",
                "points": [
                    {"label": str(point.get("t", f"T{index + 1}")), "equity": _num(point.get("equity"))}
                    for index, point in enumerate(equity_curve)
                    if isinstance(point, dict)
                ],
                "series": [{"key": "equity", "color": "#1d4ed8", "name": "Equity"}],
            },
            {
                "title": "Rolling Sharpe",
                "chart_type": "timeseries",
                "points": _build_labeled_series(rolling_sharpe, "W", "rolling"),
                "series": [{"key": "rolling", "color": "#1d4ed8", "name": "Rolling Sharpe"}],
            },
            {
                "title": "Performance Snapshot",
                "chart_type": "bar",
                "points": [
                    {"metric": "Sharpe", "value": _extract_scalar(metrics.get("sharpe"))},
                    {"metric": "Sortino", "value": _extract_scalar(metrics.get("sortino"))},
                    {"metric": "Calmar", "value": _extract_scalar(metrics.get("calmar"))},
                    {"metric": "CAGR", "value": _extract_scalar(metrics.get("cagr"))},
                ],
            },
        ],
        "Risk Metrics": [
            {
                "title": "Volatility Curves",
                "chart_type": "timeseries",
                "points": [
                    {"label": f"W{index + 1}", "rolling": value, "adaptive": adaptive_rolling_vol[index] if index < len(adaptive_rolling_vol) else value}
                    for index, value in enumerate(rolling_vol)
                ],
                "series": [
                    {"key": "rolling", "color": "#0f766e", "name": "Rolling Volatility"},
                    {"key": "adaptive", "color": "#7c3aed", "name": "Adaptive Volatility"},
                ],
            },
            {
                "title": "Drawdown Curve",
                "chart_type": "timeseries",
                "points": _build_labeled_series(rolling_drawdown, "T", "drawdown"),
                "series": [{"key": "drawdown", "color": "#b91c1c", "name": "Rolling Drawdown"}],
            },
            {
                "title": "Risk Shape",
                "chart_type": "radar",
                "points": [
                    {"metric": "Volatility", "value": _extract_scalar(metrics.get("volatility"))},
                    {"metric": "Drawdown", "value": abs(_extract_scalar(metrics.get("max_drawdown")))},
                    {"metric": "Ulcer", "value": _extract_scalar(metrics.get("ulcer_index"))},
                    {"metric": "Downside", "value": _extract_scalar(metrics.get("downside_deviation"))},
                ],
            },
        ],
        "Distribution Metrics": [
            {"title": "Return Distribution", "chart_type": "histogram", "values": returns, "bins": 12},
            {
                "title": "Distribution Shape",
                "chart_type": "bar",
                "points": [
                    {"metric": "Skew", "value": _extract_scalar(metrics.get("skewness"))},
                    {"metric": "Kurtosis", "value": _extract_scalar(metrics.get("kurtosis"))},
                    {"metric": "Tail", "value": _extract_scalar(metrics.get("tail_ratio"))},
                    {"metric": "AutoCorr", "value": _extract_scalar(metrics.get("autocorrelation"))},
                ],
            },
        ],
        "Regime Metrics": [
            {
                "title": "Regime Distribution",
                "chart_type": "bar",
                "points": [
                    {"metric": "Low", "value": _num(regime_labeling.get("low_count"))},
                    {"metric": "Medium", "value": _num(regime_labeling.get("medium_count"))},
                    {"metric": "High", "value": _num(regime_labeling.get("high_count"))},
                    {"metric": "Switches", "value": _num((metrics.get("regime_switching") or {}).get("regime_changes")) if isinstance(metrics.get("regime_switching"), dict) else 0},
                ],
            },
            {
                "title": "Transition Heatmap",
                "chart_type": "heatmap",
                "labels_x": ["LOW", "MEDIUM", "HIGH"],
                "labels_y": ["LOW", "MEDIUM", "HIGH"],
                "matrix": regime_matrix or [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
            },
        ],
        "Robustness Metrics": [
            {
                "title": "Robustness Scores",
                "chart_type": "bar",
                "points": [
                    {"metric": "Walk Fwd", "value": _extract_scalar(metrics.get("walk_forward"))},
                    {"metric": "Bootstrap", "value": _extract_scalar(metrics.get("bootstrap"))},
                    {"metric": "Noise", "value": _extract_scalar(metrics.get("noise_stability"))},
                    {"metric": "Stability", "value": _extract_scalar(metrics.get("stability_score"))},
                ],
            },
            {
                "title": "Robustness Profile",
                "chart_type": "radar",
                "points": [
                    {"metric": "Walk Fwd", "value": _extract_scalar(metrics.get("walk_forward"))},
                    {"metric": "Param", "value": _extract_scalar(metrics.get("parameter_sensitivity"))},
                    {"metric": "Noise", "value": _extract_scalar(metrics.get("noise_stability"))},
                    {"metric": "Regime", "value": _extract_scalar(metrics.get("regime_stability"))},
                    {"metric": "Monte Carlo", "value": _extract_scalar(metrics.get("monte_carlo_stability"))},
                ],
            },
        ],
        "Portfolio Metrics": [
            {
                "title": "Correlation Heatmap",
                "chart_type": "heatmap",
                "labels_x": labels,
                "labels_y": labels,
                "matrix": correlation or [[1.0]],
            },
            {
                "title": "Portfolio Allocation",
                "chart_type": "pie",
                "points": [{"name": label, "value": equal_weight} for label in labels],
            },
            {
                "title": "Portfolio Health",
                "chart_type": "bar",
                "points": [
                    {"metric": "Variance", "value": _extract_scalar(metrics.get("portfolio_variance"))},
                    {"metric": "Div Ratio", "value": _extract_scalar(metrics.get("diversification_ratio"))},
                    {"metric": "Eff Bets", "value": _extract_scalar(metrics.get("effective_number_of_bets"))},
                    {"metric": "Fragility", "value": _extract_scalar(metrics.get("portfolio_fragility_index"))},
                ],
            },
        ],
        "Capital Metrics": [
            {
                "title": "Capital Deployment",
                "chart_type": "bar",
                "points": [
                    {"metric": "Risk Budget", "value": _extract_scalar(metrics.get("risk_budgeting"))},
                    {"metric": "Kelly", "value": _extract_scalar(metrics.get("kelly"))},
                    {"metric": "Pos Size", "value": _extract_scalar(metrics.get("position_sizer"))},
                    {"metric": "Allocated", "value": _extract_scalar(metrics.get("capital_engine"))},
                ],
            },
            {
                "title": "Capital Profile",
                "chart_type": "radar",
                "points": [
                    {"metric": "Risk Budget", "value": _extract_scalar(metrics.get("risk_budgeting"))},
                    {"metric": "Kelly", "value": _extract_scalar(metrics.get("kelly"))},
                    {"metric": "Position", "value": _extract_scalar(metrics.get("position_sizer"))},
                    {"metric": "Engine", "value": _extract_scalar(metrics.get("capital_engine"))},
                ],
            },
        ],
        "Risk Control Metrics": [
            {
                "title": "Control Layer",
                "chart_type": "bar",
                "points": [
                    {"metric": "Kill Switch", "value": _extract_scalar(metrics.get("kill_switch"))},
                    {"metric": "Throttle", "value": _extract_scalar(metrics.get("dynamic_throttle"))},
                    {"metric": "Capital Mult", "value": _extract_scalar(metrics.get("capital_throttle_engine"))},
                ],
            },
            {
                "title": "Control Profile",
                "chart_type": "radar",
                "points": [
                    {"metric": "Kill", "value": _extract_scalar(metrics.get("kill_switch"))},
                    {"metric": "Throttle", "value": _extract_scalar(metrics.get("dynamic_throttle"))},
                    {"metric": "Capital", "value": _extract_scalar(metrics.get("capital_throttle_engine"))},
                ],
            },
        ],
        "Stress Metrics": [
            {
                "title": "Stress Envelope",
                "chart_type": "bar",
                "points": [
                    {"metric": "Base DD", "value": abs(_num((metrics.get("stress_engine") or {}).get("base_drawdown"))) if isinstance(metrics.get("stress_engine"), dict) else 0},
                    {"metric": "Impact DD", "value": abs(_num((metrics.get("stress_engine") or {}).get("execution_impact_dd"))) if isinstance(metrics.get("stress_engine"), dict) else 0},
                    {"metric": "Worst DD", "value": abs(_num((metrics.get("stress_engine") or {}).get("worst_case_dd"))) if isinstance(metrics.get("stress_engine"), dict) else 0},
                    {"metric": "Liq Shock", "value": _extract_scalar(metrics.get("liquidity_shock"))},
                ],
            },
            {
                "title": "Stress Profile",
                "chart_type": "radar",
                "points": [
                    {"metric": "Vol Spike", "value": _extract_scalar(metrics.get("volatility_spike"))},
                    {"metric": "Liquidity", "value": _extract_scalar(metrics.get("liquidity_shock"))},
                    {"metric": "Corr Spike", "value": _extract_scalar(metrics.get("correlation_spike"))},
                    {"metric": "Crash", "value": _extract_scalar(metrics.get("crash_simulation"))},
                ],
            },
        ],
        "Survival Metrics": [
            {
                "title": "Survival Layer",
                "chart_type": "bar",
                "points": [
                    {"metric": "Survival", "value": _extract_scalar(metrics.get("survival_score"))},
                    {"metric": "Ruin", "value": _extract_scalar(metrics.get("risk_of_ruin"))},
                    {"metric": "Leverage", "value": _extract_scalar(metrics.get("deployable_leverage"))},
                    {"metric": "Fragility", "value": _extract_scalar(metrics.get("fragility_score"))},
                ],
            },
            {
                "title": "Survival Profile",
                "chart_type": "radar",
                "points": [
                    {"metric": "Survival", "value": _extract_scalar(metrics.get("survival_score"))},
                    {"metric": "Ruin", "value": _extract_scalar(metrics.get("risk_of_ruin"))},
                    {"metric": "Leverage", "value": _extract_scalar(metrics.get("deployable_leverage"))},
                    {"metric": "Fragility", "value": _extract_scalar(metrics.get("fragility_score"))},
                ],
            },
        ],
    }
    return DashboardChartContractsResponse(groups=groups)
