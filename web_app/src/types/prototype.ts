export type PrototypeView =
  | 'dashboard'
  | 'journal'
  | 'trade-detail'
  | 'ai-insights'
  | 'missed-opportunities'
  | 'calendar'
  | 'position-sizer'
  | 'demo-data';

export type AccountSummary = {
  account_id: string;
  account_name?: string | null;
  broker_id?: string | null;
  base_currency?: string | null;
  risk_level?: string | null;
  supported_market_types?: string[];
  is_active?: boolean;
};

export type AccountIntegration = {
  account_id: string;
  broker_id: string;
  adapter_type?: string | null;
  connected?: boolean;
  inbox_dir?: string | null;
  archive_dir?: string | null;
};

export type CreateAccountInput = {
  account_id?: string;
  broker_id: string;
  account_name: string;
  initial_balance?: number;
  risk_level?: string;
  base_currency?: string;
  supported_market_types?: string[];
  timezone_name?: string;
  auto_connect_simulated?: boolean;
};

export type Mt5FileBridgeInput = {
  account_id: string;
  broker_id?: string;
  inbox_dir: string;
  archive_dir?: string;
  poll_interval_seconds?: number;
};

export type WorkspaceLayout = {
  sidebarOrder: PrototypeView[];
  sidebarCollapsed?: boolean;
  calendarVisibleMonth?: number | null;
  calendarVisibleYear?: number | null;
  dashboardGroupOrder: string[];
  dashboardMetricGroup: Record<string, string>;
  dashboardMetricSize: Record<string, 'normal' | 'wide'>;
  dashboardTopWidgetVisibility: Record<string, boolean>;
  dashboardFilters?: DashboardFilterState;
  dashboardFilterPresets?: DashboardFilterPreset[];
};

export type DashboardFilterState = {
  strategyFilter: string;
  marketFilter: string;
  symbolFilter: string;
  sideFilter: string;
  mistakeFilter: string;
  datePreset: string;
  timeFilter: string;
  dayFilter: string;
  spreadFilter: string;
  slippageFilter: string;
  holdTimeFilter: string;
  exitReasonFilter: string;
  quantityFilter: string;
  lotSizeFilter: string;
  leverageFilter: string;
  costFilter: string;
  netPnlFilter: string;
  riskAmountFilter: string;
  rrrFilter: string;
  rMultipleFilter: string;
  confidenceFilter: string;
  emotionFilter: string;
  probabilityFilter: string;
  closedEarlyFilter: string;
  statusFilter: string;
};

export type DashboardFilterPreset = {
  name: string;
  filters: DashboardFilterState;
};

export type ChartCatalog = {
  charts: Array<{ chart_type: string; best_for: string[] }>;
  metric_groups: Record<string, Array<{ metric: string; chart_type: string }>>;
  top_widgets: Array<{ key: string; label: string; helper?: string | null }>;
  group_visuals: Record<string, Array<{ title: string; chart_type: string }>>;
};

export type DashboardChartContract = {
  title: string;
  chart_type: 'bar' | 'pie' | 'radar' | 'timeseries' | 'heatmap' | 'histogram';
  points?: Array<Record<string, string | number>>;
  series?: Array<{ key: string; color: string; name?: string | null }>;
  labels_x?: string[];
  labels_y?: string[];
  matrix?: number[][];
  values?: number[];
  bins?: number;
};

export type DashboardChartContractsResponse = {
  groups: Record<string, DashboardChartContract[]>;
};

export type TradeRecord = {
  trade_id: string;
  account_id: string;
  broker_id?: string;
  symbol: string;
  market_type?: string | null;
  side: string;
  strategy?: string | null;
  strategy_tag?: string | null;
  setup_name?: string | null;
  is_closed: boolean;
  entry_price?: number | null;
  entry_time: string;
  entry_date?: string | null;
  entry_day_of_week?: string | null;
  entry_timezone?: string | null;
  entry_hour?: number | null;
  entry_spread?: number | null;
  slippage_at_entry?: number | null;
  stop_loss_at_entry?: number | null;
  target_at_entry?: number | null;
  exit_price?: number | null;
  exit_time?: string | null;
  exit_date?: string | null;
  exit_day_of_week?: string | null;
  exit_hour?: number | null;
  exit_reason?: string | null;
  slippage_at_exit?: number | null;
  quantity?: number | null;
  lot_size?: number | null;
  leverage_used?: number | null;
  fees?: number | null;
  commission?: number | null;
  swaps?: number | null;
  slippage_cost?: number | null;
  net_pnl?: number | null;
  gross_pnl?: number | null;
  total_cost?: number | null;
  risk_amount?: number | null;
  rrr_at_entry?: number | null;
  r_multiple?: number | null;
  probability_bucket?: string | null;
  confidence_score?: number | null;
  emotion_tag?: string | null;
  close_classification?: string | null;
  closed_before_plan?: boolean;
  minimum_target_price?: number | null;
  minimum_target_reward?: number | null;
  notes?: string | null;
  checklist_before?: string[];
  checklist_after?: string[];
  rule_violations_snapshot?: string[];
  pre_trade_capture?: Record<string, unknown> | null;
  post_trade_capture?: Record<string, unknown> | null;
  line_history?: Array<Record<string, unknown>>;
  economics?: Record<string, unknown> | null;
  behavioral?: Record<string, unknown> | null;
  environment?: Record<string, unknown> | null;
  system?: Record<string, unknown> | null;
  metadata?: Record<string, unknown> | null;
  entry_details?: Record<string, unknown> | null;
  exit_details?: Record<string, unknown> | null;
  created_at?: string | null;
  updated_at?: string | null;
};

export type SessionDailyTotal = {
  day: string;
  total_platform_time_minutes: number;
  platform_session_count: number;
};

export type BehaviorFinding = {
  category: string;
  title: string;
  description: string;
  severity: string;
  metric_reference?: string | null;
  value?: number | string | null;
  threshold?: number | string | null;
  metadata?: Record<string, unknown>;
};

export type BehaviorAnalysis = {
  signals: Record<string, number>;
  percentiles: Record<string, number>;
  zscores: Record<string, number>;
  time_intelligence?: {
    features?: Record<string, unknown>;
    findings?: BehaviorFinding[];
    strengths?: BehaviorFinding[];
  };
  missed_opportunity_intelligence?: {
    features?: Record<string, unknown>;
    findings?: BehaviorFinding[];
    strengths?: BehaviorFinding[];
  };
};

export type TradeAttachment = {
  attachment_id: string;
  trade_id: string;
  attachment_type?: string;
  file_path?: string | null;
  content_type?: string | null;
  metadata?: Record<string, unknown> | null;
};

export type TradeNote = {
  note_id: string;
  trade_id?: string | null;
  title?: string | null;
  body?: string | null;
  note_date?: string | null;
};

export type TradeTag = {
  tag_id: string;
  name: string;
  category?: string | null;
  color?: string | null;
};

export type TradeRating = {
  trade_id: string;
  value?: number | null;
  rationale?: string | null;
};

export type TradeBundle = {
  trade: TradeRecord | null;
  attachments: TradeAttachment[];
  notes: TradeNote[];
  tags: TradeTag[];
  rating: TradeRating | null;
};

export type OverviewData = {
  trades: TradeRecord[];
  sessionDailyTotals: SessionDailyTotal[];
  missedOpportunityCount: number;
};

export type MissedOpportunityRecord = {
  opportunity_id: string;
  account_id: string;
  broker_id: string;
  symbol: string;
  market_type: string;
  side: string;
  strategy_name: string;
  probability_bucket: string;
  entry_price: number;
  stop_loss_price: number;
  target_price: number;
  minimum_target_price?: number | null;
  observed_at: string;
  timezone_name: string;
  exit_price?: number | null;
  exit_at?: string | null;
  exit_date?: string | null;
  exit_day_of_week?: string | null;
  exit_reason?: string | null;
  checklist_items?: string[];
  notes?: string | null;
  local_date: string;
  local_day_of_week: string;
  observed_hour: number;
  metadata?: Record<string, unknown> | null;
};

export type CalendarDaySummary = {
  account_id: string;
  day: string;
  pnl: number;
  gross_pnl: number;
  total_cost: number;
  trade_count: number;
  win_count: number;
  loss_count: number;
  total_platform_time_minutes: number;
  platform_session_count: number;
  missed_opportunity_count: number;
  discipline_score?: number | null;
  state_key?: string | null;
  notes_count: number;
  metadata?: Record<string, unknown> | null;
};

export type CalendarDisplayState = {
  key: string;
  color_family: 'green' | 'red' | 'neutral';
};

export type TradingSessionRecord = {
  session_id: string;
  account_id: string;
  broker_id: string;
  platform_name: string;
  opened_at: string;
  closed_at?: string | null;
  timezone_name: string;
  local_date: string;
  local_day_of_week: string;
  start_hour: number;
  end_hour?: number | null;
  duration_minutes: number;
  minutes_within_day?: number;
  metadata?: Record<string, unknown> | null;
};

export type CalendarDayDetail = {
  day: string;
  summary: CalendarDaySummary;
  summary_source: 'stored' | 'live';
  display_state: CalendarDisplayState;
  trade_count: number;
  net_pnl: number;
  gross_pnl: number;
  total_cost: number;
  total_platform_time_minutes: number;
  platform_sessions: TradingSessionRecord[];
  trades: TradeRecord[];
  missed_opportunities: MissedOpportunityRecord[];
  notes: TradeNote[];
};

export type StrategyRecord = {
  name: string;
  description?: string;
  market_types: string[];
  checklist_items: string[];
  mandatory_checklist_items: string[];
  default_risk_percent?: number;
  max_risk_percent?: number;
};

export type TradePreviewResult = {
  position_plan?: Record<string, unknown>;
  discipline_state?: {
    enabled: boolean;
    blocked: boolean;
    missing_fields: string[];
    alerts: string[];
    strategy?: Record<string, unknown> | null;
    checklist_items?: string[];
    mandatory_checklist?: string[];
    selected_checklist?: string[];
    probability_bucket?: string | null;
    all_mandatory_selected?: boolean;
  };
};

export type DemoActionResult = {
  status: string;
  detail?: string;
  trade_id?: string;
};
