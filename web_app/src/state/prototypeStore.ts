import { create } from 'zustand';

import type { DashboardFilterPreset, DashboardFilterState, PrototypeView, WorkspaceLayout } from '@/types/prototype';

const SIDEBAR_STORAGE_KEY = 'my_platform_sidebar_order';
const SIDEBAR_COLLAPSED_KEY = 'my_platform_sidebar_collapsed';
const DASHBOARD_GROUP_ORDER_KEY = 'my_platform_dashboard_group_order';
const DASHBOARD_METRIC_GROUP_KEY = 'my_platform_dashboard_metric_group';
const DASHBOARD_METRIC_SIZE_KEY = 'my_platform_dashboard_metric_sizes';
const DASHBOARD_TOP_WIDGET_KEY = 'my_platform_dashboard_top_widgets';
const DASHBOARD_FILTERS_KEY = 'my_platform_dashboard_filters';
const DASHBOARD_FILTER_PRESETS_KEY = 'my_platform_dashboard_filter_presets';

export const defaultSidebarOrder: PrototypeView[] = [
  'dashboard',
  'journal',
  'trade-detail',
  'ai-insights',
  'missed-opportunities',
  'calendar',
  'position-sizer',
  'demo-data',
];

export const defaultDashboardGroupOrder = [
  'Performance Metrics',
  'Risk Metrics',
  'Journal Metrics',
  'Portfolio Metrics',
  'Distribution Metrics',
  'Capital Metrics',
  'Regime Metrics',
  'Robustness Metrics',
  'Risk Control Metrics',
  'Stress Metrics',
  'Survival Metrics',
];

export const defaultDashboardTopWidgetVisibility: Record<string, boolean> = {
  trades: true,
  net_pnl: true,
  win_rate: true,
  platform_time: true,
  missed_opportunities: true,
  expectancy: true,
  profit_factor: true,
  avg_win: true,
  avg_loss: true,
  avg_win_hold: true,
  avg_loss_hold: true,
  top_win: true,
  top_loss: true,
  win_streak: true,
  loss_streak: true,
  avg_daily_volume: true,
  avg_size: true,
  pre_trade_coverage: true,
  post_trade_coverage: true,
  checklist_coverage: true,
  rule_violations: true,
  probability_coverage: true,
  decision_readiness: true,
};

export const defaultDashboardFilters: DashboardFilterState = {
  strategyFilter: 'all',
  marketFilter: 'all',
  symbolFilter: 'all',
  sideFilter: 'all',
  mistakeFilter: 'all',
  datePreset: 'all',
  timeFilter: 'all',
  dayFilter: 'all',
  spreadFilter: 'all',
  slippageFilter: 'all',
  holdTimeFilter: 'all',
  exitReasonFilter: 'all',
  quantityFilter: 'all',
  lotSizeFilter: 'all',
  leverageFilter: 'all',
  costFilter: 'all',
  netPnlFilter: 'all',
  riskAmountFilter: 'all',
  rrrFilter: 'all',
  rMultipleFilter: 'all',
  confidenceFilter: 'all',
  emotionFilter: 'all',
  probabilityFilter: 'all',
  closedEarlyFilter: 'all',
  statusFilter: 'all',
};

function loadJson<T>(key: string, fallback: T): T {
  if (typeof window === 'undefined') return fallback;
  try {
    const raw = window.localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : fallback;
  } catch {
    return fallback;
  }
}

function persistJson(key: string, value: unknown) {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(key, JSON.stringify(value));
}

type PrototypeState = {
  hydrated: boolean;
  activeView: PrototypeView;
  selectedTradeId: string | null;
  selectedDay: string | null;
  accountId: string | null;
  sidebarOrder: PrototypeView[];
  sidebarCollapsed: boolean;
  dashboardGroupOrder: string[];
  dashboardMetricGroup: Record<string, string>;
  dashboardMetricSize: Record<string, 'normal' | 'wide'>;
  dashboardTopWidgetVisibility: Record<string, boolean>;
  dashboardFilters: DashboardFilterState;
  dashboardFilterPresets: DashboardFilterPreset[];
  setActiveView: (view: PrototypeView) => void;
  selectTrade: (tradeId: string) => void;
  selectDay: (day: string) => void;
  setAccountId: (accountId: string | null) => void;
  setSidebarOrder: (order: PrototypeView[]) => void;
  toggleSidebarCollapsed: () => void;
  resetSidebarOrder: () => void;
  setDashboardGroupOrder: (order: string[]) => void;
  moveMetricToGroup: (metricKey: string, groupTitle: string) => void;
  cycleMetricSize: (metricKey: string) => void;
  resetDashboardLayout: () => void;
  hydrateWorkspaceLayout: (layout: WorkspaceLayout | null) => void;
  exportWorkspaceLayout: () => WorkspaceLayout;
  toggleTopWidget: (widgetKey: string) => void;
  setDashboardFilters: (filters: DashboardFilterState) => void;
  saveDashboardFilterPreset: (name: string, filters: DashboardFilterState) => void;
  deleteDashboardFilterPreset: (name: string) => void;
  hydrateFromStorage: () => void;
};

export const usePrototypeStore = create<PrototypeState>((set, get) => ({
  hydrated: false,
  activeView: 'dashboard',
  selectedTradeId: null,
  selectedDay: null,
  accountId: null,
  sidebarOrder: defaultSidebarOrder,
  sidebarCollapsed: false,
  dashboardGroupOrder: defaultDashboardGroupOrder,
  dashboardMetricGroup: {},
  dashboardMetricSize: {},
  dashboardTopWidgetVisibility: defaultDashboardTopWidgetVisibility,
  dashboardFilters: defaultDashboardFilters,
  dashboardFilterPresets: [],
  setActiveView: (activeView) => set({ activeView }),
  selectTrade: (selectedTradeId) => set({ selectedTradeId, activeView: 'trade-detail' }),
  selectDay: (selectedDay) => set({ selectedDay, activeView: 'calendar' }),
  setAccountId: (accountId) => set({ accountId }),
  setSidebarOrder: (sidebarOrder) => {
    persistJson(SIDEBAR_STORAGE_KEY, sidebarOrder);
    set({ sidebarOrder });
  },
  toggleSidebarCollapsed: () =>
    set((state) => {
      const next = !state.sidebarCollapsed;
      persistJson(SIDEBAR_COLLAPSED_KEY, next);
      return { sidebarCollapsed: next };
    }),
  resetSidebarOrder: () => {
    persistJson(SIDEBAR_STORAGE_KEY, defaultSidebarOrder);
    set({ sidebarOrder: defaultSidebarOrder });
  },
  setDashboardGroupOrder: (dashboardGroupOrder) => {
    persistJson(DASHBOARD_GROUP_ORDER_KEY, dashboardGroupOrder);
    set({ dashboardGroupOrder });
  },
  moveMetricToGroup: (metricKey, groupTitle) =>
    set((state) => {
      const next = { ...state.dashboardMetricGroup, [metricKey]: groupTitle };
      persistJson(DASHBOARD_METRIC_GROUP_KEY, next);
      return { dashboardMetricGroup: next };
    }),
  cycleMetricSize: (metricKey) =>
    set((state) => {
      const current = state.dashboardMetricSize[metricKey] || 'normal';
      const nextValue: 'normal' | 'wide' = current === 'normal' ? 'wide' : 'normal';
      const next: Record<string, 'normal' | 'wide'> = { ...state.dashboardMetricSize, [metricKey]: nextValue };
      persistJson(DASHBOARD_METRIC_SIZE_KEY, next);
      return { dashboardMetricSize: next };
    }),
  resetDashboardLayout: () => {
    persistJson(DASHBOARD_GROUP_ORDER_KEY, defaultDashboardGroupOrder);
    persistJson(DASHBOARD_METRIC_GROUP_KEY, {});
    persistJson(DASHBOARD_METRIC_SIZE_KEY, {});
    persistJson(DASHBOARD_TOP_WIDGET_KEY, defaultDashboardTopWidgetVisibility);
    persistJson(DASHBOARD_FILTERS_KEY, defaultDashboardFilters);
    set({
      dashboardGroupOrder: defaultDashboardGroupOrder,
      dashboardMetricGroup: {},
      dashboardMetricSize: {},
      dashboardTopWidgetVisibility: defaultDashboardTopWidgetVisibility,
      dashboardFilters: defaultDashboardFilters,
    });
  },
  hydrateWorkspaceLayout: (layout) => {
    const sidebarOrder = layout?.sidebarOrder?.length ? layout.sidebarOrder : defaultSidebarOrder;
    const sidebarCollapsed = false;
    const dashboardGroupOrder = layout?.dashboardGroupOrder?.length ? layout.dashboardGroupOrder : defaultDashboardGroupOrder;
    const dashboardMetricGroup = layout?.dashboardMetricGroup || {};
    const dashboardMetricSize = layout?.dashboardMetricSize || {};
    const dashboardTopWidgetVisibility = { ...defaultDashboardTopWidgetVisibility, ...(layout?.dashboardTopWidgetVisibility || {}) };
    const dashboardFilters = { ...defaultDashboardFilters, ...(layout?.dashboardFilters || {}) };
    const dashboardFilterPresets = layout?.dashboardFilterPresets || [];
    persistJson(SIDEBAR_STORAGE_KEY, sidebarOrder);
    persistJson(SIDEBAR_COLLAPSED_KEY, sidebarCollapsed);
    persistJson(DASHBOARD_GROUP_ORDER_KEY, dashboardGroupOrder);
    persistJson(DASHBOARD_METRIC_GROUP_KEY, dashboardMetricGroup);
    persistJson(DASHBOARD_METRIC_SIZE_KEY, dashboardMetricSize);
    persistJson(DASHBOARD_TOP_WIDGET_KEY, dashboardTopWidgetVisibility);
    persistJson(DASHBOARD_FILTERS_KEY, dashboardFilters);
    persistJson(DASHBOARD_FILTER_PRESETS_KEY, dashboardFilterPresets);
    set({
      sidebarOrder,
      sidebarCollapsed,
      dashboardGroupOrder,
      dashboardMetricGroup,
      dashboardMetricSize,
      dashboardTopWidgetVisibility,
      dashboardFilters,
      dashboardFilterPresets,
    });
  },
  exportWorkspaceLayout: () => {
    const state = get();
    return {
      sidebarOrder: state.sidebarOrder,
      sidebarCollapsed: state.sidebarCollapsed,
      dashboardGroupOrder: state.dashboardGroupOrder,
      dashboardMetricGroup: state.dashboardMetricGroup,
      dashboardMetricSize: state.dashboardMetricSize,
      dashboardTopWidgetVisibility: state.dashboardTopWidgetVisibility,
      dashboardFilters: state.dashboardFilters,
      dashboardFilterPresets: state.dashboardFilterPresets,
    };
  },
  toggleTopWidget: (widgetKey) =>
    set((state) => {
      if (widgetKey === '__all__') {
        const areAllVisible = Object.values(state.dashboardTopWidgetVisibility).every(Boolean);
        const next = Object.fromEntries(
          Object.keys(state.dashboardTopWidgetVisibility).map((key) => [key, !areAllVisible]),
        );
        persistJson(DASHBOARD_TOP_WIDGET_KEY, next);
        return { dashboardTopWidgetVisibility: next };
      }
      const next = {
        ...state.dashboardTopWidgetVisibility,
        [widgetKey]: !state.dashboardTopWidgetVisibility[widgetKey],
      };
      persistJson(DASHBOARD_TOP_WIDGET_KEY, next);
      return { dashboardTopWidgetVisibility: next };
    }),
  setDashboardFilters: (dashboardFilters) => {
    persistJson(DASHBOARD_FILTERS_KEY, dashboardFilters);
    set({ dashboardFilters });
  },
  saveDashboardFilterPreset: (name, filters) =>
    set((state) => {
      const normalizedName = name.trim();
      if (!normalizedName) return state;
      const next = [
        ...state.dashboardFilterPresets.filter((preset) => preset.name !== normalizedName),
        { name: normalizedName, filters },
      ].sort((a, b) => a.name.localeCompare(b.name));
      persistJson(DASHBOARD_FILTER_PRESETS_KEY, next);
      return { dashboardFilterPresets: next };
    }),
  deleteDashboardFilterPreset: (name) =>
    set((state) => {
      const next = state.dashboardFilterPresets.filter((preset) => preset.name !== name);
      persistJson(DASHBOARD_FILTER_PRESETS_KEY, next);
      return { dashboardFilterPresets: next };
    }),
  hydrateFromStorage: () => {
    if (get().hydrated) return;
    const sidebarOrder = loadJson(SIDEBAR_STORAGE_KEY, defaultSidebarOrder);
    const sidebarCollapsed = false;
    const dashboardGroupOrder = loadJson(DASHBOARD_GROUP_ORDER_KEY, defaultDashboardGroupOrder);
    const dashboardMetricGroup = loadJson(DASHBOARD_METRIC_GROUP_KEY, {} as Record<string, string>);
    const dashboardMetricSize = loadJson(DASHBOARD_METRIC_SIZE_KEY, {} as Record<string, 'normal' | 'wide'>);
    const dashboardTopWidgetVisibility = { ...defaultDashboardTopWidgetVisibility, ...loadJson(DASHBOARD_TOP_WIDGET_KEY, {} as Record<string, boolean>) };
    const dashboardFilters = { ...defaultDashboardFilters, ...loadJson(DASHBOARD_FILTERS_KEY, {} as DashboardFilterState) };
    const dashboardFilterPresets = loadJson(DASHBOARD_FILTER_PRESETS_KEY, [] as DashboardFilterPreset[]);
    set({
      hydrated: true,
      sidebarOrder,
      sidebarCollapsed,
      dashboardGroupOrder,
      dashboardMetricGroup,
      dashboardMetricSize,
      dashboardTopWidgetVisibility,
      dashboardFilters,
      dashboardFilterPresets,
    });
  },
}));
