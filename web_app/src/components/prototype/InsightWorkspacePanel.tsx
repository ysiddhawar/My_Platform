import { useMemo, useState } from 'react';
import { useQuery } from 'react-query';

import {
  fetchCalendarDayDetail,
  fetchMissedOpportunities,
  fetchOverview,
  fetchTradeBundle,
  fetchTrades,
  runMetricComputation,
  searchTrades,
} from '@/api/prototype';
import { ChartFrame } from '@/components/charts/ChartFrame';
import { GenericTimeSeriesChart } from '@/components/charts/GenericTimeSeriesChart';
import { MetricsBarChart } from '@/components/charts/MetricsBarChart';
import { PieMetricChart } from '@/components/charts/PieMetricChart';
import { CalendarDayDrawer } from '@/components/prototype/domain/CalendarDayDrawer';
import { MissedOpportunityTable } from '@/components/prototype/domain/MissedOpportunityTable';
import { TradeBundlePanel } from '@/components/prototype/domain/TradeBundlePanel';
import { TradeTable } from '@/components/prototype/domain/TradeTable';
import { usePrototypeStore } from '@/state/prototypeStore';
import type { DashboardFilterState, InsightWorkspacePanelPayload, OverviewData, TradeRecord } from '@/types/prototype';
import { formatCurrency, formatNumber, formatPercent, humanizeKey } from '@/utils/format';
import { summarizeTradeOutcomes } from '@/utils/tradeOutcome';

function EvidenceChip({ label, value, comparison }: { label: string; value: string; comparison?: string | null }) {
  return (
    <div className="rounded-[16px] border border-black/10 bg-black/[0.03] px-3 py-2 dark:border-white/10 dark:bg-white/[0.04]">
      <p className="text-[0.62rem] font-semibold uppercase tracking-[0.14em] text-black/45 dark:text-white/45">{label}</p>
      <p className="mt-1 text-sm font-semibold text-black dark:text-white">{value}</p>
      {comparison ? <p className="mt-1 text-[11px] text-black/60 dark:text-white/60">{comparison}</p> : null}
    </div>
  );
}

function FilterChip({ label }: { label: string }) {
  return (
    <span className="rounded-full border border-black/10 bg-white px-3 py-1 text-[11px] font-semibold tracking-[0.04em] text-black/70 dark:border-white/10 dark:bg-[#232323] dark:text-white/78">
      {label}
    </span>
  );
}

export function InsightWorkspacePanel() {
  const accountId = usePrototypeStore((state) => state.accountId);
  const panel = usePrototypeStore((state) => state.insightWorkspacePanel);
  const closeInsightDrilldown = usePrototypeStore((state) => state.closeInsightDrilldown);

  if (!panel) return null;

  const filterChips = buildFilterChips(panel);
  const panelInstanceKey = `${panel.target.view}:${panel.target.selectedTradeId || panel.target.selectedDay || panel.target.dashboardFocusChart || panel.target.missedOpportunitySearchText || panel.target.journalSearchText || panel.title}`;

  return (
    <aside className="sticky top-0 self-start rounded-[28px] border border-black/10 bg-[var(--page-bg)] shadow-[0_24px_60px_rgba(15,23,42,0.08)] dark:border-white/10">
      <div className="flex items-start justify-between gap-4 border-b border-black/10 px-5 py-4 dark:border-white/10">
        <div className="min-w-0">
          <p className="text-[0.65rem] font-semibold uppercase tracking-[0.18em] text-[#FF5900]">
            {panel.actionLabel || 'Insight Evidence'}
          </p>
          <h3 className="mt-2 text-[1.12rem] font-semibold tracking-[-0.03em] text-black dark:text-white">{panel.title}</h3>
          {panel.summary ? <p className="mt-2 text-sm leading-6 text-black/70 dark:text-white/70">{panel.summary}</p> : null}
        </div>
        <button
          type="button"
          onClick={closeInsightDrilldown}
          className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-black/10 bg-white text-lg font-semibold text-black transition hover:border-[#ff5900] hover:bg-[#ff5900] hover:text-white dark:border-white/10 dark:bg-[#222] dark:text-white dark:hover:border-[#ff5900] dark:hover:bg-[#ff5900]"
          aria-label="Close evidence panel"
        >
          ×
        </button>
      </div>

      <div className="max-h-[calc(100vh-7rem)] overflow-y-auto px-5 py-5">
        {panel.evidence?.length ? (
          <section>
            <p className="text-[0.65rem] font-semibold uppercase tracking-[0.18em] text-black/45 dark:text-white/45">Opened From Insight</p>
            <div className="mt-3 grid gap-2">
              {panel.evidence.map((item) => (
                <EvidenceChip key={`${item.label}-${item.value}`} label={item.label} value={item.value} comparison={item.comparison} />
              ))}
            </div>
          </section>
        ) : null}

        {filterChips.length ? (
          <section className="mt-5">
            <p className="text-[0.65rem] font-semibold uppercase tracking-[0.18em] text-black/45 dark:text-white/45">Applied Filters</p>
            <div className="mt-3 flex flex-wrap gap-2">
              {filterChips.map((chip) => (
                <FilterChip key={chip} label={chip} />
              ))}
            </div>
          </section>
        ) : null}

        <div className="mt-6">
          {panel.target.view === 'dashboard' ? <DashboardInsightPreview key={panelInstanceKey} accountId={accountId} panel={panel} /> : null}
          {panel.target.view === 'journal' ? <JournalInsightPreview key={panelInstanceKey} accountId={accountId} panel={panel} /> : null}
          {panel.target.view === 'calendar' ? <CalendarInsightPreview key={panelInstanceKey} accountId={accountId} panel={panel} /> : null}
          {panel.target.view === 'missed-opportunities' ? <MissedInsightPreview key={panelInstanceKey} accountId={accountId} panel={panel} /> : null}
          
        </div>
      </div>
    </aside>
  );
}

function DashboardInsightPreview({
  accountId,
  panel,
}: {
  accountId: string | null;
  panel: InsightWorkspacePanelPayload;
}) {
  const filters = panel.target.dashboardFiltersPatch || {};
  const focusChart = panel.target.dashboardFocusChart || defaultFocusChartForGroup(panel.target.dashboardFocusGroup);
  const { data: overview, isLoading, error } = useQuery(
    ['insight-workspace-overview', accountId],
    () => fetchOverview(accountId as string),
    { enabled: Boolean(accountId) },
  );

  const filteredOverview = useMemo(() => applyInsightDashboardFilters(overview, filters), [overview, filters]);
  const metricPayload = useMemo(() => buildMetricPayload(filteredOverview), [filteredOverview]);
  const { data: metricRun, isLoading: metricsLoading } = useQuery(
    ['insight-workspace-metrics', accountId, focusChart, JSON.stringify(filters), filteredOverview?.trades?.length],
    () => runMetricComputation({ data: metricPayload, phase: 'research' }),
    { enabled: Boolean(accountId && filteredOverview?.trades?.length) },
  );

  if (isLoading) {
    return <p className="text-sm text-black/70 dark:text-white/70">Loading dashboard evidence…</p>;
  }
  if (error instanceof Error) {
    return <p className="rounded-[20px] border border-rose-500/20 bg-rose-50 px-4 py-3 text-sm text-rose-700 dark:bg-rose-500/10 dark:text-rose-300">{error.message}</p>;
  }

  const trades = filteredOverview?.trades || [];
  const closed = trades.filter((trade) => trade.is_closed);
  const outcomeMetrics = computeOutcomeMetrics(closed, trades.length);
  const results = metricRun?.results || {};

  return (
    <div className="space-y-5">
      <div className="grid gap-3 md:grid-cols-3">
        <PreviewStat label="Trades" value={String(trades.length)} />
        <PreviewStat label="Closed Trades" value={String(closed.length)} />
        <PreviewStat label="Net P&L" value={formatCurrency(closed.reduce((sum, trade) => sum + Number(trade.net_pnl || 0), 0))} />
      </div>

      {focusChart === 'Trade Outcomes' ? (
        <div className="grid gap-4 lg:grid-cols-2">
          <PreviewPanel title="Trade Outcomes">
            <div className="grid gap-3 md:grid-cols-3">
              <PreviewStat label="Win Rate" value={formatPercent(outcomeMetrics.winRate)} />
              <PreviewStat label="Avg Win" value={formatCurrency(outcomeMetrics.avgWin)} />
              <PreviewStat label="Avg Loss" value={formatCurrency(Math.abs(outcomeMetrics.avgLoss))} />
            </div>
            <div className="mt-4 grid gap-4 lg:grid-cols-2">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-black/50 dark:text-white/50">Wins vs Losses</p>
                <div className="mt-3 h-[230px]">
                  <PieMetricChart
                    data={[
                      { name: 'Wins', value: outcomeMetrics.winCount },
                      { name: 'Losses', value: outcomeMetrics.lossCount },
                      { name: 'Open', value: outcomeMetrics.openCount },
                    ]}
                    colors={['#10b981', '#ef4444', '#64748b']}
                    valueFormatter={(value) => `${value}`}
                  />
                </div>
              </div>
              <div className="space-y-3">
                <OutcomeRow label="Wins" value={outcomeMetrics.winCount} tone="good" />
                <OutcomeRow label="Losses" value={outcomeMetrics.lossCount} tone="risk" />
                <OutcomeRow label="Open" value={outcomeMetrics.openCount} tone="neutral" />
              </div>
            </div>
          </PreviewPanel>
        </div>
      ) : null}

      {focusChart === 'Performance Snapshot' ? (
        <PreviewPanel title="Performance Snapshot">
          {metricsLoading ? (
            <p className="text-sm text-black/70 dark:text-white/70">Loading performance metrics…</p>
          ) : (
            <div className="space-y-4">
              <div className="h-[280px]">
                <MetricsBarChart
                  data={[
                    { metric: 'Sharpe', value: Number(extractScalar(results.sharpe) || 0) },
                    { metric: 'Sortino', value: Number(extractScalar(results.sortino) || 0) },
                    { metric: 'Calmar', value: Number(extractScalar(results.calmar) || 0) },
                    { metric: 'CAGR', value: Number(extractScalar(results.cagr) || 0) },
                    { metric: 'Net Sh.', value: Number(extractScalar(results.net_sharpe) || 0) },
                    { metric: 'Net So.', value: Number(extractScalar(results.net_sortino) || 0) },
                    { metric: 'Net CAGR', value: Number(extractScalar(results.net_cagr) || 0) },
                  ]}
                  tickAngle={-18}
                  tickHeight={82}
                />
              </div>
              <div className="grid gap-3 md:grid-cols-3">
                {['sharpe', 'sortino', 'calmar', 'cagr', 'net_sharpe', 'net_sortino', 'net_cagr'].map((key) => (
                  <PreviewStat key={key} label={humanizeKey(key)} value={formatNumber(Number(extractScalar(results[key]) || 0))} />
                ))}
              </div>
            </div>
          )}
        </PreviewPanel>
      ) : null}

      {focusChart === 'Rolling Sharpe' ? (
        <PreviewPanel title="Rolling Sharpe">
          {metricsLoading ? (
            <p className="text-sm text-black/70 dark:text-white/70">Loading rolling Sharpe…</p>
          ) : (
            <ChartFrame className="h-[300px]">
              <GenericTimeSeriesChart
                data={buildRollingDateSeries(trades, toNumberArray(results.rolling_sharpe), 'rolling', 'W')}
                series={[{ key: 'rolling', color: '#1d4ed8', name: 'Rolling Sharpe' }]}
                className="h-[300px]"
                xTickFormatter={formatAxisDate}
              />
            </ChartFrame>
          )}
        </PreviewPanel>
      ) : null}

      {focusChart === 'Net P&L Curve' ? (
        <PreviewPanel title="Net P&L Curve">
          <ChartFrame className="h-[300px]">
            <GenericTimeSeriesChart
              data={buildDailyNetCurve(trades).map((row) => ({ label: row.label, cumulative: row.cumulative, net: row.net }))}
              series={[
                { key: 'cumulative', color: '#2d8659', name: 'Cumulative Net P&L' },
                { key: 'net', color: '#0066FF', name: 'Daily Net P&L' },
              ]}
              className="h-[300px]"
            />
          </ChartFrame>
        </PreviewPanel>
      ) : null}

      {focusChart === 'Drawdown Curve' ? (
        <PreviewPanel title="Drawdown Curve">
          {metricsLoading ? (
            <p className="text-sm text-black/70 dark:text-white/70">Loading drawdown curve…</p>
          ) : (
            <ChartFrame className="h-[300px]">
              <GenericTimeSeriesChart
                data={buildLabeledSeries(toNumberArray(results.rolling_drawdown), 'T', 'drawdown')}
                series={[{ key: 'drawdown', color: '#b91c1c', name: 'Rolling Drawdown' }]}
                className="h-[300px]"
              />
            </ChartFrame>
          )}
        </PreviewPanel>
      ) : null}

      {!focusChart ? (
        <p className="rounded-[20px] border border-dashed border-black/10 px-4 py-5 text-sm text-black/65 dark:border-white/10 dark:text-white/65">
          No focused dashboard chart was attached to this insight yet.
        </p>
      ) : null}
    </div>
  );
}

function JournalInsightPreview({
  accountId,
  panel,
}: {
  accountId: string | null;
  panel: InsightWorkspacePanelPayload;
}) {
  const [selectedTradeId, setSelectedTradeId] = useState<string | null>(panel.target.selectedTradeId || null);
  const searchText = panel.target.journalSearchText || '';
  const { data: tradeBundle, isLoading: bundleLoading, error: bundleError } = useQuery(
    ['insight-workspace-trade-bundle', selectedTradeId],
    () => fetchTradeBundle(selectedTradeId as string),
    { enabled: Boolean(selectedTradeId) },
  );
  const { data: searchedData, isFetching: searching } = useQuery(
    ['insight-workspace-trade-search', accountId, searchText],
    () => searchTrades(accountId as string, searchText),
    { enabled: Boolean(accountId) && !selectedTradeId && searchText.trim().length >= 2 },
  );
  const { data: allTrades, isLoading: allTradesLoading, error: tradesError } = useQuery(
    ['insight-workspace-trades', accountId],
    () => fetchTrades(accountId as string),
    { enabled: Boolean(accountId) && !selectedTradeId && searchText.trim().length < 2 },
  );

  if (selectedTradeId) {
    if (bundleLoading) return <p className="text-sm text-black/70 dark:text-white/70">Loading trade detail…</p>;
    if (bundleError instanceof Error) {
      return <p className="rounded-[20px] border border-rose-500/20 bg-rose-50 px-4 py-3 text-sm text-rose-700 dark:bg-rose-500/10 dark:text-rose-300">{bundleError.message}</p>;
    }
    if (!tradeBundle?.trade) {
      return <p className="text-sm text-black/70 dark:text-white/70">No trade detail found for this insight.</p>;
    }
    return (
      <div className="space-y-4">
        <PreviewStat label="Focused Trade" value={tradeBundle.trade.trade_id?.slice(0, 8) || '—'} />
        <TradeBundlePanel bundle={tradeBundle} />
      </div>
    );
  }

  const trades = useMemo(() => {
    const raw = searchText.trim().length >= 2 ? searchedData || [] : allTrades || [];
    return [...raw].sort((a, b) => {
      const dateA = a.entry_date || a.entry_time?.slice(0, 10) || '';
      const dateB = b.entry_date || b.entry_time?.slice(0, 10) || '';
      const cmp = dateB.localeCompare(dateA);
      if (cmp !== 0) return cmp;
      const timeA = a.entry_time || '';
      const timeB = b.entry_time || '';
      return timeB.localeCompare(timeA);
    });
  }, [allTrades, searchedData, searchText]);
  if (allTradesLoading || searching) {
    return <p className="text-sm text-black/70 dark:text-white/70">Loading journal evidence…</p>;
  }
  if (tradesError instanceof Error) {
    return <p className="rounded-[20px] border border-rose-500/20 bg-rose-50 px-4 py-3 text-sm text-rose-700 dark:bg-rose-500/10 dark:text-rose-300">{tradesError.message}</p>;
  }
  return trades.length ? (
    <TradeTable trades={trades} selectedTradeId={selectedTradeId} onSelectTrade={setSelectedTradeId} />
  ) : (
    <p className="rounded-[20px] border border-dashed border-black/10 px-4 py-5 text-sm text-black/65 dark:border-white/10 dark:text-white/65">
      No journal trades matched this insight.
    </p>
  );
}

function CalendarInsightPreview({
  accountId,
  panel,
}: {
  accountId: string | null;
  panel: InsightWorkspacePanelPayload;
}) {
  const initialDay = panel.target.selectedDay || new Date().toISOString().slice(0, 10);
  const [selectedDay, setSelectedDay] = useState(initialDay);
  const { data, isLoading, error } = useQuery(
    ['insight-workspace-calendar-day', accountId, selectedDay],
    () => fetchCalendarDayDetail(selectedDay, accountId as string),
    { enabled: Boolean(accountId && selectedDay) },
  );

  const shiftDay = (delta: number) => {
    const nextDate = new Date(`${selectedDay}T00:00:00`);
    nextDate.setDate(nextDate.getDate() + delta);
    setSelectedDay(`${nextDate.getFullYear()}-${String(nextDate.getMonth() + 1).padStart(2, '0')}-${String(nextDate.getDate()).padStart(2, '0')}`);
  };

  if (error instanceof Error) {
    return <p className="rounded-[20px] border border-rose-500/20 bg-rose-50 px-4 py-3 text-sm text-rose-700 dark:bg-rose-500/10 dark:text-rose-300">{error.message}</p>;
  }

  return <CalendarDayDrawer detail={data || null} loading={isLoading} onPrevDay={() => shiftDay(-1)} onNextDay={() => shiftDay(1)} className="border-black/10 dark:border-white/10" />;
}

function MissedInsightPreview({
  accountId,
  panel,
}: {
  accountId: string | null;
  panel: InsightWorkspacePanelPayload;
}) {
  const searchText = (panel.target.missedOpportunitySearchText || '').trim().toLowerCase();
  const { data, isLoading, error } = useQuery(
    ['insight-workspace-missed-opportunities', accountId],
    () => fetchMissedOpportunities(accountId as string),
    { enabled: Boolean(accountId) },
  );

  const filtered = useMemo(() => {
    const rows = data || [];
    if (!searchText) return rows;
    return rows.filter((item) =>
      [
        item.symbol,
        item.strategy_name,
        item.market_type,
        item.notes || '',
        item.local_date,
        item.local_day_of_week,
      ]
        .join(' ')
        .toLowerCase()
        .includes(searchText),
    );
  }, [data, searchText]);

  if (isLoading) {
    return <p className="text-sm text-black/70 dark:text-white/70">Loading missed-opportunity evidence…</p>;
  }
  if (error instanceof Error) {
    return <p className="rounded-[20px] border border-rose-500/20 bg-rose-50 px-4 py-3 text-sm text-rose-700 dark:bg-rose-500/10 dark:text-rose-300">{error.message}</p>;
  }
  return filtered.length ? (
    <MissedOpportunityTable opportunities={filtered} />
  ) : (
    <p className="rounded-[20px] border border-dashed border-black/10 px-4 py-5 text-sm text-black/65 dark:border-white/10 dark:text-white/65">
      No missed opportunities matched this insight.
    </p>
  );
}

function PreviewPanel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-[24px] border border-black/10 bg-white p-4 dark:border-white/10 dark:bg-[#1f1f1f]">
      <h4 className="text-[0.75rem] font-semibold uppercase tracking-[0.16em] text-black/55 dark:text-white/55">{title}</h4>
      <div className="mt-4">{children}</div>
    </section>
  );
}

function PreviewStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[18px] border border-black/10 bg-white px-4 py-3 dark:border-white/10 dark:bg-[#202020]">
      <p className="text-[0.62rem] font-semibold uppercase tracking-[0.14em] text-black/45 dark:text-white/45">{label}</p>
      <p className="mt-2 text-[1rem] font-semibold text-black dark:text-white">{value}</p>
    </div>
  );
}

function OutcomeRow({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: 'good' | 'risk' | 'neutral';
}) {
  const color = tone === 'good' ? 'bg-emerald-500' : tone === 'risk' ? 'bg-rose-500' : 'bg-slate-500';
  return (
    <div>
      <div className="flex items-center justify-between gap-3 text-sm">
        <span className="font-medium text-black/70 dark:text-white/70">{label}</span>
        <span className="font-semibold text-black dark:text-white">{formatNumber(value)}</span>
      </div>
      <div className="mt-1.5 h-2 rounded-full bg-black/6 dark:bg-white/10">
        <div className={`h-2 rounded-full ${color}`} style={{ width: `${Math.min(100, Math.max(8, value * 100))}%` }} />
      </div>
    </div>
  );
}

function buildFilterChips(panel: InsightWorkspacePanelPayload): string[] {
  const chips: string[] = [];
  const target = panel.target;
  const filters = target.dashboardFiltersPatch || {};
  Object.entries(filters).forEach(([key, value]) => {
    if (!value || value === 'all') return;
    chips.push(`${humanizeKey(key.replace(/Filter$/, ''))}: ${String(value)}`);
  });
  if (target.journalSearchText) chips.push(`Journal search: ${target.journalSearchText}`);
  if (target.missedOpportunitySearchText) chips.push(`Missed search: ${target.missedOpportunitySearchText}`);
  if (target.selectedTradeId) chips.push(`Trade: ${target.selectedTradeId.slice(0, 8)}`);
  if (target.selectedDay) chips.push(`Day: ${target.selectedDay}`);
  if (target.dashboardFocusGroup) chips.push(`Group: ${target.dashboardFocusGroup}`);
  if (target.dashboardFocusChart) chips.push(`Chart: ${target.dashboardFocusChart}`);
  return chips;
}

function defaultFocusChartForGroup(group?: string | null) {
  if (group === 'Performance Metrics') return 'Performance Snapshot';
  if (group === 'Risk Metrics') return 'Drawdown Curve';
  return null;
}

function computeOutcomeMetrics(closedTrades: TradeRecord[], totalTrades: number) {
  const outcomeSummary = summarizeTradeOutcomes(closedTrades);
  const wins = outcomeSummary.winTrades;
  const losses = outcomeSummary.lossTrades;
  return {
    winCount: wins.length,
    lossCount: losses.length,
    openCount: Math.max(0, totalTrades - closedTrades.length),
    winRate: outcomeSummary.winRate,
    avgWin: wins.length ? wins.reduce((sum, trade) => sum + Number(trade.net_pnl || 0), 0) / wins.length : 0,
    avgLoss: losses.length ? losses.reduce((sum, trade) => sum + Number(trade.net_pnl || 0), 0) / losses.length : 0,
  };
}

function applyInsightDashboardFilters(overview: OverviewData | undefined, filters: Partial<DashboardFilterState>): OverviewData | undefined {
  if (!overview) return overview;
  const trades = overview.trades.filter((trade) => matchesDashboardTrade(trade, filters));
  const activeDays = new Set(
    trades
      .map((trade) => trade.entry_date || trade.entry_time?.slice(0, 10))
      .filter(Boolean) as string[],
  );
  return {
    trades,
    sessionDailyTotals: overview.sessionDailyTotals.filter((row) => activeDays.size === 0 || activeDays.has(row.day)),
    missedOpportunityCount: overview.missedOpportunityCount,
  };
}

function matchesDashboardTrade(trade: TradeRecord, filters: Partial<DashboardFilterState>) {
  const strategyName = String(trade.setup_name || trade.strategy || trade.strategy_tag || 'Unspecified');
  if (filters.strategyFilter && filters.strategyFilter !== 'all' && strategyName !== filters.strategyFilter) return false;
  if (filters.symbolFilter && filters.symbolFilter !== 'all' && String(trade.symbol || '') !== filters.symbolFilter) return false;
  if (filters.marketFilter && filters.marketFilter !== 'all' && String(trade.market_type || '') !== filters.marketFilter) return false;
  if (filters.sideFilter && filters.sideFilter !== 'all' && String(trade.side || '') !== filters.sideFilter) return false;
  if (filters.dayFilter && filters.dayFilter !== 'all' && String(trade.entry_day_of_week || '') !== filters.dayFilter) return false;
  if (filters.closedEarlyFilter && filters.closedEarlyFilter !== 'all') {
    const matches = filters.closedEarlyFilter === 'yes' ? Boolean(trade.closed_before_plan) : !trade.closed_before_plan;
    if (!matches) return false;
  }
  if (filters.statusFilter && filters.statusFilter !== 'all') {
    if (filters.statusFilter === 'closed' && !trade.is_closed) return false;
    if (filters.statusFilter === 'open' && trade.is_closed) return false;
  }
  if (filters.mistakeFilter && filters.mistakeFilter !== 'all') {
    const violations = trade.rule_violations_snapshot || [];
    if (!violations.includes(filters.mistakeFilter)) return false;
  }
  return true;
}

function buildDailyReturns(trades: TradeRecord[]): number[] {
  const byDay = new Map<string, number>();
  trades
    .filter((trade) => trade.is_closed)
    .forEach((trade) => {
      const dayKey = trade.entry_date || trade.entry_time?.slice(0, 10);
      if (!dayKey) return;
      byDay.set(dayKey, (byDay.get(dayKey) || 0) + Number(trade.net_pnl || 0));
    });

  let equity = 100000;
  return Array.from(byDay.entries())
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([, net]) => {
      const denominator = Math.max(Math.abs(equity), 1);
      const dailyReturn = net / denominator;
      equity += net;
      return Number.isFinite(dailyReturn) ? dailyReturn : 0;
    });
}

function buildBookMatrix(trades: TradeRecord[], returns: number[]) {
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

  return { labels: [], matrix: [] as number[][] };
}

function buildGroupedSeries(trades: TradeRecord[], returns: number[], selector: (trade: TradeRecord, index: number) => string): Record<string, number[]> {
  const buckets = new Map<string, number[]>();
  trades.filter((trade) => trade.is_closed).forEach((trade, index) => {
    const key = selector(trade, index);
    const bucket = buckets.get(key) || [];
    bucket.push(returns[index] ?? 0);
    buckets.set(key, bucket);
  });
  return Object.fromEntries(buckets.entries());
}

function buildMetricPayload(data: OverviewData | undefined) {
  const trades = data?.trades || [];
  const closed = trades.filter((trade) => trade.is_closed);
  const returns = buildDailyReturns(trades);
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
    capital: 100000,
    total_capital: 100000,
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

function extractScalar(metric: unknown): number | null {
  if (typeof metric === 'number' && Number.isFinite(metric)) return metric;
  if (metric && typeof metric === 'object') {
    const values = Object.values(metric as Record<string, unknown>).filter(
      (value): value is number => typeof value === 'number' && Number.isFinite(value),
    );
    return values.length ? values[0] : null;
  }
  return null;
}

function toNumberArray(metric: unknown): number[] {
  if (!Array.isArray(metric)) return [];
  return metric.filter((value): value is number => typeof value === 'number' && Number.isFinite(value));
}

function normalizeDisplayNumber(value: number): number {
  return Math.abs(value) < 1e-9 ? 0 : value;
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
  const closed = trades.filter((trade) => trade.is_closed);
  const offset = Math.max(0, closed.length - values.length);
  return values.map((value, index) => {
    const trade = closed[index + offset];
    const rawDate = trade?.entry_date || trade?.entry_time?.slice(0, 10);
    return {
      label: rawDate || `${fallbackPrefix}${index + 1}`,
      [key]: normalizeDisplayNumber(value),
    };
  });
}

function buildDailyNetCurve(trades: TradeRecord[]) {
  const byDay = new Map<string, number>();
  trades
    .filter((trade) => trade.is_closed)
    .forEach((trade) => {
      const dayKey = trade.entry_date || trade.entry_time?.slice(0, 10);
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
        label: formatAxisDate(date),
        net: normalizeDisplayNumber(net),
        cumulative: normalizeDisplayNumber(cumulative),
      };
    });
}
