import { apiClient, getStoredAuthToken, setStoredAuthToken } from '@/api/client';
import type {
  AccountSummary,
  AccountIntegration,
  AIDiagnosis,
  AIInsightsResponse,
  BehaviorAnalysis,
  CalendarDayDetail,
  CalendarDaySummary,
  ChartCatalog,
  CreateAccountInput,
  DashboardChartContractsResponse,
  DashboardFilterState,
  DemoActionResult,
  Mt5FileBridgeInput,
  MissedOpportunityRecord,
  OverviewData,
  PreparedOrderTicketResult,
  SessionDailyTotal,
  StrategyRecord,
  TradeBundle,
  TradePreviewResult,
  TradeRecord,
  WorkspaceLayout,
} from '@/types/prototype';

const DEMO_USERNAME = process.env.NEXT_PUBLIC_DEMO_USERNAME || 'demo_admin';
const DEMO_PASSWORD = process.env.NEXT_PUBLIC_DEMO_PASSWORD || 'demo_pass_123';
const DEMO_ACCOUNT_ID = process.env.NEXT_PUBLIC_DEMO_ACCOUNT_ID || 'DEFAULT';
const DEMO_BROKER_ID = process.env.NEXT_PUBLIC_DEMO_BROKER_ID || 'BROKER';

let sessionBootstrapPromise: Promise<void> | null = null;
let sessionValidated = false;
const EMPTY_BEHAVIOR: BehaviorAnalysis = {
  signals: {},
  percentiles: {},
  zscores: {},
  time_intelligence: { features: {}, findings: [], strengths: [] },
  missed_opportunity_intelligence: { features: {}, findings: [], strengths: [] },
};

function buildDailyReturns(trades: TradeRecord[], capital: number = 100000): number[] {
  const dailyPnls = new Map<string, number>();
  trades
    .filter((trade) => trade.is_closed)
    .forEach((trade) => {
      const dayKey = trade.exit_date || trade.entry_date || trade.exit_time?.slice(0, 10) || trade.entry_time?.slice(0, 10);
      if (!dayKey) return;
      dailyPnls.set(dayKey, (dailyPnls.get(dayKey) || 0) + Number(trade.net_pnl || 0));
    });

  return Array.from(dailyPnls.entries())
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([, pnl]) => pnl / capital);
}

function buildStrategyMatrix(trades: TradeRecord[], capital: number = 100000) {
  const closed = trades.filter((trade) => trade.is_closed);
  const grouped = new Map<string, Map<string, number>>();

  closed.forEach((trade) => {
    const label = String(trade.setup_name || trade.strategy || trade.strategy_tag || 'Unspecified');
    const dayKey = trade.exit_date || trade.entry_date || trade.exit_time?.slice(0, 10) || trade.entry_time?.slice(0, 10);
    if (!dayKey) return;
    const bucket = grouped.get(label) || new Map<string, number>();
    bucket.set(dayKey, (bucket.get(dayKey) || 0) + Number(trade.net_pnl || 0) / capital);
    grouped.set(label, bucket);
  });

  return Object.fromEntries(
    Array.from(grouped.entries()).map(([label, values]) => [
      label,
      Array.from(values.entries())
        .sort(([left], [right]) => left.localeCompare(right))
        .map(([, value]) => value),
    ]),
  );
}

function pickMetrics(results: Record<string, unknown>, keys: string[]): Record<string, unknown> {
  return Object.fromEntries(
    keys
      .filter((key) => results[key] !== undefined && results[key] !== null)
      .map((key) => [key, results[key]]),
  );
}

async function createDemoSession(): Promise<void> {
  const response = await apiClient.post('/auth/demo-session', {
    username: DEMO_USERNAME,
    password: DEMO_PASSWORD,
    account_id: DEMO_ACCOUNT_ID,
    broker_id: DEMO_BROKER_ID,
    account_name: 'Prototype Workspace',
    initial_balance: 100000,
  });
  setStoredAuthToken(response.data?.token || null);
  sessionValidated = true;
}

async function withSessionRetry<T>(request: () => Promise<T>): Promise<T> {
  await ensureDemoSession();
  try {
    return await request();
  } catch (error) {
    const message = error instanceof Error ? error.message : '';
    if (/token|session|Authentication|required|Missing bearer|invalid/i.test(message)) {
      await createDemoSession();
      return await request();
    }
    throw error;
  }
}

export async function ensureDemoSession(): Promise<void> {
  if (sessionValidated && getStoredAuthToken()) {
    return;
  }

  if (!sessionBootstrapPromise) {
    sessionBootstrapPromise = createDemoSession().finally(() => {
      sessionBootstrapPromise = null;
    });
  }

  await sessionBootstrapPromise;
}

export async function fetchOverview(accountId = DEMO_ACCOUNT_ID): Promise<OverviewData> {
  const [tradeResponse, sessionResponse, missedResponse] = await withSessionRetry(() =>
    Promise.all([
      apiClient.get('/journal/trades', { params: { account_id: accountId } }),
      apiClient.get('/trading-sessions/daily-totals', { params: { account_id: accountId } }),
      apiClient.get('/missed-opportunities', { params: { account_id: accountId } }),
    ]),
  );

  return {
    trades: (tradeResponse.data?.trades || []) as TradeRecord[],
    sessionDailyTotals: (sessionResponse.data?.daily_totals || []) as SessionDailyTotal[],
    missedOpportunityCount: (missedResponse.data?.missed_opportunities || []).length,
  };
}

export async function runMetricComputation(payload: {
  category?: string | null;
  metrics_subset?: string[] | null;
  data: Record<string, unknown>;
  phase?: string;
}): Promise<{ results: Record<string, unknown>; errors: Record<string, unknown>; metadata: Record<string, unknown> }> {
  const response = await withSessionRetry(() => apiClient.post('/metrics/run', payload));
  return {
    results: (response.data?.results || {}) as Record<string, unknown>,
    errors: (response.data?.errors || {}) as Record<string, unknown>,
    metadata: (response.data?.metadata || {}) as Record<string, unknown>,
  };
}

export async function fetchBehavior(accountId = DEMO_ACCOUNT_ID): Promise<BehaviorAnalysis> {
  try {
    const response = await withSessionRetry(() => apiClient.get('/journal/behavior', { params: { account_id: accountId } }));
    return (response.data || EMPTY_BEHAVIOR) as BehaviorAnalysis;
  } catch {
    return EMPTY_BEHAVIOR;
  }
}

export async function fetchTrades(accountId = DEMO_ACCOUNT_ID): Promise<TradeRecord[]> {
  const response = await withSessionRetry(() => apiClient.get('/journal/trades', { params: { account_id: accountId } }));
  return (response.data?.trades || []) as TradeRecord[];
}

export async function fetchAccounts(): Promise<AccountSummary[]> {
  const response = await withSessionRetry(() => apiClient.get('/accounts'));
  return (response.data?.accounts || []) as AccountSummary[];
}

export async function fetchAccountIntegrations(): Promise<AccountIntegration[]> {
  const response = await withSessionRetry(() => apiClient.get('/accounts/integrations'));
  return (response.data?.integrations || []) as AccountIntegration[];
}

export async function createConnectedAccount(payload: CreateAccountInput): Promise<AccountSummary> {
  const response = await withSessionRetry(() => apiClient.post('/accounts', payload));
  return (response.data?.account || {}) as AccountSummary;
}

export async function connectSimulatedAccount(accountId: string, brokerId?: string): Promise<AccountIntegration> {
  const response = await withSessionRetry(() =>
    apiClient.post(`/accounts/${encodeURIComponent(accountId)}/connect-simulated`, { broker_id: brokerId }),
  );
  return (response.data || {}) as AccountIntegration;
}

export async function connectMt5FileBridge(payload: Mt5FileBridgeInput): Promise<AccountIntegration> {
  const response = await withSessionRetry(() =>
    apiClient.post(`/accounts/${encodeURIComponent(payload.account_id)}/connect-mt5-file-bridge`, {
      broker_id: payload.broker_id,
      inbox_dir: payload.inbox_dir,
      archive_dir: payload.archive_dir,
      poll_interval_seconds: payload.poll_interval_seconds ?? 0.25,
    }),
  );
  return (response.data || {}) as AccountIntegration;
}

export async function fetchWorkspaceLayout(accountId: string): Promise<WorkspaceLayout | null> {
  const response = await withSessionRetry(() =>
    apiClient.get('/dashboard-layouts/current', { params: { account_id: accountId, dashboard_name: 'web_app_workspace' } }),
  );
  const layout = response.data?.dashboard_layout;
  if (!layout?.metadata) return null;
  return {
    sidebarOrder: layout.metadata.sidebarOrder || [],
    dashboardGroupOrder: layout.metadata.dashboardGroupOrder || [],
    dashboardMetricGroup: layout.metadata.dashboardMetricGroup || {},
    dashboardMetricSize: layout.metadata.dashboardMetricSize || {},
    dashboardTopWidgetVisibility: layout.metadata.dashboardTopWidgetVisibility || {},
    dashboardFilters: layout.metadata.dashboardFilters,
    dashboardFilterPresets: layout.metadata.dashboardFilterPresets || [],
  } as WorkspaceLayout;
}

export async function saveWorkspaceLayout(accountId: string, layout: WorkspaceLayout): Promise<void> {
  await withSessionRetry(() =>
    apiClient.put('/dashboard-layouts/current', {
      account_id: accountId,
      dashboard_name: 'web_app_workspace',
      widgets: [],
      metadata: layout,
      theme_overrides: {},
    }),
  );
}

export async function fetchChartCatalog(): Promise<ChartCatalog> {
  const response = await withSessionRetry(() => apiClient.get('/visualization/chart-catalog'));
  return (response.data || { charts: [], metric_groups: {}, top_widgets: [], group_visuals: {} }) as ChartCatalog;
}

export async function fetchDashboardChartContracts(payload: {
  account_id: string;
  overview: OverviewData;
  metrics: Record<string, unknown>;
  filters: DashboardFilterState;
}): Promise<DashboardChartContractsResponse> {
  const response = await withSessionRetry(() => apiClient.post('/visualization/dashboard-contracts', payload));
  return (response.data || { groups: {} }) as DashboardChartContractsResponse;
}

export async function validateMt5FileBridge(payload: {
  inbox_dir: string;
  archive_dir?: string;
}): Promise<{
  ok: boolean;
  inbox_dir: string;
  archive_dir: string;
  inbox_exists: boolean;
  archive_exists: boolean;
  inbox_writable: boolean;
  archive_writable: boolean;
  warnings: string[];
  instructions: string[];
}> {
  const response = await withSessionRetry(() => apiClient.post('/accounts/mt5-file-bridge/validate', payload));
  return response.data;
}

export async function searchTrades(accountId: string, searchText: string): Promise<TradeRecord[]> {
  const response = await withSessionRetry(() => apiClient.post('/journal/search', {
    account_id: accountId,
    filters: {},
    search_text: searchText,
  }));
  return ((response.data?.results || []) as Array<Record<string, unknown>>)
    .map((item) => (item.trade || item) as TradeRecord)
    .filter((item) => typeof item?.trade_id === 'string' && item.trade_id.length > 0);
}

export async function fetchTradeBundle(tradeId: string): Promise<TradeBundle> {
  const response = await withSessionRetry(() => apiClient.get(`/journal/trade/${encodeURIComponent(tradeId)}/bundle`));
  return {
    trade: response.data?.trade || null,
    attachments: response.data?.attachments || [],
    notes: response.data?.notes || [],
    tags: response.data?.tags || [],
    rating: response.data?.rating || null,
  };
}

export async function fetchMissedOpportunities(accountId = DEMO_ACCOUNT_ID): Promise<MissedOpportunityRecord[]> {
  const response = await withSessionRetry(() => apiClient.get('/missed-opportunities', { params: { account_id: accountId } }));
  return (response.data?.missed_opportunities || []) as MissedOpportunityRecord[];
}

export async function rebuildCalendar(accountId = DEMO_ACCOUNT_ID): Promise<CalendarDaySummary[]> {
  const response = await withSessionRetry(() => apiClient.post('/calendar/rebuild', null, { params: { account_id: accountId } }));
  return (response.data?.day_summaries || []) as CalendarDaySummary[];
}

export async function fetchCalendarSummaries(accountId = DEMO_ACCOUNT_ID): Promise<CalendarDaySummary[]> {
  const response = await withSessionRetry(() => apiClient.get('/calendar/day-summary', { params: { account_id: accountId } }));
  return (response.data?.day_summaries || []) as CalendarDaySummary[];
}

export async function fetchCalendarDayDetail(day: string, accountId = DEMO_ACCOUNT_ID): Promise<CalendarDayDetail> {
  const response = await withSessionRetry(() => apiClient.get('/calendar/day-detail', { params: { account_id: accountId, day } }));
  return response.data as CalendarDayDetail;
}

export async function fetchAIDiagnosis(accountId = DEMO_ACCOUNT_ID): Promise<AIDiagnosis> {
  const overview = await fetchOverview(accountId);
  const behavior = await fetchBehavior(accountId);
  const accounts = await fetchAccounts();
  const account = accounts.find((a) => a.account_id === accountId);
  const capital = account?.initial_balance ? Number(account.initial_balance) : 100000;

  const closedTrades = overview.trades.filter((trade) => trade.is_closed);
  const strategyMatrix = buildStrategyMatrix(overview.trades, capital);

  const metricPayload = {
    returns: buildDailyReturns(overview.trades, capital),
    net_pnl: closedTrades.map((trade) => Number(trade.net_pnl || 0)),
    gross_pnl: closedTrades.map((trade) => Number(trade.gross_pnl || 0)),
    brokerage: closedTrades.map((trade) => Number(trade.commission || 0) + Number(trade.fees || 0)),
    slippage: closedTrades.map((trade) => Number(trade.slippage_cost || 0)),
    swaps: closedTrades.map((trade) => Number(trade.swaps || 0)),
    strategies: Object.keys(strategyMatrix).length ? strategyMatrix : undefined,
    capital: capital,
    total_capital: capital,
    target_volatility: 0.15,
    max_drawdown_threshold: 0.25,
    max_leverage: 3,
    fractional_kelly: 0.5,
    risk_per_trade: 0.01,
    risk_budget: Object.keys(strategyMatrix).length
      ? new Array(Object.keys(strategyMatrix).length).fill(1 / Object.keys(strategyMatrix).length)
      : undefined,
    ruin_floor: 0.2,
  };

  const metricRun = await runMetricComputation({ data: metricPayload, phase: 'research' });
  const metricResults = metricRun.results || {};

  const payload = {
    governance_tier: 'TIER_2',
    structured_metrics: {
      journal: pickMetrics(metricResults, ['trade_count', 'win_rate', 'profit_factor', 'expectancy', 'average_win', 'average_loss', 'payoff_ratio']),
      performance: pickMetrics(metricResults, ['sharpe', 'sortino', 'calmar', 'cagr', 'net_sharpe', 'net_sortino', 'net_cagr']),
      risk: pickMetrics(metricResults, ['volatility', 'max_drawdown', 'value_at_risk', 'conditional_var', 'downside_deviation', 'ulcer_index']),
      distributions: pickMetrics(metricResults, ['skewness', 'kurtosis', 'tail_ratio', 'autocorrelation']),
      regimes: pickMetrics(metricResults, ['regime_sharpe', 'regime_drawdown', 'regime_switch_count', 'regime_transition_matrix']),
      robustness: pickMetrics(metricResults, ['walk_forward', 'bootstrap_confidence_interval']),
      portfolio: pickMetrics(metricResults, ['portfolio_variance', 'average_correlation', 'diversification_ratio', 'effective_bets']),
      capital: pickMetrics(metricResults, ['kelly_fraction', 'safe_f', 'risk_of_ruin']),
      risk_control: pickMetrics(metricResults, ['risk_contributions', 'value_at_risk', 'conditional_var']),
      stress: pickMetrics(metricResults, ['stress_engine']),
      survival: pickMetrics(metricResults, ['survival_engine', 'survival_score']),
    },
    percentiles: behavior.percentiles,
    zscores: behavior.zscores,
    behavioral_signals: behavior.signals,
    time_intelligence: behavior.time_intelligence,
    missed_opportunity_intelligence: behavior.missed_opportunity_intelligence,
    metadata: {
      account_id: accountId,
      trade_count: overview.trades.length,
      closed_trade_count: closedTrades.length,
      missed_opportunity_count: overview.missedOpportunityCount,
    },
  };

  const response = await withSessionRetry(() => apiClient.post('/ai-diagnostic/run', payload));
  return (response.data?.diagnosis || {}) as AIDiagnosis;
}

export async function fetchAIInsightsSummary(accountId = DEMO_ACCOUNT_ID): Promise<AIInsightsResponse> {
  const response = await withSessionRetry(() =>
    apiClient.get('/ai-insights/summary', { params: { account_id: accountId } }),
  );
  return (response.data?.insights || {}) as AIInsightsResponse;
}

export async function fetchStrategies(): Promise<StrategyRecord[]> {
  const response = await withSessionRetry(() => apiClient.get('/strategy-setup/list'));
  return (response.data?.strategies || []) as StrategyRecord[];
}

export async function updateExecutionConfig(config: Record<string, unknown>, accountId?: string | null): Promise<void> {
  await withSessionRetry(() => apiClient.post('/execution-tools/update-config', { config, account_id: accountId || undefined }));
}

export async function previewPositionPlan(payload: Record<string, unknown>): Promise<TradePreviewResult> {
  const response = await withSessionRetry(() => apiClient.post('/execution-tools/preview-trade', payload));
  return (response.data?.result || {}) as TradePreviewResult;
}

export async function prepareOrderTicket(payload: Record<string, unknown>): Promise<PreparedOrderTicketResult> {
  const response = await withSessionRetry(() => apiClient.post('/execution-tools/prepare-order-ticket', payload));
  return (response.data?.result || {}) as PreparedOrderTicketResult;
}

export async function closeTrade(payload: Record<string, unknown>): Promise<Record<string, unknown>> {
  const response = await withSessionRetry(() => apiClient.post('/execution-tools/close-trade', payload));
  return (response.data?.result || {}) as Record<string, unknown>;
}

export async function createStrategy(payload: Record<string, unknown>): Promise<Record<string, unknown>> {
  const response = await withSessionRetry(() => apiClient.post('/strategy-setup/create', payload));
  return (response.data?.strategy || {}) as Record<string, unknown>;
}

export async function createMissedOpportunity(payload: Record<string, unknown>): Promise<Record<string, unknown>> {
  const response = await withSessionRetry(() => apiClient.post('/missed-opportunities', payload));
  return (response.data?.missed_opportunity || {}) as Record<string, unknown>;
}

export async function openTradingSession(payload: Record<string, unknown>): Promise<Record<string, unknown>> {
  const response = await withSessionRetry(() => apiClient.post('/trading-sessions/open', payload));
  return (response.data?.session || {}) as Record<string, unknown>;
}

export async function closeTradingSession(payload: Record<string, unknown>): Promise<Record<string, unknown>> {
  const response = await withSessionRetry(() => apiClient.post('/trading-sessions/close', payload));
  return (response.data?.session || {}) as Record<string, unknown>;
}

export async function importTradeCsv(csvText: string, accountId = DEMO_ACCOUNT_ID): Promise<{ imported_count: number; errors: Array<{ row: number; detail: string }> }> {
  const response = await withSessionRetry(() => apiClient.post('/trade-ingestion/import-csv', {
    account_id: accountId,
    broker_id: DEMO_BROKER_ID,
    csv_text: csvText,
    market_type: 'stock',
    default_strategy_name: 'CSV Import',
    timezone_name: 'Asia/Kolkata',
  }));
  return {
    imported_count: response.data?.imported_count || 0,
    errors: response.data?.errors || [],
  };
}

export async function seedInvestorDemoPack(
  accountId = DEMO_ACCOUNT_ID,
  options?: { broker_id?: string; account_name?: string; initial_balance?: number; trade_count?: number; timezone_name?: string },
): Promise<DemoActionResult> {
  const response = await withSessionRetry(() => apiClient.post('/auth/seed-demo-dataset', {
    account_id: accountId,
    broker_id: options?.broker_id || DEMO_BROKER_ID,
    account_name: options?.account_name || 'Prototype Workspace',
    initial_balance: options?.initial_balance || 100000,
    trade_count: options?.trade_count || 300,
    timezone_name: options?.timezone_name || 'Asia/Kolkata',
  }));
  return {
    status: String(response.data?.status || 'ok'),
    detail: String(response.data?.detail || 'Prototype data seeded successfully.'),
    trade_id: undefined,
  };
}
