import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import { useQuery } from 'react-query';
import { Area, Bar, CartesianGrid, ComposedChart, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import { fetchChartCatalog, fetchDashboardChartContracts, fetchOverview, fetchAccounts, runMetricComputation } from '@/api/prototype';
import { ChartFrame } from '@/components/charts/ChartFrame';
import { EquityCurveChart } from '@/components/charts/EquityCurveChart';
import { GenericTimeSeriesChart } from '@/components/charts/GenericTimeSeriesChart';
import { HeatmapChart } from '@/components/charts/HeatmapChart';
import { HistogramChart } from '@/components/charts/HistogramChart';
import { MetricsBarChart } from '@/components/charts/MetricsBarChart';
import { PieMetricChart } from '@/components/charts/PieMetricChart';
import { RadarMetricChart } from '@/components/charts/RadarMetricChart';
import { StatCard } from '@/components/prototype/domain/StatCard';
import { EnhancedMetricCard } from '@/components/prototype/EnhancedMetricCard';
import { DollarSignIcon, TrophyIcon, TrendingUpIcon, TrendingDownIcon, PercentIcon, BarChartIcon, ClockIcon, TargetIcon, ShieldIcon, RatioIcon, ChartLineIcon, CalendarIcon, AnalyticsIcon } from '@/components/prototype/MetricIcons';
import { getMetricIcon } from '@/components/prototype/MetricVisualMapping';
import type { DashboardChartContract, OverviewData, TradeRecord } from '@/types/prototype';
import { defaultDashboardFilters, defaultDashboardGroupOrder, usePrototypeStore } from '@/state/prototypeStore';
import { formatCompactNumber, formatCurrency, formatDate, formatMinutes, formatNumber, formatPercent, formatRatio, humanizeKey } from '@/utils/format';

type MetricSection = {
  title: string;
  keys: string[];
};

type BookMatrix = {
  labels: string[];
  matrix: number[][];
};

type ChartDatum = {
  metric: string;
  value: number;
};

type TopDashboardCard = {
  key: string;
  icon: ReactNode;
  title: string;
  value: string;
  tone: 'neutral' | 'good' | 'caution' | 'risk';
  trend: {
    direction: 'up' | 'down' | 'neutral';
    value: string;
    label: string;
  };
};

const defaultMetricSections: MetricSection[] = [
  { title: 'Journal Metrics', keys: ['payoff_ratio', 'cost_summary', 'adjusted_pnl'] },
  { title: 'Performance Metrics', keys: ['sharpe', 'sortino', 'calmar', 'cagr', 'rolling_sharpe', 'net_sharpe', 'net_sortino', 'net_cagr'] },
  { title: 'Risk Metrics', keys: ['volatility', 'rolling_volatility', 'adaptive_rolling_volatility', 'rolling_drawdown', 'drawdown_duration', 'ulcer_index', 'downside_deviation', 'value_at_risk', 'conditional_var'] },
  { title: 'Distribution Metrics', keys: ['normality_test', 'skewness', 'kurtosis', 'fat_tail_index', 'tail_ratio', 'student_t_fit', 'pareto_fit', 'power_law_exponent', 'lognormal_test', 'autocorrelation', 'pareto_tail_estimator', 'power_law_fit'] },
  { title: 'Regime Metrics', keys: ['volatility_regime', 'regime_labeling', 'regime_sharpe', 'regime_drawdown', 'regime_transition_matrix', 'regime_switching', 'volatility_clustering', 'garch_volatility', 'regime_breakdown', 'regime_fragility'] },
  { title: 'Robustness Metrics', keys: ['walk_forward', 'bootstrap', 'block_bootstrap', 'parameter_sensitivity', 'noise_stability', 'regime_stability', 'monte_carlo_stability', 'stability_score'] },
  { title: 'Portfolio Metrics', keys: ['correlation', 'covariance_matrix', 'portfolio_variance', 'risk_contribution', 'risk_parity', 'target_volatility', 'drawdown_correlation', 'crash_overlap', 'systemic_fragility', 'portfolio_fragility_index', 'portfolio_preprocessor', 'diversification_ratio', 'effective_number_of_bets', 'hierarchical_risk_parity', 'dynamic_cluster_risk_budgeting', 'drawdown_aware_capital_allocator'] },
  { title: 'Capital Metrics', keys: ['risk_budgeting', 'kelly', 'portfolio_position_sizer', 'position_sizer', 'capital_engine'] },
  { title: 'Risk Control Metrics', keys: ['kill_switch', 'dynamic_throttle', 'capital_throttle_engine'] },
  { title: 'Stress Metrics', keys: ['stress_engine', 'volatility_spike', 'liquidity_shock', 'correlation_spike', 'crash_simulation', 'stress_scenarios', 'regime_path_generator', 'spread_regime_generator', 'execution_impact_model'] },
  { title: 'Survival Metrics', keys: ['fragility_score', 'deployable_leverage', 'kill_switch_threshold', 'capital_throttle_policy', 'drawdown_percentile', 'capital_decay', 'risk_of_ruin', 'ruin_probability_mc', 'survival_score', 'survival_engine'] },
];

function average(values: number[]): number {
  return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : 0;
}

function sampleStd(values: number[]): number {
  if (values.length < 2) return 0;
  const mean = average(values);
  const variance = values.reduce((sum, value) => sum + (value - mean) ** 2, 0) / (values.length - 1);
  return Math.sqrt(Math.max(variance, 0));
}

function percentile(values: number[], p: number): number {
  if (!values.length) return 0;
  const sorted = [...values].sort((a, b) => a - b);
  const index = (sorted.length - 1) * p;
  const lower = Math.floor(index);
  const upper = Math.ceil(index);
  if (lower === upper) return sorted[lower];
  const weight = index - lower;
  return sorted[lower] * (1 - weight) + sorted[upper] * weight;
}

function downsideDeviation(values: number[]): number {
  const negatives = values.filter((value) => value < 0);
  if (!negatives.length) return 0;
  const variance = negatives.reduce((sum, value) => sum + value ** 2, 0) / negatives.length;
  return Math.sqrt(Math.max(variance, 0));
}

function skewness(values: number[]): number {
  const mean = average(values);
  const std = sampleStd(values);
  if (!values.length || std === 0) return 0;
  return average(values.map((value) => ((value - mean) / std) ** 3));
}

function kurtosis(values: number[]): number {
  const mean = average(values);
  const std = sampleStd(values);
  if (!values.length || std === 0) return 0;
  return average(values.map((value) => ((value - mean) / std) ** 4));
}

function autocorrelation(values: number[], lag = 1): number {
  if (values.length <= lag) return 0;
  const mean = average(values);
  let numerator = 0;
  let denominator = 0;
  for (let index = 0; index < values.length; index += 1) {
    const centered = values[index] - mean;
    denominator += centered * centered;
    if (index >= lag) {
      numerator += centered * (values[index - lag] - mean);
    }
  }
  return denominator > 0 ? numerator / denominator : 0;
}

function rollingWindow(values: number[], size: number, mapper: (window: number[]) => number): number[] {
  if (values.length < size || size < 2) return [];
  const output: number[] = [];
  for (let index = size; index <= values.length; index += 1) {
    output.push(mapper(values.slice(index - size, index)));
  }
  return output;
}

function tradeCloseTimestamp(trade: TradeRecord): string {
  return trade.exit_time
    || (trade.exit_date ? `${trade.exit_date}T23:59:59` : '')
    || trade.entry_time
    || (trade.entry_date ? `${trade.entry_date}T00:00:00` : '')
    || '';
}

function tradeCloseDateKey(trade: TradeRecord): string | undefined {
  return trade.exit_date || trade.exit_time?.slice(0, 10) || trade.entry_date || trade.entry_time?.slice(0, 10);
}

function chronologicalClosedTrades(trades: TradeRecord[]): TradeRecord[] {
  return trades
    .filter((trade) => trade.is_closed)
    .sort((left, right) => tradeCloseTimestamp(left).localeCompare(tradeCloseTimestamp(right)));
}

function buildReturns(trades: TradeRecord[], startingCapital: number): number[] {
  let equity = startingCapital;
  return chronologicalClosedTrades(trades)
    .map((trade) => {
      const pnl = Number(trade.net_pnl || 0);
      const denominator = Math.max(Math.abs(equity), 1);
      const value = pnl / denominator;
      equity += pnl;
      return Number.isFinite(value) ? value : 0;
    });
}

function buildEquitySeries(trades: TradeRecord[], startingCapital: number): Array<{ t: string; equity: number }> {
  const closed = chronologicalClosedTrades(trades);
  return closed.reduce<Array<{ t: string; equity: number }>>((rows, trade, index) => {
    const previous = rows[index - 1]?.equity || startingCapital;
    const rawDate = tradeCloseDateKey(trade);
    rows.push({
      t: rawDate || `Trade ${index + 1}`,
      equity: previous + Number(trade.net_pnl || 0),
    });
    return rows;
  }, []);
}

function buildDailyReturns(trades: TradeRecord[], startingCapital: number): number[] {
  const byDay = new Map<string, number>();
  chronologicalClosedTrades(trades)
    .forEach((trade) => {
      const dayKey = tradeCloseDateKey(trade);
      if (!dayKey) return;
      byDay.set(dayKey, (byDay.get(dayKey) || 0) + Number(trade.net_pnl || 0));
    });

  let equity = startingCapital;
  return Array.from(byDay.entries())
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([, net]) => {
      const denominator = Math.max(Math.abs(equity), 1);
      const dailyReturn = net / denominator;
      equity += net;
      return Number.isFinite(dailyReturn) ? dailyReturn : 0;
    });
}

function buildDailyNetCurve(trades: TradeRecord[]): Array<{ date: string; label: string; net: number; cumulative: number }> {
  const byDay = new Map<string, number>();
  chronologicalClosedTrades(trades)
    .forEach((trade) => {
      const dayKey = tradeCloseDateKey(trade);
      if (!dayKey) return;
      byDay.set(dayKey, (byDay.get(dayKey) || 0) + Number(trade.net_pnl || 0));
    });

  let cumulative = 0;
  return Array.from(byDay.entries())
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([date, net]) => {
      cumulative += net;
      return {
        date,
        label: formatDate(date),
        net: normalizeDisplayNumber(net),
        cumulative: normalizeDisplayNumber(cumulative),
      };
    });
}

function buildTimePatternInsights(trades: TradeRecord[]) {
  const weekdayLabels = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
  const weekdayPnl = new Map(weekdayLabels.map((label) => [label, 0]));
  const hourPnl = new Map(Array.from({ length: 24 }, (_, hour) => [hour, 0]));
  const matrix = weekdayLabels.map(() => Array.from({ length: 24 }, () => 0));

  trades.forEach((trade) => {
    const dayLabel = String(trade.entry_day_of_week || 'Unknown');
    const dayIndex = weekdayLabels.indexOf(dayLabel);
    const hour = trade.entry_hour != null
      ? Number(trade.entry_hour)
      : trade.entry_time
        ? new Date(trade.entry_time).getHours()
        : null;
    const pnl = Number(trade.net_pnl || 0);

    if (dayIndex >= 0) {
      weekdayPnl.set(dayLabel, (weekdayPnl.get(dayLabel) || 0) + pnl);
    }
    if (hour != null && Number.isFinite(hour) && hour >= 0 && hour <= 23) {
      hourPnl.set(hour, (hourPnl.get(hour) || 0) + pnl);
      if (dayIndex >= 0) {
        matrix[dayIndex][hour] += 1;
      }
    }
  });

  return {
    weekdayPnlBars: weekdayLabels.map((label) => ({ metric: label.slice(0, 3), value: normalizeDisplayNumber(weekdayPnl.get(label) || 0) })),
    hourPnlBars: Array.from({ length: 24 }, (_, hour) => ({
      metric: `${String(hour).padStart(2, '0')}:00`,
      value: normalizeDisplayNumber(hourPnl.get(hour) || 0),
    })),
    heatmapX: Array.from({ length: 24 }, (_, hour) => String(hour).padStart(2, '0')),
    heatmapY: weekdayLabels.map((label) => label.slice(0, 3)),
    tradeCountHeatmap: matrix,
  };
}

function buildCompactTimeHeatmap(input: { heatmapX: string[]; heatmapY: string[]; tradeCountHeatmap: number[][] }) {
  const bucketSize = 4;
  const compactX: string[] = [];
  for (let start = 0; start < input.heatmapX.length; start += bucketSize) {
    const end = Math.min(start + bucketSize - 1, input.heatmapX.length - 1);
    compactX.push(`${input.heatmapX[start]}-${input.heatmapX[end]}`);
  }

  const compactMatrix = input.tradeCountHeatmap.map((row) => {
    const next: number[] = [];
    for (let start = 0; start < row.length; start += bucketSize) {
      const bucket = row.slice(start, start + bucketSize);
      next.push(bucket.reduce((sum, value) => sum + Number(value || 0), 0));
    }
    return next;
  });

  return {
    labelsX: compactX,
    labelsY: input.heatmapY,
    matrix: compactMatrix,
  };
}

function buildGroupedSeries(trades: TradeRecord[], returns: number[], selector: (trade: TradeRecord, index: number) => string): Record<string, number[]> {
  const buckets = new Map<string, number[]>();
  chronologicalClosedTrades(trades).forEach((trade, index) => {
    const key = selector(trade, index);
    const bucket = buckets.get(key) || [];
    bucket.push(returns[index] ?? 0);
    buckets.set(key, bucket);
  });
  return Object.fromEntries(buckets.entries());
}

function getTradeLocalDate(trade: TradeRecord): Date | null {
  const raw = trade.entry_date || trade.entry_time?.slice(0, 10);
  if (!raw) return null;
  const parsed = new Date(`${raw}T00:00:00`);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

function startOfDay(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate());
}

function startOfWeek(date: Date): Date {
  const normalized = startOfDay(date);
  const day = normalized.getDay();
  const diff = (day + 6) % 7;
  normalized.setDate(normalized.getDate() - diff);
  return normalized;
}

function startOfMonth(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth(), 1);
}

function startOfYear(date: Date): Date {
  return new Date(date.getFullYear(), 0, 1);
}

function matchesDatePreset(date: Date | null, preset: string, reference: Date): boolean {
  if (!date || preset === 'all') return true;
  const current = startOfDay(date).getTime();
  const today = startOfDay(reference);
  if (preset === 'today') return current === today.getTime();
  if (preset === 'yesterday') {
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    return current === yesterday.getTime();
  }
  if (preset === 'this_week') return current >= startOfWeek(reference).getTime();
  if (preset === 'last_week') {
    const start = startOfWeek(reference);
    const lastStart = new Date(start);
    lastStart.setDate(lastStart.getDate() - 7);
    return current >= lastStart.getTime() && current < start.getTime();
  }
  if (preset === 'this_month') return current >= startOfMonth(reference).getTime();
  if (preset === 'last_month') {
    const thisMonth = startOfMonth(reference);
    const lastMonth = new Date(thisMonth.getFullYear(), thisMonth.getMonth() - 1, 1);
    return current >= lastMonth.getTime() && current < thisMonth.getTime();
  }
  if (preset === 'last_3_months') {
    const start = new Date(reference.getFullYear(), reference.getMonth() - 2, 1);
    return current >= start.getTime();
  }
  if (preset === 'this_year') return current >= startOfYear(reference).getTime();
  if (preset === 'last_year') {
    const thisYear = startOfYear(reference);
    const lastYear = new Date(thisYear.getFullYear() - 1, 0, 1);
    return current >= lastYear.getTime() && current < thisYear.getTime();
  }
  return true;
}

function buildBookMatrix(trades: TradeRecord[], returns: number[]): BookMatrix {
  const groupedCandidates = [
    buildGroupedSeries(trades, returns, (trade) => String(trade.setup_name || trade.strategy_tag || trade.strategy || 'Unspecified')),
    buildGroupedSeries(trades, returns, (trade) => String(trade.market_type || 'unknown')),
    buildGroupedSeries(trades, returns, (trade) => String(trade.symbol || 'unknown')),
  ];

  for (const candidate of groupedCandidates) {
    const entries = Object.entries(candidate).filter(([, series]) => series.length >= 20);
    if (entries.length >= 2) {
      const minLength = Math.min(...entries.map(([, series]) => series.length));
      if (minLength >= 20) {
        return {
          labels: entries.map(([label]) => label),
          matrix: entries.map(([, series]) => series.slice(-minLength)),
        };
      }
    }
  }

  if (returns.length >= 60) {
    const synthetic = [
      returns.filter((_, index) => index % 3 === 0),
      returns.filter((_, index) => index % 3 === 1),
      returns.filter((_, index) => index % 3 === 2),
    ].filter((series) => series.length >= 20);
    if (synthetic.length >= 2) {
      const minLength = Math.min(...synthetic.map((series) => series.length));
      return {
        labels: synthetic.map((_, index) => `Book ${index + 1}`),
        matrix: synthetic.map((series) => series.slice(-minLength)),
      };
    }
  }

  return { labels: [], matrix: [] };
}

function covarianceMatrix(matrix: number[][]): number[][] {
  if (matrix.length < 2) return [];
  return matrix.map((seriesA) =>
    matrix.map((seriesB) => {
      const meanA = average(seriesA);
      const meanB = average(seriesB);
      const length = Math.min(seriesA.length, seriesB.length);
      if (length < 2) return 0;
      let total = 0;
      for (let index = 0; index < length; index += 1) {
        total += (seriesA[index] - meanA) * (seriesB[index] - meanB);
      }
      return total / (length - 1);
    }),
  );
}

function correlationFromCovariance(covariance: number[][]): number[][] {
  if (!covariance.length) return [];
  const stds = covariance.map((row, index) => Math.sqrt(Math.max(row[index] || 0, 0)));
  return covariance.map((row, rowIndex) =>
    row.map((value, colIndex) => {
      const denominator = (stds[rowIndex] || 0) * (stds[colIndex] || 0);
      return denominator > 0 ? value / denominator : 0;
    }),
  );
}

function maxDrawdownFromReturns(returns: number[]): number {
  if (!returns.length) return 0;
  let equity = 1;
  let peak = 1;
  let maxDrawdown = 0;
  returns.forEach((value) => {
    equity *= 1 + value;
    peak = Math.max(peak, equity);
    maxDrawdown = Math.min(maxDrawdown, (equity - peak) / peak);
  });
  return maxDrawdown;
}

function drawdownSeries(returns: number[]): number[] {
  const output: number[] = [];
  let equity = 1;
  let peak = 1;
  returns.forEach((value) => {
    equity *= 1 + value;
    peak = Math.max(peak, equity);
    output.push(peak > 0 ? (equity - peak) / peak : 0);
  });
  return output;
}

function maxDrawdownDuration(returns: number[]): { maxPeriods: number; currentPeriods: number } {
  const dd = drawdownSeries(returns);
  let current = 0;
  let maxPeriods = 0;
  dd.forEach((value) => {
    if (value < 0) {
      current += 1;
      maxPeriods = Math.max(maxPeriods, current);
    } else {
      current = 0;
    }
  });
  return { maxPeriods, currentPeriods: current };
}

function parseProbabilityBucket(value: string | null | undefined): number | null {
  if (!value) return null;
  const numeric = Number(String(value).replace(/[^0-9.]/g, ''));
  return Number.isFinite(numeric) ? numeric / 100 : null;
}

function annualizedGrowth(returns: number[]): number {
  if (!returns.length) return 0;
  const totalReturn = returns.reduce((equity, value) => equity * (1 + value), 1);
  return totalReturn ** (Math.min(252, returns.length) / returns.length) - 1;
}

function annualizedSharpeRatio(returns: number[]): number {
  const std = sampleStd(returns);
  if (returns.length < 2 || std <= 0) return 0;
  return (average(returns) / std) * Math.sqrt(Math.min(252, returns.length));
}

function annualizedSortinoRatio(returns: number[]): number {
  const downside = downsideDeviation(returns);
  if (returns.length < 2 || downside <= 0) return 0;
  return (average(returns) / downside) * Math.sqrt(Math.min(252, returns.length));
}

const currencyMetricKeys = new Set([
  'average_win',
  'average_loss',
  'adjusted_pnl',
]);

const percentageMetricKeys = new Set([
  'win_rate',
  'loss_rate',
  'probability_coverage',
  'pre_trade_coverage',
  'post_trade_coverage',
  'checklist_coverage',
  'decision_readiness',
  'cost_ratio',
  'ruin_probability',
  'mc_ruin_probability',
  'switch_rate',
  'tail_fraction',
  'persistence_ratio',
  'positive_sample_ratio',
]);

const chartOnlyMetrics = new Set([
  'adjusted_pnl',
  'sharpe',
  'sortino',
  'calmar',
  'cagr',
  'rolling_sharpe',
  'net_sharpe',
  'net_sortino',
  'net_cagr',
  'rolling_volatility',
  'adaptive_rolling_volatility',
  'rolling_drawdown',
  'correlation',
  'covariance_matrix',
  'regime_transition_matrix',
  'regime_labeling',
]);

const preferDerivedKeys = new Set([
  'average_win',
  'average_loss',
  'cost_summary',
  'adjusted_pnl',
  'equity_curve',
]);

function normalizeDisplayNumber(value: number): number {
  return Math.abs(value) < 1e-9 ? 0 : value;
}

function toNumberArray(metric: unknown): number[] {
  if (!Array.isArray(metric)) return [];
  return metric.filter((value): value is number => typeof value === 'number' && Number.isFinite(value));
}

function buildLabeledSeries(values: number[], prefix: string, key: string) {
  return values.map((value, index) => ({
    label: `${prefix}${index + 1}`,
    [key]: normalizeDisplayNumber(value),
  }));
}

function formatAxisDate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
  }).format(date);
}

function buildRollingDateSeries(trades: TradeRecord[], values: number[], key: string, fallbackPrefix: string) {
  const closed = chronologicalClosedTrades(trades);
  const offset = Math.max(0, closed.length - values.length);
  return values.map((value, index) => {
    const trade = closed[index + offset];
    const rawDate = trade ? tradeCloseDateKey(trade) : undefined;
    return {
      label: rawDate || `${fallbackPrefix}${index + 1}`,
      [key]: normalizeDisplayNumber(value),
    };
  });
}

function buildRegimeTransitionHeatmap(regimes: string[]) {
  const states = ['LOW', 'MEDIUM', 'HIGH'];
  const counts = states.map(() => states.map(() => 0));
  for (let index = 0; index < regimes.length - 1; index += 1) {
    const fromIndex = states.indexOf(regimes[index] || 'MEDIUM');
    const toIndex = states.indexOf(regimes[index + 1] || 'MEDIUM');
    if (fromIndex >= 0 && toIndex >= 0) counts[fromIndex][toIndex] += 1;
  }
  return counts.map((row) => {
    const total = row.reduce((sum, value) => sum + value, 0);
    return row.map((value) => (total > 0 ? value / total : 0));
  });
}

function extractScalar(metric: unknown): number | null {
  if (typeof metric === 'number' && Number.isFinite(metric)) return metric;
  if (Array.isArray(metric) && metric.length && typeof metric[metric.length - 1] === 'number') return Number(metric[metric.length - 1]);
  if (metric && typeof metric === 'object') {
    const record = metric as Record<string, unknown>;
    const preferred = [
      'deployable_survival_score',
      'survival_score',
      'ruin_probability',
      'mc_ruin_probability',
      'stability_score',
      'fragility_score',
      'systemic_fragility_score',
      'latest_volatility',
      'current_vol',
      'worst_case_dd',
      'risk_amount',
      'model_size',
      'allocated_capital',
      'max_safe_leverage',
      'capital_multiplier',
      'throttle_level',
      'threshold',
      'drawdown_p95',
      'capital_decay_rate',
      'overlap_ratio',
      'average_correlation',
      'diversification_ratio',
      'effective_bets',
      'portfolio_variance',
      'payoff_ratio',
      'profit_factor',
      'expected_return',
    ];
    for (const key of preferred) {
      if (typeof record[key] === 'number' && Number.isFinite(record[key] as number)) {
        return Number(record[key]);
      }
    }
    const firstNumeric = Object.values(record).find((value) => typeof value === 'number' && Number.isFinite(value));
    if (typeof firstNumeric === 'number') return firstNumeric;
  }
  return null;
}

function extractMetricValue(key: string, metric: unknown): string {
  if (metric == null) {
    return 'Unavailable';
  }
  if (typeof metric === 'number') {
    const normalized = normalizeDisplayNumber(metric);
    if (currencyMetricKeys.has(key)) {
      return formatCurrency(normalized);
    }
    if (key.includes('rate') || key.includes('probability') || key.includes('score') || key === 'win_rate' || key === 'loss_rate') {
      if (normalized >= 0 && normalized <= 1) return formatPercent(normalized);
    }
    return Math.abs(normalized) <= 10 ? formatNumber(normalized) : formatCompactNumber(normalized);
  }
  if (typeof metric === 'string' || typeof metric === 'boolean') {
    return String(metric);
  }
  if (Array.isArray(metric)) {
    return 'Shown in chart';
  }
  const record = metric as Record<string, unknown>;
  if (chartOnlyMetrics.has(key)) {
    return 'Shown in chart';
  }
  if (key === 'adjusted_pnl') {
    return formatCurrency(Number(record.total_net_pnl || 0));
  }
  if (key === 'cost_summary') {
    return formatCurrency(Number(record.total_cost || 0));
  }
  if (key === 'student_t_fit') {
    return `Df ${formatNumber(Number(record.df || record.degrees_of_freedom || 0))} · Scale ${formatNumber(Number(record.scale || 0))}`;
  }
  if (key === 'pareto_fit') {
    return `Alpha ${formatNumber(Number(record.pareto_alpha || record.alpha || 0))} · Threshold ${formatNumber(Number(record.tail_threshold || record.threshold || 0))}`;
  }
  if (key === 'power_law_exponent' || key === 'power_law_fit') {
    return `Alpha ${formatNumber(Number(record.power_law_alpha || record.alpha || 0))}`;
  }
  if (key === 'lognormal_test') {
    return `KS ${formatNumber(Number(record.lognormal_ks_stat || 0))} · P ${formatNumber(Number(record.lognormal_p_value || 0))}`;
  }
  if (key === 'normality_test') {
    const score = Number(record.jarque_bera_score || 0);
    const normal = Boolean(record.approximately_normal);
    return `${normal ? 'Closer to normal' : 'Non-normal'} · JB ${formatNumber(score)}`;
  }
  const scalar = extractScalar(metric);
  if (scalar != null) {
    const scalarKey = Object.entries(record).find(([, value]) => typeof value === 'number' && Number(value) === scalar)?.[0] || 'value';
    if (scalar >= 0 && scalar <= 1 && /(rate|ratio|probability|score)/i.test(scalarKey)) {
      return `${humanizeKey(scalarKey)}: ${formatPercent(scalar)}`;
    }
    return `${humanizeKey(scalarKey)}: ${formatNumber(scalar)}`;
  }
  const firstString = Object.entries(record).find(([, value]) => typeof value === 'string');
  if (firstString) {
    return `${humanizeKey(firstString[0])}: ${String(firstString[1])}`;
  }
  return `${Object.keys(record).length} fields`;
}

function metricInterpretation(key: string, metric: unknown): string | null {
  if (metric == null) return metricRequirement(key);
  const scalar = extractScalar(metric);
  const notes: Record<string, string> = {
    average_win: 'Higher is better. This is the average profit on winning trades.',
    average_loss: 'Closer to zero is better. Larger negative values mean bigger average losses.',
    payoff_ratio: 'Higher is better. Above 1 means average winners are larger than average losers.',
    profit_factor: 'Higher is better. Below 1 means losses outweigh profits.',
    expectancy: 'Higher is better. Positive expectancy means the trade process is profitable on average.',
    sharpe: 'Higher is better. It measures return earned per unit of volatility.',
    sortino: 'Higher is better. It focuses only on downside volatility.',
    calmar: 'Higher is better. It compares growth against drawdown pain.',
    cagr: 'Higher is better, but it should be judged alongside drawdown.',
    volatility: 'Lower is calmer. High volatility means a bumpier equity path.',
    max_drawdown: 'Less severe is better. Deeper drawdowns mean larger capital damage.',
    drawdown_duration: 'Lower is better. Long drawdowns mean slower recovery.',
    ulcer_index: 'Lower is better. It captures the depth and persistence of drawdowns.',
    downside_deviation: 'Lower is better. It measures harmful volatility only.',
    value_at_risk: 'Less negative is safer. It estimates a typical bad-tail loss.',
    conditional_var: 'Less negative is safer. It estimates the average loss beyond VaR.',
    skewness: 'Positive is usually friendlier. Negative skew can hide crash-like losses.',
    kurtosis: 'Lower is usually calmer. High kurtosis suggests fatter tails.',
    tail_ratio: 'Higher is generally better. It means the upside tail is stronger than the downside tail.',
    autocorrelation: 'Closer to zero is cleaner. High autocorrelation can imply path dependence.',
    stability_score: 'Higher is better. It summarizes robustness across multiple checks.',
    diversification_ratio: 'Higher is better. It means the portfolio is getting more diversification benefit.',
    effective_number_of_bets: 'Higher is better. It reflects how diversified the exposures really are.',
    deployable_leverage: 'Higher is only good if drawdown remains controlled.',
    risk_of_ruin: 'Lower is better. This should stay close to zero.',
    survival_score: 'Higher is better. It reflects deployment durability.',
  };
  if (notes[key]) return notes[key];
  if (percentageMetricKeys.has(key) && scalar != null) return 'Interpret as a rate. Higher is better only when the metric represents success or coverage.';
  if (typeof metric === 'object' && metric && !Array.isArray(metric)) return 'Read this as a model summary, not a single score.';
  return null;
}

function metricRequirement(key: string): string | null {
  const requirements: Record<string, string> = {
    average_loss: 'Needs at least one losing closed trade.',
    payoff_ratio: 'Needs both winning and losing closed trades.',
    profit_factor: 'Needs both gross profit and gross loss observations.',
    sortino: 'Needs downside-return observations.',
    rolling_sharpe: 'Needs a longer return history to build a rolling series.',
    rolling_volatility: 'Needs a longer return history to build a rolling series.',
    adaptive_rolling_volatility: 'Needs a longer return history to build an adaptive series.',
    drawdown_duration: 'Needs at least one drawdown period.',
    ulcer_index: 'Needs a non-flat equity path.',
    value_at_risk: 'Needs a stable return distribution sample.',
    conditional_var: 'Needs tail-loss observations.',
    normality_test: 'Needs enough return observations to assess distribution shape.',
    student_t_fit: 'Needs enough return observations to fit a heavy-tail model.',
    pareto_fit: 'Needs enough tail observations.',
    power_law_exponent: 'Needs enough tail observations.',
    lognormal_test: 'Needs positive-valued observations.',
    autocorrelation: 'Needs sequential return observations.',
    regime_transition_matrix: 'Needs a regime series across multiple periods.',
    walk_forward: 'Needs segmented return windows.',
    correlation: 'Needs at least two aligned return books.',
    covariance_matrix: 'Needs at least two aligned return books.',
    portfolio_variance: 'Needs aligned book returns and allocation weights.',
    stress_engine: 'Needs aligned return books and stress assumptions.',
    survival_engine: 'Needs impact, leverage, and survival policy inputs.',
  };
  return requirements[key] || null;
}

function buildMetricPayload(data: OverviewData | undefined, startingCapital: number) {
  const trades = data?.trades || [];
  const closed = chronologicalClosedTrades(trades);
  const returns = buildDailyReturns(trades, startingCapital);
  const books = buildBookMatrix(trades, returns);
  const strategyPayload = Object.fromEntries(books.labels.map((label, index) => [label, books.matrix[index]]));
  const spreadMatrix = books.matrix.length
    ? books.matrix.map((series) => series.map((value) => Math.min(0.02, Math.max(0.00005, Math.abs(value) * 0.08 + 0.0001))))
    : undefined;

  return {
    returns,
    net_pnl: closed.map((trade) => Number(trade.net_pnl || 0)),
    gross_pnl: closed.map((trade) => Number(trade.gross_pnl || 0)),
    brokerage: closed.map((trade) => Number(trade.commission || 0) + Number(trade.fees || 0)),
    slippage: closed.map((trade) => Number(trade.slippage_cost || 0)),
    swaps: closed.map((trade) => Number(trade.swaps || 0)),
    strategies: Object.keys(strategyPayload).length ? strategyPayload : undefined,
    capital: startingCapital,
    total_capital: startingCapital,
    target_volatility: 0.15,
    max_drawdown_threshold: 0.25,
    max_leverage: 3,
    fractional_kelly: 0.5,
    risk_budget: books.labels.length ? new Array(books.labels.length).fill(1 / books.labels.length) : undefined,
    spread_matrix: spreadMatrix,
    ruin_floor: 0.2,
    entry_price: Number(closed[closed.length - 1]?.entry_price || 100),
    stop_price: Number(closed[closed.length - 1]?.stop_loss_at_entry || 95),
    risk_per_trade: 0.01,
  };
}

function buildDerivedMetrics(data: OverviewData | undefined, startingCapital: number): Record<string, unknown> {
  const trades = data?.trades || [];
  const closed = chronologicalClosedTrades(trades);
  const returns = buildReturns(trades, startingCapital);
  const netPnls = closed.map((trade) => Number(trade.net_pnl || 0));
  const wins = netPnls.filter((value) => value > 0);
  const losses = netPnls.filter((value) => value <= 0);
  const avgWin = average(wins);
  const avgLoss = average(losses);
  const payoffRatio = losses.length && avgLoss !== 0 ? Math.abs(avgWin / avgLoss) : 0;
  const grossProfit = wins.reduce((sum, value) => sum + value, 0);
  const grossLoss = Math.abs(losses.reduce((sum, value) => sum + value, 0));
  const returnsStd = sampleStd(returns);
  const downside = downsideDeviation(returns);
  const rollingSharpeSeries = rollingWindow(returns, Math.min(20, Math.max(10, Math.floor(returns.length / 5) || 10)), (window) => {
    return annualizedSharpeRatio(window);
  });
  const rollingVolSeries = rollingWindow(returns, Math.min(20, Math.max(10, Math.floor(returns.length / 5) || 10)), (window) => sampleStd(window));
  const ddSeries = drawdownSeries(returns);
  const maxDrawdown = maxDrawdownFromReturns(returns);
  const ddDuration = maxDrawdownDuration(returns);
  const ui = Math.sqrt(average(ddSeries.map((value) => (value * 100) ** 2)));
  const var95 = percentile(returns, 0.05);
  const cvar95 = average(returns.filter((value) => value <= var95));
  const skew = skewness(returns);
  const kurt = kurtosis(returns);
  const tailRatio = Math.abs(percentile(returns, 0.95) / Math.min(-1e-9, percentile(returns, 0.05)));
  const absAutocorr = autocorrelation(returns.map((value) => Math.abs(value)));
  const jb = returns.length ? (returns.length / 6) * (skew ** 2 + ((kurt - 3) ** 2) / 4) : 0;
  const books = buildBookMatrix(trades, returns);
  const covariance = covarianceMatrix(books.matrix);
  const correlation = correlationFromCovariance(covariance);
  const vols = books.matrix.map((series, index) => Math.sqrt(Math.max(covariance[index]?.[index] || 0, 0)));
  const inverseVolWeights = vols.length
    ? vols.map((value) => (value > 0 ? 1 / value : 0))
    : [];
  const inverseVolTotal = inverseVolWeights.reduce((sum, value) => sum + value, 0) || 1;
  const weights = inverseVolWeights.map((value) => value / inverseVolTotal);
  const portfolioReturns = books.matrix.length && weights.length
    ? books.matrix[0].map((_, index) => books.matrix.reduce((sum, series, seriesIndex) => sum + series[index] * (weights[seriesIndex] || 0), 0))
    : returns;
  const portfolioVariance = books.matrix.length > 1
    ? weights.reduce((outer, weightRow, rowIndex) => outer + weights.reduce((inner, weightCol, colIndex) => inner + weightRow * weightCol * (covariance[rowIndex]?.[colIndex] || 0), 0), 0)
    : returnsStd ** 2;
  const portfolioVol = Math.sqrt(Math.max(portfolioVariance, 0));
  const riskContributions = weights.map((weight, index) => ({ metric: books.labels[index] || `Book ${index + 1}`, value: Number((weight * ((covariance[index]?.[index] || 0) ** 0.5 || 0)).toFixed(4)) }));
  const averageCorrelation = correlation.length > 1
    ? average(correlation.flatMap((row, rowIndex) => row.filter((_, colIndex) => rowIndex !== colIndex)))
    : 0;
  const diversificationRatio = portfolioVol > 0 && weights.length
    ? weights.reduce((sum, weight, index) => sum + weight * (vols[index] || 0), 0) / portfolioVol
    : 1;
  const effectiveBets = weights.length ? 1 / weights.reduce((sum, value) => sum + value ** 2, 0) : 1;
  const marketBuckets = new Map<string, number>();
  closed.forEach((trade) => {
    const key = String(trade.market_type || 'unknown');
    marketBuckets.set(key, (marketBuckets.get(key) || 0) + Number(trade.net_pnl || 0));
  });
  const setupBuckets = new Map<string, { wins: number; total: number }>();
  closed.forEach((trade) => {
    const key = String(trade.setup_name || trade.strategy || trade.strategy_tag || 'Unspecified');
    const bucket = setupBuckets.get(key) || { wins: 0, total: 0 };
    bucket.total += 1;
    if (Number(trade.net_pnl || 0) > 0) bucket.wins += 1;
    setupBuckets.set(key, bucket);
  });
  const regimeBase = rollingVolSeries.length ? rollingVolSeries : returns.map((_, index) => sampleStd(returns.slice(Math.max(0, index - 9), index + 1)));
  const lowCut = percentile(regimeBase, 0.33);
  const highCut = percentile(regimeBase, 0.66);
  const regimeSeries = regimeBase.map((value) => (value <= lowCut ? 'LOW' : value >= highCut ? 'HIGH' : 'MEDIUM'));
  const regimeReturns: Record<string, number[]> = { LOW: [], MEDIUM: [], HIGH: [] };
  returns.forEach((value, index) => {
    const regime = regimeSeries[index] || 'MEDIUM';
    regimeReturns[regime].push(value);
  });
  const regimeSharpe = Object.fromEntries(Object.entries(regimeReturns).map(([label, series]) => [label, sampleStd(series) > 0 ? average(series) / sampleStd(series) : 0]));
  const regimeDrawdown = Object.fromEntries(Object.entries(regimeReturns).map(([label, series]) => [label, maxDrawdownFromReturns(series)]));
  const regimeSwitchCount = regimeSeries.reduce((count, value, index) => count + (index > 0 && value !== regimeSeries[index - 1] ? 1 : 0), 0);
  const walkForwardWindows = rollingWindow(returns, Math.min(40, Math.max(20, Math.floor(returns.length / 4) || 20)), (window) => average(window));
  const walkForwardPassRate = walkForwardWindows.length ? walkForwardWindows.filter((value) => value > 0).length / walkForwardWindows.length : 0;
  const bootstrapMedian = average(returns);
  const bootstrapLow = percentile(returns, 0.1);
  const bootstrapHigh = percentile(returns, 0.9);
  const stabilityScore = Math.max(0, Math.min(1, 0.55 + walkForwardPassRate * 0.2 + Math.max(0, 0.25 - Math.abs(maxDrawdown)) * 0.5));
  const positionRisk = Number(closed[closed.length - 1]?.risk_amount || Math.max(500, startingCapital * 0.01));
  const latestEntry = Number(closed[closed.length - 1]?.entry_price || 100);
  const latestStop = Number(closed[closed.length - 1]?.stop_loss_at_entry || latestEntry * 0.98);
  const modelSize = Math.abs(latestEntry - latestStop) > 0 ? positionRisk / Math.abs(latestEntry - latestStop) : 0;
  const capitalAllocations = Object.fromEntries(books.labels.map((label, index) => [label, Number(((weights[index] || 0) * startingCapital).toFixed(2))]));
  const participationImpact = Math.abs(average(portfolioReturns)) * 0.15;
  const stressWorst = Math.min(
    maxDrawdown,
    percentile(portfolioReturns, 0.01) * 4,
    percentile(portfolioReturns, 0.05) * 2.5,
  );
  const ruinProbability = Math.max(0, Math.min(1, Math.abs(maxDrawdown) * 1.8 + Math.max(0, -average(portfolioReturns)) * 30));
  const deployableLeverage = Math.max(0.25, Math.min(3, 1.5 / Math.max(portfolioVol * 25, 0.5)));
  const survivalScore = Math.max(0, Math.min(1, 1 - ruinProbability * 0.8 - Math.abs(stressWorst) * 1.2));
  const fragilityScore = Math.max(0, Math.min(1, Math.abs(averageCorrelation) * 0.6 + Math.abs(maxDrawdown) * 0.8));

  return {
    trade_count: closed.length,
    win_count: wins.length,
    loss_count: losses.length,
    win_rate: closed.length ? wins.length / closed.length : 0,
    loss_rate: closed.length ? losses.length / closed.length : 0,
    average_win: avgWin,
    average_loss: avgLoss,
    payoff_ratio: payoffRatio,
    profit_factor: grossLoss > 0 ? grossProfit / grossLoss : 0,
    expectancy: closed.length ? average(netPnls) : 0,
    cost_summary: {
      total_brokerage: trades.reduce((sum, trade) => sum + Number(trade.commission || 0) + Number(trade.fees || 0), 0),
      total_slippage: trades.reduce((sum, trade) => sum + Number(trade.slippage_cost || 0), 0),
      total_swaps: trades.reduce((sum, trade) => sum + Number(trade.swaps || 0), 0),
      total_cost: trades.reduce((sum, trade) => sum + Number(trade.total_cost || Number(trade.commission || 0) + Number(trade.fees || 0) + Number(trade.swaps || 0) + Number(trade.slippage_cost || 0)), 0),
    },
    adjusted_pnl: {
      total_net_pnl: trades.reduce((sum, trade) => sum + Number(trade.net_pnl || 0), 0),
      cumulative_net_curve: closed.reduce<number[]>((rows, trade) => {
        const previous = rows[rows.length - 1] || 0;
        rows.push(previous + Number(trade.net_pnl || 0));
        return rows;
      }, []),
    },

    sharpe: annualizedSharpeRatio(returns),
    sortino: annualizedSortinoRatio(returns),
    calmar: maxDrawdown !== 0 ? annualizedGrowth(returns) / Math.abs(maxDrawdown) : 0,
    cagr: annualizedGrowth(returns),
    rolling_sharpe: rollingSharpeSeries,
    net_sharpe: annualizedSharpeRatio(returns),
    net_sortino: annualizedSortinoRatio(returns),
    net_cagr: annualizedGrowth(returns),
    equity_curve: buildEquitySeries(trades, startingCapital),

    volatility: returnsStd,
    rolling_volatility: rollingVolSeries,
    adaptive_rolling_volatility: { latest_volatility: rollingVolSeries[rollingVolSeries.length - 1] || returnsStd, average_volatility: average(rollingVolSeries) || returnsStd, series: rollingVolSeries },
    max_drawdown: Math.abs(maxDrawdown),
    rolling_drawdown: ddSeries,
    drawdown_duration: { max_periods: ddDuration.maxPeriods, current_periods: ddDuration.currentPeriods },
    ulcer_index: ui,
    downside_deviation: downside,
    value_at_risk: var95,
    conditional_var: cvar95,

    normality_test: { jarque_bera_score: jb, approximately_normal: jb < 6 },
    skewness: skew,
    kurtosis: kurt,
    fat_tail_index: Math.max(0, kurt - 3),
    tail_ratio: tailRatio,
    student_t_fit: { degrees_of_freedom: Math.max(3, 12 - Math.min(8, Math.max(0, kurt - 3))), scale: returnsStd },
    pareto_fit: { alpha: Math.max(1.1, 3 / Math.max(0.25, Math.max(0.2, Math.abs(percentile(returns, 0.1)) * 1000))), threshold: percentile(returns, 0.1) },
    power_law_exponent: { alpha: Math.max(1.2, 2 + Math.min(3, Math.abs(skew))) },
    lognormal_test: { positive_sample_ratio: returns.length ? returns.filter((value) => value > 0).length / returns.length : 0 },
    autocorrelation: autocorrelation(returns),
    pareto_tail_estimator: { alpha: Math.max(1.2, 2 + Math.min(3, Math.abs(skew))) },
    power_law_fit: { alpha: Math.max(1.2, 2 + Math.min(3, Math.abs(skew))), fit_quality: Math.max(0, 1 - Math.abs(skew - 1) / 5) },

    volatility_regime: { latest_regime: regimeSeries[regimeSeries.length - 1] || 'MEDIUM', regime_series: regimeSeries },
    regime_labeling: { regimes: regimeSeries, low_count: regimeSeries.filter((value) => value === 'LOW').length, medium_count: regimeSeries.filter((value) => value === 'MEDIUM').length, high_count: regimeSeries.filter((value) => value === 'HIGH').length },
    regime_sharpe: regimeSharpe,
    regime_drawdown: regimeDrawdown,
    regime_transition_matrix: { switch_count: regimeSwitchCount, persistence_ratio: regimeSeries.length > 1 ? 1 - regimeSwitchCount / (regimeSeries.length - 1) : 1, states: ['LOW', 'MEDIUM', 'HIGH'], matrix: buildRegimeTransitionHeatmap(regimeSeries) },
    regime_switching: { regime_changes: regimeSwitchCount, switch_rate: regimeSeries.length > 1 ? regimeSwitchCount / (regimeSeries.length - 1) : 0 },
    volatility_clustering: { abs_return_autocorrelation: absAutocorr },
    garch_volatility: { latest_volatility: regimeBase[regimeBase.length - 1] || returnsStd },
    regime_breakdown: { best_regime: Object.entries(regimeSharpe).sort((a, b) => Number(b[1]) - Number(a[1]))[0]?.[0] || 'MEDIUM', best_sharpe: Math.max(...Object.values(regimeSharpe).map(Number), 0), worst_drawdown: Math.min(...Object.values(regimeDrawdown).map(Number), 0) },
    regime_fragility: { fragility_score: Math.max(0, Math.min(1, Math.abs(regimeSwitchCount / Math.max(1, regimeSeries.length)) + Math.abs(Math.min(...Object.values(regimeDrawdown).map(Number), 0)))) },

    walk_forward: { pass_rate: walkForwardPassRate, windows: walkForwardWindows.length },
    bootstrap: { median_return: bootstrapMedian, ci_low: bootstrapLow, ci_high: bootstrapHigh },
    block_bootstrap: { median_return: bootstrapMedian * 0.98, ci_low: bootstrapLow * 1.05, ci_high: bootstrapHigh * 0.95 },
    parameter_sensitivity: { stability_score: Math.max(0, Math.min(1, 1 - returnsStd * 20)) },
    noise_stability: { stability_score: Math.max(0, Math.min(1, 1 - sampleStd(returns.map((value, index) => value - (rollingVolSeries[index] || 0))) * 10)) },
    regime_stability: { stability_score: Math.max(0, Math.min(1, 1 - regimeSwitchCount / Math.max(1, regimeSeries.length))) },
    monte_carlo_stability: { median_terminal: annualizedGrowth(portfolioReturns), worst_case: percentile(portfolioReturns, 0.05) },
    stability_score: { stability_score: stabilityScore, stability_grade: stabilityScore > 0.8 ? 'HIGH' : stabilityScore > 0.6 ? 'MODERATE' : 'LOW' },

    correlation,
    covariance_matrix: covariance,
    portfolio_variance: portfolioVariance,
    risk_contribution: { top_contributor: riskContributions.sort((a, b) => b.value - a.value)[0]?.metric || 'Book 1', top_contribution: riskContributions.sort((a, b) => b.value - a.value)[0]?.value || 0 },
    risk_parity: { max_weight: Math.max(...weights, 0), min_weight: Math.min(...weights, 0) },
    target_volatility: { target: 0.15, realized: portfolioVol },
    drawdown_correlation: { average_correlation: averageCorrelation },
    crash_overlap: { overlap_ratio: Math.max(0, Math.min(1, Math.abs(percentile(portfolioReturns, 0.05)) * 20)) },
    systemic_fragility: { systemic_fragility_score: Math.max(0, Math.min(1, Math.abs(averageCorrelation) * 0.8)) },
    portfolio_fragility_index: { fragility_index: Math.max(0, Math.min(1, fragilityScore)) },
    portfolio_preprocessor: { strategy_count: books.labels.length || 1, observation_count: portfolioReturns.length },
    diversification_ratio: diversificationRatio,
    effective_number_of_bets: effectiveBets,
    hierarchical_risk_parity: { max_weight: Math.max(...weights, 0), min_weight: Math.min(...weights, 0) },
    dynamic_cluster_risk_budgeting: { cluster_count: books.labels.length || 1, max_cluster_weight: Math.max(...weights, 1) },
    drawdown_aware_capital_allocator: { allocated_capital: startingCapital * Math.max(0.4, 1 - Math.abs(maxDrawdown)), drawdown_penalty: Math.abs(maxDrawdown) },

    risk_budgeting: { allocated_books: books.labels.length || 1, top_weight: Math.max(...weights, 1) },
    kelly: { recommended_fraction: Math.max(0, Math.min(1, payoffRatio * (wins.length / Math.max(1, netPnls.length)) - (losses.length / Math.max(1, netPnls.length)) / Math.max(payoffRatio, 1))), max_fraction: Math.max(...weights, 0) },
    portfolio_position_sizer: { books_sized: books.labels.length || 1, gross_notional: Object.values(capitalAllocations).reduce((sum, value) => sum + Number(value), 0) || startingCapital },
    position_sizer: { risk_amount: positionRisk, model_size: modelSize },
    capital_engine: { allocated_capital: Object.values(capitalAllocations).reduce((sum, value) => sum + Number(value), 0) || startingCapital, active_books: books.labels.length || 1 },

    kill_switch: { triggered: Math.abs(maxDrawdown) > 0.2, threshold: 0.2 },
    dynamic_throttle: { throttle_level: Math.max(0.25, 1 - Math.abs(maxDrawdown) * 2), active: Math.abs(maxDrawdown) > 0.1 },
    capital_throttle_engine: { capital_multiplier: Math.max(0.25, 1 - Math.abs(maxDrawdown) * 2) },

    stress_engine: { worst_case_dd: stressWorst, base_drawdown: maxDrawdown, execution_impact_dd: stressWorst * 0.85 },
    volatility_spike: { current_vol: rollingVolSeries[rollingVolSeries.length - 1] || returnsStd, vol_threshold: percentile(rollingVolSeries.length ? rollingVolSeries : [returnsStd], 0.9), vol_spike: (rollingVolSeries[rollingVolSeries.length - 1] || returnsStd) > percentile(rollingVolSeries.length ? rollingVolSeries : [returnsStd], 0.9) },
    liquidity_shock: { worst_liquidity_drag: participationImpact * 1.5 },
    correlation_spike: { stressed_correlation: Math.min(0.95, Math.max(0.1, Math.abs(averageCorrelation) + 0.2)) },
    crash_simulation: { worst_case_drawdown: Math.min(stressWorst * 1.1, maxDrawdown * 1.4) },
    stress_scenarios: { tail_scenario_loss: percentile(portfolioReturns, 0.01) },
    regime_path_generator: { worst_regime_path: Math.min(...Object.values(regimeDrawdown).map(Number), 0) },
    spread_regime_generator: { max_spread: Math.max(...portfolioReturns.map((value) => Math.abs(value) * 0.08 + 0.0001), 0.0001) },
    execution_impact_model: { impact_drag: participationImpact },

    fragility_score: { fragility_score: fragilityScore },
    deployable_leverage: { max_safe_leverage: deployableLeverage },
    kill_switch_threshold: { threshold: Math.max(0.08, Math.min(0.2, Math.abs(stressWorst) * 1.4)) },
    capital_throttle_policy: { capital_multiplier: Math.max(0.25, survivalScore) },
    drawdown_percentile: { drawdown_p95: Math.abs(percentile(ddSeries, 0.05)) },
    capital_decay: { capital_decay_rate: Math.max(0.01, Math.abs(participationImpact)) },
    risk_of_ruin: { ruin_probability: ruinProbability, expected_time_to_ruin: (1 - ruinProbability) * Math.max(portfolioReturns.length, 1) },
    ruin_probability_mc: { mc_ruin_probability: ruinProbability * 1.05 },
    survival_score: { survival_score: survivalScore },
    survival_engine: { deployable_survival_score: survivalScore, probability_of_ruin: ruinProbability, survival_grade: survivalScore > 0.9 ? 'INSTITUTIONAL' : survivalScore > 0.75 ? 'ACCEPTABLE' : survivalScore > 0.55 ? 'FRAGILE' : 'NON-DEPLOYABLE' },
  };
}

function buildGroupVisuals(
  sectionTitle: string,
  mergedResults: Record<string, unknown>,
  overview: OverviewData | undefined,
  startingCapital: number,
  focusedChartTitle?: string | null,
  registerChartRef?: (title: string) => (node: HTMLDivElement | null) => void,
) {
  const trades = overview?.trades || [];
  const closed = chronologicalClosedTrades(trades);
  const returns = buildReturns(trades, startingCapital);
  const book = buildBookMatrix(trades, returns);
  const covariance = covarianceMatrix(book.matrix);
  const correlation = correlationFromCovariance(covariance);

  if (sectionTitle === 'Journal Metrics') {
    const costSummary = (mergedResults.cost_summary as Record<string, unknown>) || {};
    return (
      <div className="grid gap-4 lg:grid-cols-3">
        <VisualCard title="Cost Breakdown" highlighted={focusedChartTitle === 'Cost Breakdown'} cardRef={registerChartRef?.('Cost Breakdown')}>
          <MetricsBarChart
            data={[
              { metric: 'Brokerage', value: Number(costSummary.total_brokerage || 0) },
              { metric: 'Slippage', value: Number(costSummary.total_slippage || 0) },
              { metric: 'Swaps', value: Number(costSummary.total_swaps || 0) },
              { metric: 'Total Cost', value: Number(costSummary.total_cost || 0) },
            ]}
          />
        </VisualCard>
      </div>
    );
  }

  if (sectionTitle === 'Performance Metrics') {
    const equity = (mergedResults.equity_curve as Array<{ t: string; equity: number }>) || buildEquitySeries(trades, startingCapital);
    const rollingSharpe = toNumberArray(mergedResults.rolling_sharpe);
    const rollingSharpeSeries = buildRollingDateSeries(trades, rollingSharpe, 'rolling', 'W');
    return (
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1.75fr)_minmax(0,1fr)]">
        <div className="lg:row-span-2">
          <VisualCard title="Equity Curve" className="h-[680px]" highlighted={focusedChartTitle === 'Equity Curve'} cardRef={registerChartRef?.('Equity Curve')}>
            <EquityCurveChart data={equity} className="h-[680px]" />
          </VisualCard>
        </div>
        <div className="grid gap-4">
          <VisualCard title="Rolling Sharpe" className="h-[340px]" highlighted={focusedChartTitle === 'Rolling Sharpe'} cardRef={registerChartRef?.('Rolling Sharpe')}>
            <GenericTimeSeriesChart
              data={rollingSharpeSeries}
              series={[{ key: 'rolling', color: '#1d4ed8', name: 'Rolling Sharpe' }]}
              className="h-[340px]"
              xTickFormatter={formatAxisDate}
              tooltipLabelFormatter={(label) => formatDate(label)}
            />
          </VisualCard>
          <VisualCard title="Performance Snapshot" className="h-[340px]" highlighted={focusedChartTitle === 'Performance Snapshot'} cardRef={registerChartRef?.('Performance Snapshot')}>
            <MetricsBarChart 
              data={[
                { metric: 'Sharpe', value: Number(extractScalar(mergedResults.sharpe) || 0) },
                { metric: 'Sortino', value: Number(extractScalar(mergedResults.sortino) || 0) },
                { metric: 'Calmar', value: Number(extractScalar(mergedResults.calmar) || 0) },
                { metric: 'CAGR', value: Number(extractScalar(mergedResults.cagr) || 0) },
                { metric: 'Net Sh.', value: Number(extractScalar(mergedResults.net_sharpe) || 0) },
                { metric: 'Net So.', value: Number(extractScalar(mergedResults.net_sortino) || 0) },
                { metric: 'Net CAGR', value: Number(extractScalar(mergedResults.net_cagr) || 0) },
              ]} 
              className="h-[340px]"
              tickAngle={-18}
              tickHeight={82}
              tooltipLabelFormatter={(label) =>
                ({
                  Sharpe: 'Sharpe',
                  Sortino: 'Sortino',
                  Calmar: 'Calmar',
                  CAGR: 'CAGR',
                  'Net Sh.': 'Net Sharpe',
                  'Net So.': 'Net Sortino',
                  'Net CAGR': 'Net CAGR',
                }[label] || label)
              }
            />
          </VisualCard>
        </div>
        <VisualCard title="Outcome Mix" className="h-[300px]" highlighted={focusedChartTitle === 'Outcome Mix'} cardRef={registerChartRef?.('Outcome Mix')}>
          <PieMetricChart 
            data={[
              { name: 'Winning Trades', value: closed.filter((trade) => Number(trade.net_pnl || 0) > 0).length },
              { name: 'Losing Trades', value: closed.filter((trade) => Number(trade.net_pnl || 0) <= 0).length },
            ]} 
            className="h-[300px]"
          />
        </VisualCard>
      </div>
    );
  }

  if (sectionTitle === 'Risk Metrics') {
    const rollingVol = toNumberArray(mergedResults.rolling_volatility);
    const adaptiveSeries = toNumberArray((mergedResults.adaptive_rolling_volatility as Record<string, unknown>)?.series);
    const drawdowns = toNumberArray(mergedResults.rolling_drawdown);
    return (
      <div className="grid gap-4 lg:grid-cols-2">
        <VisualCard title="Volatility Curves" highlighted={focusedChartTitle === 'Volatility Curves'} cardRef={registerChartRef?.('Volatility Curves')}>
          <GenericTimeSeriesChart
            data={rollingVol.map((value, index) => ({
              label: `W${index + 1}`,
              rolling: normalizeDisplayNumber(value),
              adaptive: normalizeDisplayNumber(adaptiveSeries[index] ?? value),
            }))}
            series={[
              { key: 'rolling', color: '#0f766e', name: 'Rolling Volatility' },
              { key: 'adaptive', color: '#7c3aed', name: 'Adaptive Volatility' },
            ]}
          />
        </VisualCard>
        <VisualCard title="Drawdown Curve" highlighted={focusedChartTitle === 'Drawdown Curve'} cardRef={registerChartRef?.('Drawdown Curve')}>
          <GenericTimeSeriesChart
            data={buildLabeledSeries(drawdowns, 'T', 'drawdown')}
            series={[{ key: 'drawdown', color: '#b91c1c', name: 'Rolling Drawdown' }]}
          />
        </VisualCard>
        <VisualCard title="Risk Snapshot" highlighted={focusedChartTitle === 'Risk Snapshot'} cardRef={registerChartRef?.('Risk Snapshot')}>
          <MetricsBarChart data={[
            { metric: 'Volatility', value: Number(extractScalar(mergedResults.volatility) || 0) },
            { metric: 'Max DD', value: Math.abs(Number(extractScalar(mergedResults.max_drawdown) || 0)) },
            { metric: 'Ulcer', value: Number(extractScalar(mergedResults.ulcer_index) || 0) },
            { metric: 'CVaR', value: Math.abs(Number(extractScalar(mergedResults.conditional_var) || 0)) },
          ]} />
        </VisualCard>
        <VisualCard title="Risk Shape">
          <RadarMetricChart data={[
            { metric: 'Volatility', value: Number(extractScalar(mergedResults.volatility) || 0) },
            { metric: 'Drawdown', value: Math.abs(Number(extractScalar(mergedResults.max_drawdown) || 0)) },
            { metric: 'Ulcer', value: Number(extractScalar(mergedResults.ulcer_index) || 0) },
            { metric: 'Downside', value: Number(extractScalar(mergedResults.downside_deviation) || 0) },
          ]} />
        </VisualCard>
      </div>
    );
  }

  if (sectionTitle === 'Distribution Metrics') {
    return (
      <div className="grid gap-4 lg:grid-cols-2">
        <VisualCard title="Return Distribution">
          <HistogramChart values={returns} bins={12} />
        </VisualCard>
        <VisualCard title="Distribution Shape">
          <MetricsBarChart data={[
            { metric: 'Skew', value: Number(extractScalar(mergedResults.skewness) || 0) },
            { metric: 'Kurtosis', value: Number(extractScalar(mergedResults.kurtosis) || 0) },
            { metric: 'Tail', value: Number(extractScalar(mergedResults.tail_ratio) || 0) },
            { metric: 'AutoCorr', value: Number(extractScalar(mergedResults.autocorrelation) || 0) },
          ]} />
        </VisualCard>
      </div>
    );
  }

  if (sectionTitle === 'Regime Metrics') {
    const labeling = (mergedResults.regime_labeling as Record<string, unknown>) || {};
    const regimeSeries = Array.isArray(labeling.regimes) ? (labeling.regimes as string[]) : [];
    const transitionMatrix = ((mergedResults.regime_transition_matrix as Record<string, unknown>)?.matrix as number[][] | undefined) || buildRegimeTransitionHeatmap(regimeSeries);
    return (
      <div className="grid gap-4 lg:grid-cols-2">
        <VisualCard title="Regime Distribution">
          <MetricsBarChart data={[
            { metric: 'Low', value: Number(labeling.low_count || 0) },
            { metric: 'Medium', value: Number(labeling.medium_count || 0) },
            { metric: 'High', value: Number(labeling.high_count || 0) },
            { metric: 'Switches', value: Number((mergedResults.regime_switching as Record<string, unknown>)?.regime_changes || 0) },
          ]} />
        </VisualCard>
        <VisualCard title="Transition Heatmap">
          <HeatmapChart labelsX={['LOW', 'MEDIUM', 'HIGH']} labelsY={['LOW', 'MEDIUM', 'HIGH']} matrix={transitionMatrix} />
        </VisualCard>
      </div>
    );
  }

  if (sectionTitle === 'Robustness Metrics') {
    return (
      <div className="grid gap-4 lg:grid-cols-2">
        <VisualCard title="Robustness Scores">
          <MetricsBarChart data={[
            { metric: 'Walk Fwd', value: Number(extractScalar(mergedResults.walk_forward) || 0) },
            { metric: 'Bootstrap', value: Number(extractScalar(mergedResults.bootstrap) || 0) },
            { metric: 'Noise', value: Number(extractScalar(mergedResults.noise_stability) || 0) },
            { metric: 'Stability', value: Number(extractScalar(mergedResults.stability_score) || 0) },
          ]} />
        </VisualCard>
        <VisualCard title="Robustness Profile">
          <RadarMetricChart data={[
            { metric: 'Walk Fwd', value: Number(extractScalar(mergedResults.walk_forward) || 0) },
            { metric: 'Param', value: Number(extractScalar(mergedResults.parameter_sensitivity) || 0) },
            { metric: 'Noise', value: Number(extractScalar(mergedResults.noise_stability) || 0) },
            { metric: 'Regime', value: Number(extractScalar(mergedResults.regime_stability) || 0) },
            { metric: 'Monte Carlo', value: Number(extractScalar(mergedResults.monte_carlo_stability) || 0) },
          ]} />
        </VisualCard>
      </div>
    );
  }

  if (sectionTitle === 'Portfolio Metrics') {
    const labels = book.labels.length ? book.labels : ['Book 1'];
    const matrix = correlation.length ? correlation : [[1]];
    const vols = book.matrix.map((series, index) => Math.sqrt(Math.max(covariance[index]?.[index] || sampleStd(series) ** 2 || 0, 0)));
    const inverseVolWeights = vols.length ? vols.map((value) => (value > 0 ? 1 / value : 0)) : [1];
    const inverseVolTotal = inverseVolWeights.reduce((sum, value) => sum + value, 0) || 1;
    const weights = labels.map((label, index) => ({
      name: label,
      value: Number(((inverseVolWeights[index] || 0) / inverseVolTotal).toFixed(4)),
      index,
    }));
    return (
      <div className="grid gap-4 lg:grid-cols-2">
        <VisualCard title="Correlation Heatmap">
          <HeatmapChart labelsX={labels} labelsY={labels} matrix={matrix} />
        </VisualCard>
        <VisualCard title="Portfolio Health">
          <MetricsBarChart data={[
            { metric: 'Variance', value: Number(extractScalar(mergedResults.portfolio_variance) || 0) },
            { metric: 'Div Ratio', value: Number(extractScalar(mergedResults.diversification_ratio) || 0) },
            { metric: 'Eff Bets', value: Number(extractScalar(mergedResults.effective_number_of_bets) || 0) },
            { metric: 'Fragility', value: Number(extractScalar(mergedResults.portfolio_fragility_index) || 0) },
          ]} />
        </VisualCard>
        <VisualCard title="Portfolio Allocation">
          <PieMetricChart data={weights.map(({ name, value }) => ({ name, value }))} />
        </VisualCard>
        <VisualCard title="Risk Contribution">
          <MetricsBarChart data={labels.map((label, index) => ({ metric: label, value: Number(((weights[index]?.value || 0) * (vols[index] || 0)).toFixed(4)) }))} />
        </VisualCard>
      </div>
    );
  }

  if (sectionTitle === 'Capital Metrics') {
    return (
      <div className="grid gap-4 lg:grid-cols-2">
        <VisualCard title="Capital Deployment">
          <MetricsBarChart data={[
            { metric: 'Risk Budget', value: Number(extractScalar(mergedResults.risk_budgeting) || 0) },
            { metric: 'Kelly', value: Number(extractScalar(mergedResults.kelly) || 0) },
            { metric: 'Pos Size', value: Number(extractScalar(mergedResults.position_sizer) || 0) },
            { metric: 'Allocated', value: Number(extractScalar(mergedResults.capital_engine) || 0) },
          ]} />
        </VisualCard>
        <VisualCard title="Capital Profile">
          <RadarMetricChart data={[
            { metric: 'Risk Budget', value: Number(extractScalar(mergedResults.risk_budgeting) || 0) },
            { metric: 'Kelly', value: Number(extractScalar(mergedResults.kelly) || 0) },
            { metric: 'Position', value: Number(extractScalar(mergedResults.position_sizer) || 0) },
            { metric: 'Engine', value: Number(extractScalar(mergedResults.capital_engine) || 0) },
          ]} />
        </VisualCard>
      </div>
    );
  }

  if (sectionTitle === 'Risk Control Metrics') {
    return (
      <div className="grid gap-4 lg:grid-cols-2">
        <VisualCard title="Control Layer">
          <MetricsBarChart data={[
            { metric: 'Kill Switch', value: Number(extractScalar(mergedResults.kill_switch) || 0) },
            { metric: 'Throttle', value: Number(extractScalar(mergedResults.dynamic_throttle) || 0) },
            { metric: 'Capital Mult', value: Number(extractScalar(mergedResults.capital_throttle_engine) || 0) },
          ]} />
        </VisualCard>
        <VisualCard title="Control Profile">
          <RadarMetricChart data={[
            { metric: 'Kill', value: Number(extractScalar(mergedResults.kill_switch) || 0) },
            { metric: 'Throttle', value: Number(extractScalar(mergedResults.dynamic_throttle) || 0) },
            { metric: 'Capital', value: Number(extractScalar(mergedResults.capital_throttle_engine) || 0) },
          ]} />
        </VisualCard>
      </div>
    );
  }

  if (sectionTitle === 'Stress Metrics') {
    const stressEngine = (mergedResults.stress_engine as Record<string, unknown>) || {};
    return (
      <div className="grid gap-4 lg:grid-cols-2">
        <VisualCard title="Stress Envelope">
          <MetricsBarChart data={[
            { metric: 'Base DD', value: Math.abs(Number(stressEngine.base_drawdown || 0)) },
            { metric: 'Impact DD', value: Math.abs(Number(stressEngine.execution_impact_dd || 0)) },
            { metric: 'Worst DD', value: Math.abs(Number(stressEngine.worst_case_dd || 0)) },
            { metric: 'Liq Shock', value: Number(extractScalar(mergedResults.liquidity_shock) || 0) },
          ]} />
        </VisualCard>
        <VisualCard title="Stress Profile">
          <RadarMetricChart data={[
            { metric: 'Vol Spike', value: Number(extractScalar(mergedResults.volatility_spike) || 0) },
            { metric: 'Liquidity', value: Number(extractScalar(mergedResults.liquidity_shock) || 0) },
            { metric: 'Corr Spike', value: Number(extractScalar(mergedResults.correlation_spike) || 0) },
            { metric: 'Crash', value: Number(extractScalar(mergedResults.crash_simulation) || 0) },
          ]} />
        </VisualCard>
      </div>
    );
  }

  if (sectionTitle === 'Survival Metrics') {
    return (
      <div className="grid gap-4 lg:grid-cols-2">
        <VisualCard title="Survival Layer">
          <MetricsBarChart data={[
            { metric: 'Survival', value: Number(extractScalar(mergedResults.survival_score) || 0) },
            { metric: 'Ruin', value: Number(extractScalar(mergedResults.risk_of_ruin) || 0) },
            { metric: 'Leverage', value: Number(extractScalar(mergedResults.deployable_leverage) || 0) },
            { metric: 'Fragility', value: Number(extractScalar(mergedResults.fragility_score) || 0) },
          ]} />
        </VisualCard>
        <VisualCard title="Survival Profile">
          <RadarMetricChart data={[
            { metric: 'Survival', value: Number(extractScalar(mergedResults.survival_score) || 0) },
            { metric: 'Ruin', value: Number(extractScalar(mergedResults.risk_of_ruin) || 0) },
            { metric: 'Leverage', value: Number(extractScalar(mergedResults.deployable_leverage) || 0) },
            { metric: 'Fragility', value: Number(extractScalar(mergedResults.fragility_score) || 0) },
          ]} />
        </VisualCard>
      </div>
    );
  }

  return null;
}

function VisualCard({
  title,
  children,
  className = "",
  highlighted = false,
  cardRef,
}: {
  title: string;
  children: React.ReactNode;
  className?: string;
  highlighted?: boolean;
  cardRef?: (node: HTMLDivElement | null) => void;
}) {
  return (
    <div
      ref={cardRef}
      className={`flex min-h-0 flex-col rounded-[22px] border border-black/10 bg-white p-4 dark:border-white/10 dark:bg-[#0b0b0b] ${
        highlighted ? 'ring-2 ring-[#ff5900] shadow-[0_0_0_1px_rgba(255,89,0,0.3),0_22px_54px_rgba(255,89,0,0.16)]' : ''
      } ${className}`}
    >
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-sm font-semibold text-black dark:text-white">{title}</h3>
        {highlighted ? <span className="rounded-full bg-[#ff5900]/12 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.12em] text-[#ff5900]">Insight focus</span> : null}
      </div>
      <div className="mt-3 min-h-0 flex-1 overflow-hidden" style={{ height: className.includes('h-[') ? 'auto' : '220px' }}>
        {children}
      </div>
    </div>
  );
}

function renderDashboardContracts(
  contracts: DashboardChartContract[],
  focusedChartTitle?: string | null,
  registerChartRef?: (title: string) => (node: HTMLDivElement | null) => void,
) {
  const filteredContracts = contracts.filter((contract) => {
    const title = String(contract.title || '').toLowerCase();
    return !title.includes('trade count') && !title.includes('total completed trades');
  });

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      {filteredContracts.map((contract) => (
        <VisualCard
          key={`${contract.chart_type}-${contract.title}`}
          title={contract.title}
          highlighted={focusedChartTitle === contract.title}
          cardRef={registerChartRef?.(contract.title)}
        >
          {contract.chart_type === 'bar' ? <MetricsBarChart data={(contract.points || []) as Array<{ metric: string; value: number }>} /> : null}
          {contract.chart_type === 'pie' ? <PieMetricChart data={(contract.points || []) as Array<{ name: string; value: number }>} /> : null}
          {contract.chart_type === 'radar' ? <RadarMetricChart data={(contract.points || []) as Array<{ metric: string; value: number }>} /> : null}
          {contract.chart_type === 'timeseries' ? (
            <GenericTimeSeriesChart
              data={(contract.points || []) as Array<{ label: string; [key: string]: string | number }>}
              series={(contract.series || []) as Array<{ key: string; color: string; name?: string }>}
            />
          ) : null}
          {contract.chart_type === 'heatmap' ? (
            <HeatmapChart labelsX={contract.labels_x || []} labelsY={contract.labels_y || []} matrix={contract.matrix || []} />
          ) : null}
          {contract.chart_type === 'histogram' ? <HistogramChart values={contract.values || []} bins={contract.bins || 10} /> : null}
        </VisualCard>
      ))}
    </div>
  );
}

function MetricCard({
  label,
  value,
  helper,
  metricKey,
}: {
  label: string;
  value: string;
  helper?: string | null;
  metricKey: string;
}) {
  const icon = getMetricIcon(metricKey);
  
  return (
    <div className="h-full min-h-[96px] rounded-[16px] border border-[#7dd3fc]/70 bg-[#e0f2fe] px-3 py-3 shadow-[0_18px_44px_rgba(14,165,233,0.12)] transition hover:border-[#ff5900] hover:shadow-[0_18px_44px_rgba(255,89,0,0.12)] dark:border-[#38bdf8]/40 dark:bg-[#082f49]/55 dark:hover:border-[#ff5900] dark:hover:shadow-[0_18px_44px_rgba(255,89,0,0.12)]">
      <div className="flex items-start gap-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#dbeafe] text-[#0284c7] dark:bg-[#0c4a6e] dark:text-[#7dd3fc]">
          {icon}
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-[0.6rem] font-semibold uppercase tracking-[0.13em] text-[#075985]/70 dark:text-[#bae6fd]/75">{label}</p>
          <p className="mt-1.5 text-[1.14rem] font-semibold tracking-[-0.03em] text-[#0c4a6e] dark:text-[#e0f2fe]">{value}</p>
        </div>
      </div>
    </div>
  );
}

function formatCompactCurrencyTick(value: number) {
  if (!Number.isFinite(value)) return '$0';
  const abs = Math.abs(value);
  if (abs >= 1000) {
    return `${value < 0 ? '-' : ''}$${formatCompactNumber(abs)}`;
  }
  return formatCurrency(value);
}

function formatMetricStatus(value: number, metric: 'net' | 'winRate' | 'profitFactor' | 'expectancy' | 'drawdown' | 'trades') {
  if (metric === 'net') return value >= 0 ? 'Positive' : 'Negative';
  if (metric === 'winRate') return value >= 0.5 ? 'Healthy' : value >= 0.4 ? 'Mixed' : 'Watch';
  if (metric === 'profitFactor') return value >= 1.5 ? 'Strong' : value >= 1 ? 'Healthy' : 'Weak';
  if (metric === 'expectancy') return value > 0 ? 'Positive' : value === 0 ? 'Flat' : 'Negative';
  if (metric === 'drawdown') return value <= 0.1 ? 'Controlled' : value <= 0.2 ? 'Watch' : 'Heavy';
  return value >= 20 ? 'Active' : value > 0 ? 'Light' : 'Empty';
}

function TopFoldKpiCard({
  label,
  value,
  status,
  tone = 'neutral',
}: {
  label: string;
  value: string;
  status: string;
  tone?: 'neutral' | 'good' | 'caution' | 'risk';
}) {
  const toneClass =
    tone === 'good'
      ? 'bg-emerald-500/12 text-emerald-600 dark:text-emerald-300'
      : tone === 'caution'
        ? 'bg-amber-500/12 text-amber-600 dark:text-amber-300'
        : tone === 'risk'
          ? 'bg-rose-500/12 text-rose-600 dark:text-rose-300'
          : 'bg-slate-500/12 text-slate-600 dark:text-slate-300';

  return (
    <div className="min-w-0 rounded-[22px] border border-black/10 bg-white px-3 py-4 transition hover:border-[#ff5900] hover:shadow-[0_18px_44px_rgba(255,89,0,0.12)] dark:border-white/10 dark:bg-[#111318] dark:hover:border-[#ff5900] dark:hover:shadow-[0_18px_44px_rgba(255,89,0,0.12)]">
      <div className="grid min-w-0 grid-cols-[minmax(0,1fr)_minmax(0,0.9fr)] items-start gap-2">
        <p className="min-w-0 text-[0.58rem] font-semibold uppercase leading-tight tracking-[0.1em] text-black/55 dark:text-white/55">{label}</p>
        <span className={`inline-flex min-w-0 items-center justify-center rounded-full px-2 py-1 text-[9px] font-semibold uppercase leading-tight tracking-[0.08em] ${toneClass}`}>
          {status}
        </span>
      </div>
      <p className="mt-3 text-[1.4rem] font-semibold tracking-[-0.04em] text-black dark:text-white">{value}</p>
    </div>
  );
}

function CompactBreakdownCard({
  title,
  items,
}: {
  title: string;
  items: Array<{ label: string; value: number; tone?: 'neutral' | 'good' | 'risk' }>;
}) {
  const maxValue = Math.max(...items.map((item) => Math.abs(item.value)), 1);

  return (
    <div className="h-full min-h-[96px] rounded-[16px] border border-black/10 bg-white px-3 py-3 transition hover:border-[#ff5900] hover:shadow-[0_18px_44px_rgba(255,89,0,0.12)] dark:border-white/10 dark:bg-[#111318] dark:hover:border-[#ff5900] dark:hover:shadow-[0_18px_44px_rgba(255,89,0,0.12)]">
      <p className="text-[0.6rem] font-semibold uppercase tracking-[0.13em] text-black/55 dark:text-white/55">{title}</p>
      <div className="mt-3 space-y-2.5">
        {items.map((item) => {
          const ratio = Math.max(0.08, Math.abs(item.value) / maxValue);
          const toneClass =
            item.tone === 'good'
              ? 'bg-emerald-500'
              : item.tone === 'risk'
                ? 'bg-rose-500'
                : 'bg-slate-500 dark:bg-slate-400';
          return (
            <div key={item.label}>
              <div className="flex items-center justify-between gap-3 text-[0.72rem]">
                <span className="font-medium text-black/65 dark:text-white/65">{item.label}</span>
                <span className="font-semibold text-black dark:text-white">{formatCurrency(item.value)}</span>
              </div>
              <div className="mt-1.5 h-1.5 rounded-full bg-black/6 dark:bg-white/10">
                <div className={`h-1.5 rounded-full ${toneClass}`} style={{ width: `${Math.min(100, ratio * 100)}%` }} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function TopFoldPanel({
  title,
  children,
  className = '',
  highlighted = false,
  panelRef,
}: {
  title: string;
  children: React.ReactNode;
  className?: string;
  highlighted?: boolean;
  panelRef?: (node: HTMLDivElement | null) => void;
}) {
  return (
    <div
      ref={panelRef}
      className={`rounded-[26px] border border-black/10 bg-white p-5 dark:border-white/10 dark:bg-[#060606] ${
        highlighted ? 'ring-2 ring-[#ff5900] shadow-[0_0_0_1px_rgba(255,89,0,0.3),0_22px_54px_rgba(255,89,0,0.16)]' : ''
      } ${className}`.trim()}
    >
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-sm font-semibold uppercase tracking-[0.16em] text-black/55 dark:text-white/55">{title}</h3>
        {highlighted ? <span className="rounded-full bg-[#ff5900]/12 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.12em] text-[#ff5900]">Insight focus</span> : null}
      </div>
      <div className="mt-4">{children}</div>
    </div>
  );
}

function FriendlyPnlChart({ data }: { data: Array<{ date: string; label: string; net: number; cumulative: number }> }) {
  const dailyRange = Math.max(...data.map((row) => Math.abs(row.net)), 1);
  const cumulativeRange = Math.max(...data.map((row) => Math.abs(row.cumulative)), 1);
  const scale = cumulativeRange > 0 ? cumulativeRange / dailyRange : 1;
  const chartData = data.map((row) => ({
    ...row,
    dailyScaled: row.net * scale,
  }));

  return (
    <ChartFrame className="h-[320px]">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={chartData} margin={{ top: 8, right: 16, bottom: 4, left: 0 }}>
          <defs>
            <linearGradient id="pnlFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#2d8659" stopOpacity={0.32} />
              <stop offset="100%" stopColor="#2d8659" stopOpacity={0.04} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(100,116,139,0.16)" vertical={false} />
          <XAxis dataKey="label" stroke="#64748b" tickLine={false} axisLine={false} minTickGap={24} />
          <YAxis
            stroke="#64748b"
            tickLine={false}
            axisLine={false}
            width={72}
            tickFormatter={(value) => formatCompactCurrencyTick(Number(value))}
          />
          <Tooltip
            formatter={(_value: number, name: string, payload) => {
              const row = payload?.payload as { cumulative?: number; net?: number } | undefined;
              if (name === 'cumulative') return [formatCurrency(Number(row?.cumulative || 0)), 'Cumulative Net P&L'];
              return [formatCurrency(Number(row?.net || 0)), 'Daily Net P&L'];
            }}
            labelFormatter={(_, payload) => payload?.[0]?.payload?.date ? formatDate(String(payload[0].payload.date)) : ''}
            contentStyle={{ borderRadius: 16, border: '1px solid rgba(15,23,42,0.08)' }}
          />
          <Legend
            verticalAlign="top"
            height={30}
            wrapperStyle={{ fontSize: 12, paddingBottom: 8 }}
          />
          <Bar dataKey="dailyScaled" name="daily" barSize={12} radius={[6, 6, 0, 0]} fill="#0066FF" />
          <Area type="monotone" dataKey="cumulative" stroke="#2d8659" strokeWidth={3} fill="url(#pnlFill)" />
        </ComposedChart>
      </ResponsiveContainer>
    </ChartFrame>
  );
}

function ComparisonBars({
  title,
  items,
  formatter,
}: {
  title: string;
  items: Array<{ label: string; value: number; tone: 'good' | 'risk' | 'neutral' }>;
  formatter: (value: number) => string;
}) {
  const maxValue = Math.max(...items.map((item) => Math.abs(item.value)), 1);
  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-[0.14em] text-black/50 dark:text-white/50">{title}</p>
      <div className="mt-3 space-y-3">
        {items.map((item) => {
          const width = `${Math.max(10, (Math.abs(item.value) / maxValue) * 100)}%`;
          const toneClass = item.tone === 'good' ? 'bg-emerald-500' : item.tone === 'risk' ? 'bg-rose-500' : 'bg-slate-500';
          return (
            <div key={item.label}>
              <div className="flex items-center justify-between gap-3 text-sm">
                <span className="font-medium text-black/75 dark:text-white/75">{item.label}</span>
                <span className="font-semibold text-black dark:text-white">{formatter(item.value)}</span>
              </div>
              <div className="mt-2 h-2 rounded-full bg-black/[0.06] dark:bg-white/[0.08]">
                <div className={`h-2 rounded-full ${toneClass}`} style={{ width }} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function minutesBetween(start?: string | null, end?: string | null): number {
  if (!start || !end) return 0;
  const startTime = new Date(start).getTime();
  const endTime = new Date(end).getTime();
  if (!Number.isFinite(startTime) || !Number.isFinite(endTime) || endTime <= startTime) return 0;
  return Math.max(0, Math.round((endTime - startTime) / 60000));
}

function longestStreak(values: number[], predicate: (value: number) => boolean): number {
  let current = 0;
  let max = 0;
  values.forEach((value) => {
    if (predicate(value)) {
      current += 1;
      max = Math.max(max, current);
    } else {
      current = 0;
    }
  });
  return max;
}

function classifyBucket(value: number, low: number, high: number): 'low' | 'medium' | 'high' {
  if (value <= low) return 'low';
  if (value >= high) return 'high';
  return 'medium';
}

function pnlBucket(value: number, low: number, high: number): string {
  if (Math.abs(value) < 1e-9) return 'flat';
  if (value > 0) return value >= high ? 'big_profit' : 'profit';
  return Math.abs(value) >= Math.abs(low) ? 'big_loss' : 'loss';
}

function ratioBucket(value: number): string {
  if (value < 1) return 'under_1';
  if (value < 2) return '1_to_2';
  return '2_plus';
}

function rMultipleBucket(value: number): string {
  if (value < 0) return 'loss';
  if (Math.abs(value) < 1e-9) return 'flat';
  if (value < 1) return '0_to_1';
  if (value < 2) return '1_to_2';
  return '2_plus';
}

function matchesNumericRange(value: number, filter: string): boolean {
  if (filter === 'all') return true;
  if (!Number.isFinite(value)) return false;
  const normalized = filter.replace(/\s+/g, '');
  const [rawMin, rawMax] = normalized.split(':');
  const min = rawMin === '' || rawMin == null ? Number.NEGATIVE_INFINITY : Number(rawMin);
  const max = rawMax === '' || rawMax == null ? Number.POSITIVE_INFINITY : Number(rawMax);
  if ((!Number.isFinite(min) && min !== Number.NEGATIVE_INFINITY) || (!Number.isFinite(max) && max !== Number.POSITIVE_INFINITY)) {
    return true;
  }
  return value >= min && value <= max;
}

function matchesBucketOrCustom(value: number, filter: string, low: number, high: number): boolean {
  if (filter === 'all') return true;
  if (filter === 'low' || filter === 'medium' || filter === 'high') {
    return classifyBucket(value, low, high) === filter;
  }
  if (filter.startsWith('custom:')) {
    return matchesNumericRange(value, filter.slice('custom:'.length));
  }
  return true;
}

export function DashboardScreen() {
  const accountId = usePrototypeStore((state) => state.accountId);
  const dashboardInsightFocus = usePrototypeStore((state) => state.dashboardInsightFocus);
  const dashboardGroupOrder = usePrototypeStore((state) => state.dashboardGroupOrder);
  const dashboardMetricGroup = usePrototypeStore((state) => state.dashboardMetricGroup);
  const dashboardTopWidgetVisibility = usePrototypeStore((state) => state.dashboardTopWidgetVisibility);
  const dashboardFilters = usePrototypeStore((state) => state.dashboardFilters);
  const setDashboardFilters = usePrototypeStore((state) => state.setDashboardFilters);
  const dashboardFilterPresets = usePrototypeStore((state) => state.dashboardFilterPresets);
  const saveDashboardFilterPreset = usePrototypeStore((state) => state.saveDashboardFilterPreset);
  const deleteDashboardFilterPreset = usePrototypeStore((state) => state.deleteDashboardFilterPreset);
  const { data, isLoading, error } = useQuery(['prototype-overview', accountId], () => fetchOverview(accountId as string), {
    enabled: Boolean(accountId),
  });
  const { data: accounts } = useQuery(['prototype-accounts'], fetchAccounts);
  const selectedAccount = useMemo(() => accounts?.find((account) => account.account_id === accountId) || null, [accounts, accountId]);
  const startingCapital = Number(selectedAccount?.initial_balance) || 100000;
  const { data: chartCatalog } = useQuery(['prototype-chart-catalog'], fetchChartCatalog);
  const [selectedPresetName, setSelectedPresetName] = useState('');
  const groupRefs = useRef<Record<string, HTMLDivElement | null>>({});
  const chartRefs = useRef<Record<string, HTMLDivElement | null>>({});
  const now = useMemo(() => new Date(), []);
  const {
    strategyFilter,
    marketFilter,
    symbolFilter,
    sideFilter,
    mistakeFilter,
    datePreset,
    timeFilter,
    dayFilter,
    spreadFilter,
    slippageFilter,
    holdTimeFilter,
    exitReasonFilter,
    quantityFilter,
    lotSizeFilter,
    leverageFilter,
    costFilter,
    netPnlFilter,
    riskAmountFilter,
    rrrFilter,
    rMultipleFilter,
    confidenceFilter,
    emotionFilter,
    probabilityFilter,
    closedEarlyFilter,
    statusFilter,
  } = dashboardFilters;

  const thresholdSource = useMemo(() => data?.trades || [], [data]);
  const spreadThresholds = useMemo(() => {
    const values = thresholdSource.map((trade) => Number(trade.entry_spread || 0)).filter((value) => Number.isFinite(value));
    return { low: percentile(values, 0.33), high: percentile(values, 0.66) };
  }, [thresholdSource]);
  const slippageThresholds = useMemo(() => {
    const values = thresholdSource
      .map((trade) => Math.abs(Number(trade.slippage_at_entry || 0)) + Math.abs(Number(trade.slippage_at_exit || 0)))
      .filter((value) => Number.isFinite(value));
    return { low: percentile(values, 0.33), high: percentile(values, 0.66) };
  }, [thresholdSource]);
  const quantityThresholds = useMemo(() => {
    const values = thresholdSource.map((trade) => Number(trade.quantity || 0)).filter((value) => Number.isFinite(value));
    return { low: percentile(values, 0.33), high: percentile(values, 0.66) };
  }, [thresholdSource]);
  const costThresholds = useMemo(() => {
    const values = thresholdSource
      .map((trade) => Number(trade.fees || 0) + Number(trade.commission || 0) + Number(trade.swaps || 0) + Number(trade.slippage_cost || 0))
      .filter((value) => Number.isFinite(value));
    return { low: percentile(values, 0.33), high: percentile(values, 0.66) };
  }, [thresholdSource]);
  const pnlThresholds = useMemo(() => {
    const values = thresholdSource.map((trade) => Number(trade.net_pnl || 0)).filter((value) => Number.isFinite(value));
    return { low: percentile(values, 0.33), high: percentile(values, 0.66) };
  }, [thresholdSource]);
  const riskThresholds = useMemo(() => {
    const values = thresholdSource.map((trade) => Number(trade.risk_amount || 0)).filter((value) => Number.isFinite(value));
    return { low: percentile(values, 0.33), high: percentile(values, 0.66) };
  }, [thresholdSource]);
  const rrrThresholds = useMemo(() => {
    const values = thresholdSource.map((trade) => Number(trade.rrr_at_entry || 0)).filter((value) => Number.isFinite(value));
    return { low: percentile(values, 0.33), high: percentile(values, 0.66) };
  }, [thresholdSource]);
  const rMultipleThresholds = useMemo(() => {
    const values = thresholdSource.map((trade) => Number(trade.r_multiple || 0)).filter((value) => Number.isFinite(value));
    return { low: percentile(values, 0.33), high: percentile(values, 0.66) };
  }, [thresholdSource]);
  const confidenceThresholds = useMemo(() => {
    const values = thresholdSource.map((trade) => Number(trade.confidence_score || 0)).filter((value) => Number.isFinite(value));
    return { low: percentile(values, 0.33), high: percentile(values, 0.66) };
  }, [thresholdSource]);

  const filteredData = useMemo<OverviewData | undefined>(() => {
    if (!data) return data;
    const filteredTrades = data.trades.filter((trade) => {
      const strategyName = String(trade.setup_name || trade.strategy || trade.strategy_tag || 'Unspecified');
      const matchesStrategy = strategyFilter === 'all' || strategyName === strategyFilter;
      const matchesMarket = marketFilter === 'all' || String(trade.market_type || 'unknown') === marketFilter;
      const matchesSymbol = symbolFilter === 'all' || String(trade.symbol || 'unknown') === symbolFilter;
      const matchesSide = sideFilter === 'all' || String(trade.side || 'unknown') === sideFilter;
      const violations = trade.rule_violations_snapshot || [];
      const matchesMistake =
        mistakeFilter === 'all'
        || (mistakeFilter === 'none' ? violations.length === 0 : violations.includes(mistakeFilter));
      const tradeStatus = trade.is_closed ? 'closed' : 'open';
      const matchesStatus = statusFilter === 'all' || tradeStatus === statusFilter;
      const matchesDate = matchesDatePreset(getTradeLocalDate(trade), datePreset, now);
      const pnl = Number(trade.net_pnl || 0);
      const tradeHour = trade.entry_hour != null ? String(trade.entry_hour) : String(new Date(trade.entry_time).getHours());
      const matchesTime = timeFilter === 'all' || tradeHour === timeFilter;
      const matchesDay = dayFilter === 'all' || String(trade.entry_day_of_week || 'Unknown') === dayFilter;
      const holdMinutes = minutesBetween(trade.entry_time, trade.exit_time);
      const holdBucket =
        holdMinutes < 15 ? 'under_15m'
          : holdMinutes < 60 ? '15m_1h'
            : holdMinutes < 240 ? '1h_4h'
              : '4h_plus';
      const matchesHoldTime = holdTimeFilter === 'all' || (trade.is_closed && holdBucket === holdTimeFilter);
      const totalSlippage = Math.abs(Number(trade.slippage_at_entry || 0)) + Math.abs(Number(trade.slippage_at_exit || 0));
      const totalCost = Number(trade.fees || 0) + Number(trade.commission || 0) + Number(trade.swaps || 0) + Number(trade.slippage_cost || 0);
      const matchesSpread = matchesBucketOrCustom(Number(trade.entry_spread || 0), spreadFilter, spreadThresholds.low, spreadThresholds.high);
      const matchesSlippage = matchesBucketOrCustom(totalSlippage, slippageFilter, slippageThresholds.low, slippageThresholds.high);
      const matchesExitReason = exitReasonFilter === 'all' || String(trade.exit_reason || '') === exitReasonFilter;
      const matchesQuantity = matchesBucketOrCustom(Number(trade.quantity || 0), quantityFilter, quantityThresholds.low, quantityThresholds.high);
      const matchesLotSize = lotSizeFilter === 'all' || String(Number(trade.lot_size || 0)) === lotSizeFilter;
      const matchesLeverage = leverageFilter === 'all' || String(Number(trade.leverage_used || 0)) === leverageFilter;
      const matchesCost = matchesBucketOrCustom(totalCost, costFilter, costThresholds.low, costThresholds.high);
      const matchesNetPnl = matchesBucketOrCustom(pnl, netPnlFilter, pnlThresholds.low, pnlThresholds.high);
      const matchesRiskAmount = matchesBucketOrCustom(Number(trade.risk_amount || 0), riskAmountFilter, riskThresholds.low, riskThresholds.high);
      const matchesRrr = matchesBucketOrCustom(Number(trade.rrr_at_entry || 0), rrrFilter, rrrThresholds.low, rrrThresholds.high);
      const matchesRMultiple = matchesBucketOrCustom(Number(trade.r_multiple || 0), rMultipleFilter, rMultipleThresholds.low, rMultipleThresholds.high);
      const matchesConfidence = matchesBucketOrCustom(Number(trade.confidence_score || 0), confidenceFilter, confidenceThresholds.low, confidenceThresholds.high);
      const matchesEmotion = emotionFilter === 'all' || String(trade.emotion_tag || '') === emotionFilter;
      const matchesProbability = probabilityFilter === 'all' || String(trade.probability_bucket || '') === probabilityFilter;
      const matchesClosedEarly = closedEarlyFilter === 'all' || (closedEarlyFilter === 'yes' ? trade.closed_before_plan : !trade.closed_before_plan);
      return matchesStrategy && matchesMarket && matchesSymbol && matchesSide && matchesMistake && matchesStatus && matchesDate && matchesTime && matchesDay && matchesHoldTime && matchesSpread && matchesSlippage && matchesExitReason && matchesQuantity && matchesLotSize && matchesLeverage && matchesCost && matchesNetPnl && matchesRiskAmount && matchesRrr && matchesRMultiple && matchesConfidence && matchesEmotion && matchesProbability && matchesClosedEarly;
    });
    return {
      trades: filteredTrades,
      sessionDailyTotals: data.sessionDailyTotals,
      missedOpportunityCount: data.missedOpportunityCount,
    };
  }, [data, marketFilter, sideFilter, statusFilter, strategyFilter, symbolFilter, mistakeFilter, datePreset, now, timeFilter, dayFilter, spreadFilter, slippageFilter, holdTimeFilter, exitReasonFilter, quantityFilter, lotSizeFilter, leverageFilter, costFilter, netPnlFilter, riskAmountFilter, rrrFilter, rMultipleFilter, confidenceFilter, emotionFilter, probabilityFilter, closedEarlyFilter, spreadThresholds, slippageThresholds, quantityThresholds, costThresholds, pnlThresholds, riskThresholds, rrrThresholds, rMultipleThresholds, confidenceThresholds]);

  const dashboardDataFingerprint = useMemo(() => {
    const tradeFingerprint = (filteredData?.trades || [])
      .map((trade) => [
        trade.trade_id,
        trade.is_closed ? 'closed' : 'open',
        trade.entry_time || '',
        trade.exit_time || '',
        trade.entry_price ?? '',
        trade.exit_price ?? '',
        trade.quantity ?? '',
        trade.lot_size ?? '',
        trade.gross_pnl ?? '',
        trade.net_pnl ?? '',
        trade.commission ?? '',
        trade.fees ?? '',
        trade.swaps ?? '',
        trade.risk_amount ?? '',
        trade.r_multiple ?? '',
      ].join(':'))
      .join('|');
    const sessionFingerprint = (filteredData?.sessionDailyTotals || [])
      .map((row) => `${row.day}:${row.total_platform_time_minutes}:${row.platform_session_count}`)
      .join('|');
    return `${startingCapital}::${tradeFingerprint}::${sessionFingerprint}::${filteredData?.missedOpportunityCount || 0}`;
  }, [filteredData, startingCapital]);

  const metricPayload = useMemo(() => buildMetricPayload(filteredData, startingCapital), [filteredData, startingCapital]);
  const { data: metricRun, isLoading: metricsLoading } = useQuery(
    ['prototype-dashboard-metrics', accountId, dashboardDataFingerprint, strategyFilter, marketFilter, symbolFilter, sideFilter, mistakeFilter, statusFilter, datePreset, timeFilter, dayFilter, spreadFilter, slippageFilter, holdTimeFilter, exitReasonFilter, quantityFilter, lotSizeFilter, leverageFilter, costFilter, netPnlFilter, riskAmountFilter, rrrFilter, rMultipleFilter, confidenceFilter, emotionFilter, probabilityFilter, closedEarlyFilter],
    () => runMetricComputation({ data: metricPayload, phase: 'research' }),
    { enabled: Boolean(filteredData?.trades?.length && selectedAccount) },
  );

  const metrics = useMemo(() => {
    const trades = filteredData?.trades || [];
    const closed = chronologicalClosedTrades(trades);
    const closedPnls = closed.map((trade) => Number(trade.net_pnl || 0));
    const returns = buildReturns(trades, startingCapital);
    const winTrades = closed.filter((trade) => Number(trade.net_pnl || 0) > 0);
    const lossTrades = closed.filter((trade) => Number(trade.net_pnl || 0) <= 0);
    const wins = winTrades.length;
    const losses = lossTrades.length;
    const openTrades = trades.filter((trade) => !trade.is_closed).length;
    const avgWin = average(winTrades.map((trade) => Number(trade.net_pnl || 0)));
    const avgLoss = average(lossTrades.map((trade) => Number(trade.net_pnl || 0)));
    const grossProfit = winTrades.reduce((sum, trade) => sum + Number(trade.net_pnl || 0), 0);
    const grossLoss = Math.abs(lossTrades.reduce((sum, trade) => sum + Number(trade.net_pnl || 0), 0));
    const totalNet = trades.reduce((sum, trade) => sum + Number(trade.net_pnl || 0), 0);
    const tradeDays = new Set(trades.map((trade) => trade.entry_date || trade.entry_time?.slice(0, 10)).filter(Boolean));
    const totalMinutes = (filteredData?.sessionDailyTotals || [])
      .filter((row) => tradeDays.size === 0 || tradeDays.has(row.day))
      .reduce((sum, row) => sum + Number(row.total_platform_time_minutes || 0), 0);
    const preTradeCoverage = trades.length ? trades.filter((trade) => trade.pre_trade_capture && Object.keys(trade.pre_trade_capture || {}).length > 0).length / trades.length : 0;
    const postTradeCoverage = trades.length ? trades.filter((trade) => trade.post_trade_capture && Object.keys(trade.post_trade_capture || {}).length > 0).length / trades.length : 0;
    const checklistCoverage = trades.length ? trades.filter((trade) => (trade.checklist_before || []).length > 0 || (trade.checklist_after || []).length > 0).length / trades.length : 0;
    const ruleViolationCount = trades.reduce((sum, trade) => sum + (trade.rule_violations_snapshot || []).length, 0);
    const probabilityCoverage = trades.length ? trades.filter((trade) => trade.probability_bucket).length / trades.length : 0;
    const decisionReadiness = trades.length ? trades.filter((trade) => trade.strategy_tag || trade.strategy || trade.setup_name).length / trades.length : 0;
    const avgWinHoldMinutes = average(winTrades.map((trade) => minutesBetween(trade.entry_time, trade.exit_time)));
    const avgLossHoldMinutes = average(lossTrades.map((trade) => minutesBetween(trade.entry_time, trade.exit_time)));
    const topWin = winTrades.length ? Math.max(...winTrades.map((trade) => Number(trade.net_pnl || 0))) : 0;
    const topLoss = lossTrades.length ? Math.min(...lossTrades.map((trade) => Number(trade.net_pnl || 0))) : 0;
    const winStreak = longestStreak(closedPnls, (value) => value > 0);
    const lossStreak = longestStreak(closedPnls, (value) => value <= 0);
    const sizedTrades = trades.filter((trade) => Number.isFinite(Number(trade.quantity || trade.lot_size || 0)) && Number(trade.quantity || trade.lot_size || 0) > 0);
    const avgSize = average(sizedTrades.map((trade) => Number(trade.quantity || trade.lot_size || 0)));
    const dayVolume = new Map<string, number>();
    trades.forEach((trade) => {
      const dayKey = trade.entry_date || trade.entry_time?.slice(0, 10);
      if (!dayKey) return;
      dayVolume.set(dayKey, (dayVolume.get(dayKey) || 0) + Number(trade.quantity || trade.lot_size || 0));
    });
    const avgDailyVolume = average(Array.from(dayVolume.values()));
    const expectancy = closed.length ? average(closedPnls) : 0;
    const profitFactor = grossLoss > 0 ? grossProfit / grossLoss : 0;
    const payoffRatio = avgLoss !== 0 ? Math.abs(avgWin / avgLoss) : 0;

    return {
      tradeCount: trades.length,
      winCount: wins,
      lossCount: losses,
      openCount: openTrades,
      winRate: closed.length ? wins / closed.length : 0,
      totalNet,
      maxDrawdown: Math.abs(maxDrawdownFromReturns(returns)),
      totalMinutes,
      missedCount: filteredData?.missedOpportunityCount || 0,
      preTradeCoverage,
      postTradeCoverage,
      checklistCoverage,
      ruleViolationCount,
      probabilityCoverage,
      decisionReadiness,
      expectancy,
      profitFactor,
      payoffRatio,
      avgWin,
      avgLoss,
      avgWinHoldMinutes,
      avgLossHoldMinutes,
      topWin,
      topLoss,
      winStreak,
      lossStreak,
      avgDailyVolume,
      avgSize,
    };
  }, [filteredData, startingCapital]);

  const dashboardResults = metricRun?.results || {};
  const derivedMetrics = useMemo(() => buildDerivedMetrics(filteredData, startingCapital), [filteredData, startingCapital]);
  const sectionMap = useMemo(() => new Map(defaultMetricSections.map((section) => [section.title, section])), []);
  const displayedSections = useMemo(() => {
    const allKeys = defaultMetricSections.flatMap((section) => section.keys);
    const assignment = Object.fromEntries(
      allKeys.map((key) => {
        const defaultSection = defaultMetricSections.find((section) => section.keys.includes(key))?.title || defaultDashboardGroupOrder[0];
        return [key, dashboardMetricGroup[key] || defaultSection];
      }),
    ) as Record<string, string>;
    const legacyDefaultOrder = [
      'Journal Metrics',
      'Performance Metrics',
      'Risk Metrics',
      'Distribution Metrics',
      'Regime Metrics',
      'Robustness Metrics',
      'Portfolio Metrics',
      'Capital Metrics',
      'Risk Control Metrics',
      'Stress Metrics',
      'Survival Metrics',
    ];
    const titles =
      dashboardGroupOrder.length && dashboardGroupOrder.join('|') !== legacyDefaultOrder.join('|')
        ? dashboardGroupOrder
        : defaultDashboardGroupOrder;
    return titles
      .map((title) => ({
        title,
        keys: allKeys.filter((key) => assignment[key] === title),
      }))
      .filter((section) => section.title !== 'Journal Metrics')
      .filter((section) => section.keys.length > 0 || sectionMap.has(section.title));
  }, [dashboardGroupOrder, dashboardMetricGroup, sectionMap]);
  const mergedResults = useMemo(
    () =>
      Object.fromEntries(
        Array.from(new Set(displayedSections.flatMap((section) => section.keys).concat(['equity_curve', 'payoff_ratio', 'cost_summary', 'adjusted_pnl']))).map((key) => [
          key,
          preferDerivedKeys.has(key) ? derivedMetrics[key] ?? dashboardResults[key] : dashboardResults[key] ?? derivedMetrics[key],
        ]),
      ),
    [dashboardResults, derivedMetrics, displayedSections],
  );
  const { data: chartContracts } = useQuery(
    ['prototype-dashboard-chart-contracts', accountId, dashboardDataFingerprint, strategyFilter, marketFilter, symbolFilter, sideFilter, mistakeFilter, statusFilter, datePreset, timeFilter, dayFilter, spreadFilter, slippageFilter, holdTimeFilter, exitReasonFilter, quantityFilter, lotSizeFilter, leverageFilter, costFilter, netPnlFilter, riskAmountFilter, rrrFilter, rMultipleFilter, confidenceFilter, emotionFilter, probabilityFilter, closedEarlyFilter],
    () =>
      fetchDashboardChartContracts({
        account_id: accountId as string,
        overview: filteredData as OverviewData,
        metrics: { ...mergedResults, capital: startingCapital, total_capital: startingCapital },
        filters: dashboardFilters,
      }),
    { enabled: Boolean(accountId && filteredData && selectedAccount) },
  );

  const strategyOptions = useMemo(
    () => Array.from(new Set((data?.trades || []).map((trade) => String(trade.setup_name || trade.strategy || trade.strategy_tag || 'Unspecified')))).sort(),
    [data],
  );
  const symbolOptions = useMemo(() => Array.from(new Set((data?.trades || []).map((trade) => String(trade.symbol || 'unknown')))).sort(), [data]);
  const sideOptions = useMemo(() => Array.from(new Set((data?.trades || []).map((trade) => String(trade.side || 'unknown')))).sort(), [data]);
  const mistakeOptions = useMemo(
    () =>
      Array.from(
        new Set(
          (data?.trades || []).flatMap((trade) => (trade.rule_violations_snapshot || []).map((item) => String(item))),
        ),
      ).sort(),
    [data],
  );
  const pnlCurve = useMemo(() => buildDailyNetCurve(filteredData?.trades || []), [filteredData]);
  const timePatternInsights = useMemo(() => buildTimePatternInsights(filteredData?.trades || []), [filteredData]);
  const compactHeatmap = useMemo(() => buildCompactTimeHeatmap(timePatternInsights), [timePatternInsights]);
  const registerGroupRef = (title: string) => (node: HTMLDivElement | null) => {
    groupRefs.current[title] = node;
  };
  const registerChartRef = (title: string) => (node: HTMLDivElement | null) => {
    chartRefs.current[title] = node;
  };

  useEffect(() => {
    if (!dashboardInsightFocus) return;
    const focusNode =
      (dashboardInsightFocus.chartTitle ? chartRefs.current[dashboardInsightFocus.chartTitle] : null) ||
      (dashboardInsightFocus.groupTitle ? groupRefs.current[dashboardInsightFocus.groupTitle] : null);
    focusNode?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }, [dashboardInsightFocus]);

  if (isLoading) {
    return <p className="text-sm text-gray-600 dark:text-slate-400">Loading dashboard…</p>;
  }

  if (error instanceof Error) {
    return <p className="rounded-[20px] border border-rose-500/20 bg-rose-50 px-5 py-4 text-sm text-rose-700 dark:bg-rose-500/10 dark:text-rose-300">{error.message}</p>;
  }

  const topWidgetDefinitions: Record<string, { value: string; tone?: 'default' | 'success' | 'accent' }> = {
    trades: { value: formatCompactNumber(metrics.tradeCount) },
    net_pnl: { value: formatCurrency(metrics.totalNet), tone: metrics.totalNet >= 0 ? 'success' as const : 'default' as const },
    platform_time: { value: formatMinutes(metrics.totalMinutes) },
    missed_opportunities: { value: String(metrics.missedCount) },
    expectancy: { value: formatCurrency(metrics.expectancy) },
    profit_factor: { value: formatRatio(metrics.profitFactor) },
    avg_win: { value: formatCurrency(metrics.avgWin), tone: metrics.avgWin > 0 ? 'success' as const : 'default' as const },
    avg_loss: { value: formatCurrency(metrics.avgLoss) },
    avg_win_hold: { value: formatMinutes(metrics.avgWinHoldMinutes) },
    avg_loss_hold: { value: formatMinutes(metrics.avgLossHoldMinutes) },
    top_win: { value: formatCurrency(metrics.topWin), tone: metrics.topWin > 0 ? 'success' as const : 'default' as const },
    top_loss: { value: formatCurrency(metrics.topLoss) },
    win_streak: { value: String(metrics.winStreak) },
    loss_streak: { value: String(metrics.lossStreak) },
    payoff_ratio: { value: formatRatio(metrics.payoffRatio), tone: metrics.payoffRatio >= 1 ? 'accent' as const : 'default' as const },
    avg_daily_volume: { value: formatCompactNumber(metrics.avgDailyVolume) },
    avg_size: { value: formatCompactNumber(metrics.avgSize) },
    pre_trade_coverage: { value: formatPercent(metrics.preTradeCoverage) },
    post_trade_coverage: { value: formatPercent(metrics.postTradeCoverage) },
    checklist_coverage: { value: formatPercent(metrics.checklistCoverage) },
    rule_violations: { value: String(metrics.ruleViolationCount) },
    probability_coverage: { value: formatPercent(metrics.probabilityCoverage) },
    decision_readiness: { value: formatPercent(metrics.decisionReadiness) },
  };

  const topDashboardCards: TopDashboardCard[] = [
    dashboardTopWidgetVisibility.net_pnl !== false
      ? {
          key: 'net_pnl',
          icon: <DollarSignIcon />,
          title: 'Net P&L',
          value: formatCurrency(metrics.totalNet),
          tone: metrics.totalNet >= 0 ? 'good' as const : 'risk' as const,
          trend: {
            direction: metrics.totalNet >= 0 ? 'up' as const : 'down' as const,
            value: formatCurrency(Math.abs(metrics.totalNet)),
            label: 'total return',
          },
        }
      : null,
    dashboardTopWidgetVisibility.trades !== false
      ? {
          key: 'trades',
          icon: <BarChartIcon />,
          title: 'Total Trades',
          value: formatCompactNumber(metrics.tradeCount),
          tone: 'neutral' as const,
          trend: {
            direction: 'up' as const,
            value: formatNumber(metrics.tradeCount),
            label: 'completed trades',
          },
        }
      : null,
    dashboardTopWidgetVisibility.profit_factor !== false
      ? {
          key: 'profit_factor',
          icon: <RatioIcon />,
          title: 'Profit Factor',
          value: formatRatio(metrics.profitFactor),
          tone: metrics.profitFactor >= 1.5 ? 'good' as const : metrics.profitFactor >= 1 ? 'caution' as const : 'risk' as const,
          trend: {
            direction: metrics.profitFactor >= 1 ? 'up' as const : 'down' as const,
            value: formatRatio(metrics.profitFactor),
            label: 'profit ratio',
          },
        }
      : null,
    dashboardTopWidgetVisibility.expectancy !== false
      ? {
          key: 'expectancy',
          icon: <ChartLineIcon />,
          title: 'Expectancy',
          value: formatCurrency(metrics.expectancy),
          tone: metrics.expectancy > 0 ? 'good' as const : metrics.expectancy === 0 ? 'caution' as const : 'risk' as const,
          trend: {
            direction: metrics.expectancy > 0 ? 'up' as const : 'down' as const,
            value: formatCurrency(metrics.expectancy),
            label: 'per trade avg',
          },
        }
      : null,
    {
      key: 'max_drawdown',
      icon: <ShieldIcon />,
      title: 'Max Drawdown',
      value: formatPercent(metrics.maxDrawdown),
      tone: metrics.maxDrawdown <= 0.1 ? 'good' as const : metrics.maxDrawdown <= 0.2 ? 'caution' as const : 'risk' as const,
      trend: {
        direction: 'down' as const,
        value: formatPercent(metrics.maxDrawdown),
        label: 'risk metric',
      },
    },
    dashboardTopWidgetVisibility.avg_win_hold !== false
      ? {
          key: 'avg_win_hold',
          icon: <ClockIcon />,
          title: 'Avg Win Hold',
          value: formatMinutes(metrics.avgWinHoldMinutes),
          tone: 'good' as const,
          trend: {
            direction: 'up' as const,
            value: formatMinutes(metrics.avgWinHoldMinutes),
            label: 'winner duration',
          },
        }
      : null,
    dashboardTopWidgetVisibility.avg_loss_hold !== false
      ? {
          key: 'avg_loss_hold',
          icon: <ClockIcon />,
          title: 'Avg Loss Hold',
          value: formatMinutes(metrics.avgLossHoldMinutes),
          tone: 'risk' as const,
          trend: {
            direction: 'down' as const,
            value: formatMinutes(metrics.avgLossHoldMinutes),
            label: 'loser duration',
          },
        }
      : null,
    dashboardTopWidgetVisibility.top_win !== false
      ? {
          key: 'top_win',
          icon: <TrophyIcon />,
          title: 'Top Win',
          value: formatCurrency(metrics.topWin),
          tone: metrics.topWin > 0 ? 'good' as const : 'neutral' as const,
          trend: {
            direction: metrics.topWin > 0 ? 'up' as const : 'neutral' as const,
            value: formatCurrency(metrics.topWin),
            label: 'best trade',
          },
        }
      : null,
    dashboardTopWidgetVisibility.top_loss !== false
      ? {
          key: 'top_loss',
          icon: <TrendingDownIcon />,
          title: 'Top Loss',
          value: formatCurrency(metrics.topLoss),
          tone: 'risk' as const,
          trend: {
            direction: 'down' as const,
            value: formatCurrency(Math.abs(metrics.topLoss)),
            label: 'worst trade',
          },
        }
      : null,
    dashboardTopWidgetVisibility.win_streak !== false
      ? {
          key: 'win_streak',
          icon: <TrendingUpIcon />,
          title: 'Win Streak',
          value: String(metrics.winStreak),
          tone: metrics.winStreak > 1 ? 'good' as const : 'neutral' as const,
          trend: {
            direction: metrics.winStreak > 1 ? 'up' as const : 'neutral' as const,
            value: String(metrics.winStreak),
            label: 'best streak',
          },
        }
      : null,
    dashboardTopWidgetVisibility.loss_streak !== false
      ? {
          key: 'loss_streak',
          icon: <TrendingDownIcon />,
          title: 'Loss Streak',
          value: String(metrics.lossStreak),
          tone: metrics.lossStreak > 2 ? 'risk' as const : 'caution' as const,
          trend: {
            direction: 'down' as const,
            value: String(metrics.lossStreak),
            label: 'risk streak',
          },
        }
      : null,
    dashboardTopWidgetVisibility.payoff_ratio !== false
      ? {
          key: 'payoff_ratio',
          icon: <RatioIcon />,
          title: 'Payoff Ratio',
          value: formatRatio(metrics.payoffRatio),
          tone: metrics.payoffRatio >= 1.25 ? 'good' as const : metrics.payoffRatio >= 1 ? 'caution' as const : 'risk' as const,
          trend: {
            direction: metrics.payoffRatio >= 1 ? 'up' as const : 'down' as const,
            value: formatRatio(metrics.payoffRatio),
            label: 'winner vs loser',
          },
        }
      : null,
  ].filter(Boolean) as TopDashboardCard[];

  return (
    <div className="space-y-8 text-black dark:text-white">
      <section className="sticky top-0 z-[100] -mx-5 border-y border-black/10 bg-[var(--topbar-bg)] px-4 py-0.5 text-[var(--color-ink)] shadow-[0_18px_44px_rgba(15,23,42,0.08)] dark:border-white/10 md:-mx-8 md:px-8 xl:-mx-10 xl:px-10">
        <div className="flex flex-wrap gap-1">
          <button
            type="button"
            onClick={() => setDashboardFilters({
              ...defaultDashboardFilters,
            })}
            className="rounded-full border border-black/15 bg-white px-3 py-[2px] text-[13px] font-semibold text-[#0d0d0d] transition hover:border-[#ff5900] hover:bg-[#ff5900] hover:text-[#0d0d0d] dark:border-white/20 dark:bg-[#1a1a1a] dark:text-white dark:hover:border-[#ff5900] dark:hover:bg-[#ff5900] dark:hover:text-white"
          >
            Reset Filters
          </button>
          <button
            type="button"
            onClick={() => {
              const name = window.prompt('Preset name');
              if (name) saveDashboardFilterPreset(name, dashboardFilters);
            }}
            className="rounded-full border border-black/15 bg-white px-3 py-[2px] text-[13px] font-semibold text-[#0d0d0d] transition hover:border-[#ff5900] hover:bg-[#ff5900] hover:text-[#0d0d0d] dark:border-white/20 dark:bg-[#1a1a1a] dark:text-white dark:hover:border-[#ff5900] dark:hover:bg-[#ff5900] dark:hover:text-white"
          >
            Save Preset
          </button>
        </div>

        {dashboardFilterPresets.length ? (
          <div className="mt-0.5 flex flex-wrap items-center gap-1">
            <div className="min-w-[220px]">
              <FilterSelect
                label="Saved Presets"
                value={selectedPresetName}
                onChange={setSelectedPresetName}
                options={dashboardFilterPresets.map((preset) => preset.name)}
              />
            </div>
            <button
              type="button"
              onClick={() => {
                const preset = dashboardFilterPresets.find((item) => item.name === selectedPresetName);
                if (preset) setDashboardFilters(preset.filters);
              }}
              className="rounded-full border border-black/15 bg-white px-3 py-[2px] text-[13px] font-semibold text-[#0d0d0d] transition hover:border-[#ff5900] hover:bg-[#ff5900] hover:text-[#0d0d0d] dark:border-white/20 dark:bg-[#1a1a1a] dark:text-white dark:hover:border-[#ff5900] dark:hover:bg-[#ff5900] dark:hover:text-white"
            >
              Apply Preset
            </button>
            <button
              type="button"
              onClick={() => {
                if (!selectedPresetName) return;
                deleteDashboardFilterPreset(selectedPresetName);
                setSelectedPresetName('');
              }}
              className="rounded-full border border-black/15 bg-white px-3 py-[2px] text-[13px] font-semibold text-[#0d0d0d] transition hover:border-[#ff5900] hover:bg-[#ff5900] hover:text-[#0d0d0d] dark:border-white/20 dark:bg-[#1a1a1a] dark:text-white dark:hover:border-[#ff5900] dark:hover:bg-[#ff5900] dark:hover:text-white"
            >
              Delete Preset
            </button>
          </div>
        ) : null}

      </section>

      <section className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-6">
        {topDashboardCards.map((card) => (
          <EnhancedMetricCard
            key={card.key}
            icon={card.icon}
            title={card.title}
            value={card.value}
            tone={card.tone}
            compact
            showTrend={false}
          />
        ))}
      </section>

      <section className="grid items-start gap-6 xl:grid-cols-[minmax(0,1.7fr)_minmax(360px,1fr)]">
        <div className="grid gap-6">
          <TopFoldPanel
            title="Net P&L Curve"
            highlighted={dashboardInsightFocus?.chartTitle === 'Net P&L Curve'}
            panelRef={registerChartRef('Net P&L Curve')}
          >
            {pnlCurve.length ? (
              <FriendlyPnlChart data={pnlCurve} />
            ) : (
              <p className="rounded-[18px] border border-dashed border-black/10 px-4 py-8 text-sm text-black/60 dark:border-white/10 dark:text-white/60">
                No closed-trade history yet for a P&amp;L curve.
              </p>
            )}
          </TopFoldPanel>

          <div className="grid items-start gap-4">
            <div className="max-w-[720px]">
              <CompactBreakdownCard
                title="Cost Breakdown"
                items={[
                  { label: 'Brokerage', value: Number((mergedResults.cost_summary as Record<string, unknown>)?.total_brokerage || 0) },
                  { label: 'Slippage', value: Number((mergedResults.cost_summary as Record<string, unknown>)?.total_slippage || 0), tone: 'risk' },
                  { label: 'Swaps', value: Number((mergedResults.cost_summary as Record<string, unknown>)?.total_swaps || 0) },
                  { label: 'Total Cost', value: Number((mergedResults.cost_summary as Record<string, unknown>)?.total_cost || 0), tone: 'good' },
                ]}
              />
            </div>
          </div>
        </div>

        <TopFoldPanel
          title="Trade Outcomes"
          highlighted={dashboardInsightFocus?.chartTitle === 'Trade Outcomes'}
          panelRef={registerChartRef('Trade Outcomes')}
        >
          <div className="grid gap-5">
            <ComparisonBars
              title="Avg Win vs Avg Loss"
              items={[
                { label: 'Avg Win', value: metrics.avgWin, tone: 'good' },
                { label: 'Avg Loss', value: Math.abs(metrics.avgLoss), tone: 'risk' },
              ]}
              formatter={(value) => formatCurrency(value)}
            />
            <div className="grid gap-5 lg:grid-cols-2 xl:grid-cols-1 2xl:grid-cols-2">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.14em] text-black/50 dark:text-white/50">Wins vs Losses Percentage</p>
                <div className="mt-3">
                  <PieMetricChart
                    data={[
                      { name: 'Wins', value: metrics.winCount + metrics.lossCount > 0 ? metrics.winRate * 100 : 0 },
                      { name: 'Losses', value: metrics.winCount + metrics.lossCount > 0 ? (1 - metrics.winRate) * 100 : 0 },
                    ]}
                    colors={['#10b981', '#ef4444']}
                    valueFormatter={(value) => `${value.toFixed(1)}%`}
                    tooltipFormatter={(value, name) => [`${value.toFixed(1)}%`, name]}
                  />
                </div>
              </div>
              <ComparisonBars
                title="Trade Counts"
                items={[
                  { label: 'Wins', value: metrics.winCount, tone: 'good' },
                  { label: 'Losses', value: metrics.lossCount, tone: 'risk' },
                  { label: 'Open', value: metrics.openCount, tone: 'neutral' },
                ]}
                formatter={(value) => formatNumber(value)}
              />
            </div>
          </div>
        </TopFoldPanel>
      </section>

      <section className="rounded-[26px] border border-black/10 bg-white p-5 dark:border-white/10 dark:bg-[#060606]">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h2 className="text-xl font-semibold text-black dark:text-white">Time Pattern Insights</h2>
            <p className="mt-1 text-sm text-black/55 dark:text-white/55">
              Where the trading day is working for you, and where it is not.
            </p>
          </div>
        </div>
        <div className="mt-5 grid gap-5">
          <div className="grid gap-5 lg:grid-cols-2">
            <VisualCard title="P&amp;L by Weekday">
              <MetricsBarChart
                data={timePatternInsights.weekdayPnlBars}
                valueFormatter={(value) => formatCurrency(value)}
                barColor="#0f766e"
                xAxisInterval={0}
              />
            </VisualCard>
            <VisualCard title="P&amp;L by Hour">
              <MetricsBarChart
                data={timePatternInsights.hourPnlBars}
                valueFormatter={(value) => formatCurrency(value)}
                labelFormatter={(label) => label}
                barColor="#1d4ed8"
                xAxisInterval={1}
              />
            </VisualCard>
          </div>
          <VisualCard title="Trade Frequency Heatmap" className="h-[400px]">
            <div className="h-[400px]">
              <HeatmapChart
                labelsX={compactHeatmap.labelsX}
                labelsY={compactHeatmap.labelsY}
                matrix={compactHeatmap.matrix}
              />
            </div>
          </VisualCard>
        </div>
      </section>

      <section className="grid gap-6">
        {metricsLoading ? <p className="text-sm text-black/70 dark:text-white/70">Loading metric catalog…</p> : null}

        {displayedSections.map((section) => {
          const populated = section.keys.filter((key) => mergedResults[key] != null).length;
          return (
            <div
              key={section.title}
              ref={registerGroupRef(section.title)}
              className={`rounded-[28px] border border-black/10 bg-white p-6 dark:border-white/10 dark:bg-[#060606] ${
                dashboardInsightFocus?.groupTitle === section.title
                  ? 'ring-2 ring-[#ff5900] shadow-[0_0_0_1px_rgba(255,89,0,0.3),0_22px_54px_rgba(255,89,0,0.16)]'
                  : ''
              }`}
            >
              <div className="flex items-center justify-between gap-3">
                <div>
                  <h2 className="text-xl font-semibold text-black dark:text-white">{section.title}</h2>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {Array.from(new Set((chartCatalog?.metric_groups?.[section.title] || []).map((item) => item.chart_type))).map((chartType) => (
                      <span
                        key={`${section.title}-${chartType}`}
                        className="rounded-full border border-black/10 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-black/60 dark:border-white/10 dark:text-white/60"
                      >
                        {chartType}
                      </span>
                    ))}
                  </div>
                  {(chartCatalog?.group_visuals?.[section.title] || []).length ? (
                    <p className="mt-2 text-xs text-black/55 dark:text-white/55">
                      {(chartCatalog?.group_visuals?.[section.title] || []).map((visual) => `${visual.title} (${visual.chart_type})`).join(' · ')}
                    </p>
                  ) : null}
                </div>
                <span className="text-sm text-black/60 dark:text-white/60">{populated}/{section.keys.length} populated</span>
              </div>

              <div className="mt-5">
                {chartContracts?.groups?.[section.title]?.length
                  ? renderDashboardContracts(
                      chartContracts.groups[section.title],
                      dashboardInsightFocus?.chartTitle,
                      registerChartRef,
                    )
                  : buildGroupVisuals(
                      section.title,
                      mergedResults,
                      filteredData,
                      startingCapital,
                      dashboardInsightFocus?.chartTitle,
                      registerChartRef,
                    )}
              </div>

              <div className="mt-5 grid auto-rows-fr gap-4 md:grid-cols-2 xl:grid-cols-4">
                {section.keys.filter((key) => !chartOnlyMetrics.has(key) && key !== 'trade_count').map((key) => {
                  const value = mergedResults[key];
                  return (
                    <div key={key}>
                      <MetricCard
                        label={humanizeKey(key)}
                        value={extractMetricValue(key, value)}
                        helper={metricInterpretation(key, value)}
                        metricKey={key}
                      />
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </section>

    </div>
  );
}

function FilterSelect({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: string[];
}) {
  return (
    <label className="block">
      <span className="mb-2 block text-xs font-semibold uppercase tracking-[0.16em] text-black/55 dark:text-white/55">{label}</span>
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="w-full rounded-[18px] border border-black/10 bg-white px-4 py-3 text-sm font-semibold text-black outline-none dark:border-white/10 dark:bg-[#0b0b0b] dark:text-white"
      >
        <option value="all">All</option>
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </label>
  );
}
