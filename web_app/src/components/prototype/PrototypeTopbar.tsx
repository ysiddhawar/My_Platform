import { useEffect, useMemo, useRef, useState } from 'react';
import { useQuery, useQueryClient } from 'react-query';

import { fetchCalendarSummaries, fetchOverview, rebuildCalendar } from '@/api/prototype';
import { ThemeToggle } from '@/components/foundation/ThemeToggle';
import { usePrototypeStore } from '@/state/prototypeStore';
import type { AccountSummary, DashboardFilterState, PrototypeView, TradeRecord } from '@/types/prototype';

const titleMap: Record<PrototypeView, string> = {
  dashboard: 'Dashboard',
  journal: 'Journal',
  'trade-detail': 'Trade Detail',
  'ai-insights': 'AI Insights',
  'missed-opportunities': 'Missed Opportunities',
  calendar: 'Calendar',
  'position-sizer': 'Position Sizer',
  'demo-data': 'Data',
};

type PrototypeTopbarProps = {
  activeView: PrototypeView;
  accountId: string | null;
  accounts: AccountSummary[];
  onChooseAccount: (accountId: string) => void;
  onOpenAccountPicker: () => void;
};

export function PrototypeTopbar({ activeView, accountId, accounts, onChooseAccount, onOpenAccountPicker }: PrototypeTopbarProps) {
  const isDashboard = activeView === 'dashboard';
  const isCalendar = activeView === 'calendar';
  const selectedAccount = accounts.find((account) => account.account_id === accountId) || null;

  return (
    <header className="relative z-[11000] shrink-0 border-b border-black/10 bg-[var(--topbar-bg)] px-1 py-2 text-[var(--color-ink)] dark:border-white/10 lg:px-1.5">
      {isDashboard ? (
        <DashboardTopbarControls
          accountId={accountId}
          account={selectedAccount}
          accounts={accounts}
          onChooseAccount={onChooseAccount}
          onOpenAccountPicker={onOpenAccountPicker}
        />
      ) : isCalendar ? (
        <CalendarTopbarControls
          accountId={accountId}
          accounts={accounts}
          onChooseAccount={onChooseAccount}
          onOpenAccountPicker={onOpenAccountPicker}
        />
      ) : (
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <p className="text-[0.7rem] font-semibold uppercase tracking-[0.24em] text-black/55 dark:text-white/65">
              {accountId ? `Account ${accountId}` : 'No Account Selected'}
            </p>
            <h1 className="mt-1 text-[1.8rem] font-semibold tracking-[-0.04em] text-[#0d0d0d] dark:text-white">
              {titleMap[activeView]}
            </h1>
          </div>
          <div className="shrink-0 pt-0.5">
            <div className="flex items-center gap-1.5">
              <AccountSelectControl
                accountId={accountId}
                accounts={accounts}
                onChooseAccount={onChooseAccount}
                onOpenAccountPicker={onOpenAccountPicker}
              />
              <ThemeToggle />
            </div>
          </div>
        </div>
      )}
    </header>
  );
}

function CalendarTopbarControls({
  accountId,
  accounts,
  onChooseAccount,
  onOpenAccountPicker,
}: {
  accountId: string | null;
  accounts: AccountSummary[];
  onChooseAccount: (accountId: string) => void;
  onOpenAccountPicker: () => void;
}) {
  const queryClient = useQueryClient();
  const selectedDay = usePrototypeStore((state) => state.selectedDay);
  const selectDay = usePrototypeStore((state) => state.selectDay);
  const calendarVisibleMonth = usePrototypeStore((state) => state.calendarVisibleMonth);
  const calendarVisibleYear = usePrototypeStore((state) => state.calendarVisibleYear);
  const setCalendarVisibleMonthYear = usePrototypeStore((state) => state.setCalendarVisibleMonthYear);

  const { data: summaries, isFetching } = useQuery(
    ['prototype-calendar-summaries', accountId],
    () => fetchCalendarSummaries(accountId as string),
    { enabled: Boolean(accountId) },
  );

  useEffect(() => {
    if (calendarVisibleMonth != null && calendarVisibleYear != null) return;
    const today = new Date();
    setCalendarVisibleMonthYear(today.getMonth(), today.getFullYear());
  }, [calendarVisibleMonth, calendarVisibleYear, setCalendarVisibleMonthYear]);

  const monthValue = calendarVisibleMonth ?? new Date().getMonth();
  const yearValue = calendarVisibleYear ?? new Date().getFullYear();
  const visibleSummaries = useMemo(() => {
    return (summaries || []).filter((summary) => {
      const day = new Date(`${summary.day}T00:00:00`);
      return day.getMonth() === monthValue && day.getFullYear() === yearValue;
    });
  }, [monthValue, summaries, yearValue]);
  const monthlyNetPnl = useMemo(
    () => visibleSummaries.reduce((sum, item) => sum + Number(item.pnl || 0), 0),
    [visibleSummaries],
  );
  const monthlyTradedDays = useMemo(
    () => visibleSummaries.filter((item) => item.trade_count > 0).length,
    [visibleSummaries],
  );

  const monthOptions = useMemo(
    () =>
      Array.from({ length: 12 }, (_, month) => ({
        value: String(month),
        label: new Date(2026, month, 1).toLocaleString('en-US', { month: 'long' }),
      })),
    [],
  );
  const yearOptions = useMemo(() => {
    const yearsFromData = Array.from(
      new Set((summaries || []).map((item) => Number(item.day.slice(0, 4))).filter((value) => Number.isFinite(value))),
    ).sort((a, b) => a - b);
    if (yearsFromData.length) {
      return yearsFromData.map((year) => ({ value: String(year), label: String(year) }));
    }
    const currentYear = new Date().getFullYear();
    return Array.from({ length: 7 }, (_, index) => currentYear - 3 + index).map((year) => ({
      value: String(year),
      label: String(year),
    }));
  }, [summaries]);

  const shiftMonth = (delta: number) => {
    const nextDate = new Date(yearValue, monthValue + delta, 1);
    setCalendarVisibleMonthYear(nextDate.getMonth(), nextDate.getFullYear());
    selectDay(`${nextDate.getFullYear()}-${String(nextDate.getMonth() + 1).padStart(2, '0')}-01`);
  };

  return (
    <div className="grid grid-cols-[1fr_auto] items-center gap-2">
      <div className="flex min-w-0 items-center justify-center gap-1.5">
        <CalendarNavButton label="<" onClick={() => shiftMonth(-1)} />
        <CalendarTopbarSelect
          value={String(monthValue)}
          onChange={(value) => {
            const nextMonth = Number(value);
            setCalendarVisibleMonthYear(nextMonth, yearValue);
            selectDay(`${yearValue}-${String(nextMonth + 1).padStart(2, '0')}-01`);
          }}
          options={monthOptions}
          minWidthClass="min-w-[126px]"
        />
        <CalendarTopbarSelect
          value={String(yearValue)}
          onChange={(value) => {
            const nextYear = Number(value);
            setCalendarVisibleMonthYear(monthValue, nextYear);
            selectDay(`${nextYear}-${String(monthValue + 1).padStart(2, '0')}-01`);
          }}
          options={yearOptions}
          minWidthClass="min-w-[90px]"
        />
        <CalendarNavButton label=">" onClick={() => shiftMonth(1)} />
        <button
          type="button"
          onClick={async () => {
            if (!accountId) return;
            await rebuildCalendar(accountId);
            await Promise.all([
              queryClient.invalidateQueries(['prototype-calendar-summaries', accountId]),
              queryClient.invalidateQueries(['prototype-calendar-day-detail', accountId]),
            ]);
          }}
          className="h-[30px] rounded-[10px] border border-black/10 bg-white px-2.5 text-sm font-semibold leading-none text-[#0d0d0d] transition hover:border-[#ff5900] hover:bg-[#ff5900] hover:text-[#0d0d0d] dark:border-white/15 dark:bg-[#1a1a1a] dark:text-white dark:hover:border-[#ff5900] dark:hover:bg-[#ff5900] dark:hover:text-white"
        >
          {isFetching ? 'Refreshing…' : 'Refresh'}
        </button>
        <div className="ml-2 flex items-center gap-2 rounded-[12px] border border-black/10 bg-[#1f1f1f] px-3 py-1.5 text-white dark:border-white/10 dark:bg-[#1f1f1f]">
          <span className="text-[11px] font-semibold uppercase tracking-[0.14em] text-white/70">Monthly Stats</span>
          <span className="rounded-full bg-[#2b2b2b] px-2.5 py-1 text-[12px] font-semibold text-[#7ef0a0]">
            {formatCompactCalendarCurrency(monthlyNetPnl)}
          </span>
          <span className="rounded-full bg-[#2b2b2b] px-2.5 py-1 text-[12px] font-semibold text-white">
            {monthlyTradedDays} days
          </span>
        </div>
      </div>
      <div className="flex shrink-0 items-center gap-1.5 justify-self-end">
        <AccountSelectControl
          accountId={accountId}
          accounts={accounts}
          onChooseAccount={onChooseAccount}
          onOpenAccountPicker={onOpenAccountPicker}
        />
        <ThemeToggle />
      </div>
    </div>
  );
}

function formatCompactCalendarCurrency(value: number) {
  const sign = value < 0 ? '-' : '';
  const absolute = Math.abs(value);
  if (absolute >= 1000) {
    return `${sign}$${(absolute / 1000).toFixed(2)}K`;
  }
  return `${sign}$${absolute.toFixed(2)}`;
}

function DashboardTopbarControls({
  accountId,
  account,
  accounts,
  onChooseAccount,
  onOpenAccountPicker,
}: {
  accountId: string | null;
  account: AccountSummary | null;
  accounts: AccountSummary[];
  onChooseAccount: (accountId: string) => void;
  onOpenAccountPicker: () => void;
}) {
  const dashboardFilters = usePrototypeStore((state) => state.dashboardFilters);
  const setDashboardFilters = usePrototypeStore((state) => state.setDashboardFilters);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [openDropdownId, setOpenDropdownId] = useState<string | null>(null);
  const controlsRef = useRef<HTMLDivElement | null>(null);
  const { data } = useQuery(['prototype-overview', accountId], () => fetchOverview(accountId as string), {
    enabled: Boolean(accountId),
  });

  useEffect(() => {
    const handlePointerDown = (event: MouseEvent) => {
      if (!controlsRef.current?.contains(event.target as Node)) {
        setOpenDropdownId(null);
      }
    };
    window.addEventListener('mousedown', handlePointerDown);
    return () => window.removeEventListener('mousedown', handlePointerDown);
  }, []);

  const strategyOptions = useMemo(
    () => uniqueSorted((data?.trades || []).map((trade) => String(trade.setup_name || trade.strategy || trade.strategy_tag || 'Unspecified'))),
    [data],
  );
  const symbolOptions = useMemo(() => uniqueSorted((data?.trades || []).map((trade) => String(trade.symbol || 'unknown'))), [data]);
  const sideOptions = useMemo(() => uniqueSorted((data?.trades || []).map((trade) => String(trade.side || 'unknown'))), [data]);
  const mistakeOptions = useMemo(
    () => uniqueSorted((data?.trades || []).flatMap((trade) => (trade.rule_violations_snapshot || []).map((item) => String(item)))),
    [data],
  );
  const marketOptions = useMemo(() => {
    const fromTrades = uniqueSorted((data?.trades || []).map((trade) => String(trade.market_type || 'unknown')).filter((value) => value !== 'unknown'));
    const fromAccount = uniqueSorted((account?.supported_market_types || []).map((value) => String(value)).filter(Boolean));
    return uniqueSorted([...fromTrades, ...fromAccount]);
  }, [account, data]);
  const exitReasonOptions = useMemo(
    () => uniqueSorted((data?.trades || []).map((trade) => String(trade.exit_reason || '')).filter(Boolean)),
    [data],
  );
  const lotSizeOptions = useMemo(
    () => uniqueSorted((data?.trades || []).map((trade) => String(Number(trade.lot_size || 0))).filter((value) => value !== '0')),
    [data],
  );
  const leverageOptions = useMemo(
    () => uniqueSorted((data?.trades || []).map((trade) => String(Number(trade.leverage_used || 0))).filter((value) => value !== '0')),
    [data],
  );
  const emotionOptions = useMemo(
    () => uniqueSorted((data?.trades || []).map((trade) => String(trade.emotion_tag || '')).filter(Boolean)),
    [data],
  );
  const probabilityOptions = useMemo(
    () => uniqueSorted((data?.trades || []).map((trade) => String(trade.probability_bucket || '')).filter(Boolean)),
    [data],
  );
  const spreadBucketOptions = useMemo(() => buildBucketOptions(getSpreadValues(data?.trades || []), formatBucketNumber), [data]);
  const slippageBucketOptions = useMemo(() => buildBucketOptions(getSlippageValues(data?.trades || []), formatBucketNumber), [data]);
  const quantityBucketOptions = useMemo(() => buildBucketOptions(getQuantityValues(data?.trades || []), formatBucketNumber), [data]);
  const costBucketOptions = useMemo(() => buildBucketOptions(getCostValues(data?.trades || []), formatCurrencyBucket), [data]);
  const netPnlBucketOptions = useMemo(() => buildBucketOptions(getNetPnlValues(data?.trades || []), formatCurrencyBucket), [data]);
  const riskAmountBucketOptions = useMemo(() => buildBucketOptions(getRiskAmountValues(data?.trades || []), formatCurrencyBucket), [data]);
  const rrrBucketOptions = useMemo(() => buildBucketOptions(getRrrValues(data?.trades || []), formatBucketNumber), [data]);
  const rMultipleBucketOptions = useMemo(() => buildBucketOptions(getRMultipleValues(data?.trades || []), formatBucketNumber), [data]);
  const confidenceBucketOptions = useMemo(() => buildBucketOptions(getConfidenceValues(data?.trades || []), formatBucketNumber), [data]);

  const hasAdvancedValues =
    dashboardFilters.timeFilter !== 'all'
    || dashboardFilters.dayFilter !== 'all'
    || dashboardFilters.spreadFilter !== 'all'
    || dashboardFilters.slippageFilter !== 'all'
    || dashboardFilters.holdTimeFilter !== 'all'
    || dashboardFilters.exitReasonFilter !== 'all'
    || dashboardFilters.quantityFilter !== 'all'
    || dashboardFilters.lotSizeFilter !== 'all'
    || dashboardFilters.leverageFilter !== 'all'
    || dashboardFilters.costFilter !== 'all'
    || dashboardFilters.netPnlFilter !== 'all'
    || dashboardFilters.riskAmountFilter !== 'all'
    || dashboardFilters.rrrFilter !== 'all'
    || dashboardFilters.rMultipleFilter !== 'all'
    || dashboardFilters.confidenceFilter !== 'all'
    || dashboardFilters.emotionFilter !== 'all'
    || dashboardFilters.probabilityFilter !== 'all'
    || dashboardFilters.closedEarlyFilter !== 'all'
    || dashboardFilters.statusFilter !== 'all';

  const advancedVisible = showAdvanced || hasAdvancedValues;
  const update = (patch: Partial<DashboardFilterState>) => setDashboardFilters({ ...dashboardFilters, ...patch });

  const rowOne: React.ReactNode[] = [
    <CompactFilterSelect key="date" dropdownId="date" openDropdownId={openDropdownId} setOpenDropdownId={setOpenDropdownId} label="Date" value={dashboardFilters.datePreset} onChange={(value) => update({ datePreset: value })} options={DATE_OPTIONS} tooltipPlacement="right" />,
    <CompactFilterSelect key="setup" dropdownId="setup" openDropdownId={openDropdownId} setOpenDropdownId={setOpenDropdownId} label="Setup" value={dashboardFilters.strategyFilter} onChange={(value) => update({ strategyFilter: value })} options={strategyOptions.map((value) => [value, value])} tooltipPlacement="right" />,
    <CompactFilterSelect key="symbol" dropdownId="symbol" openDropdownId={openDropdownId} setOpenDropdownId={setOpenDropdownId} label="Symbol" value={dashboardFilters.symbolFilter} onChange={(value) => update({ symbolFilter: value })} options={symbolOptions.map((value) => [value, value])} tooltipPlacement="right" />,
    <CompactFilterSelect key="side" dropdownId="side" openDropdownId={openDropdownId} setOpenDropdownId={setOpenDropdownId} label="Side" value={dashboardFilters.sideFilter} onChange={(value) => update({ sideFilter: value })} options={sideOptions.map((value) => [value, humanize(value)])} tooltipPlacement="left" />,
    <CompactFilterSelect key="mistakes" dropdownId="mistakes" openDropdownId={openDropdownId} setOpenDropdownId={setOpenDropdownId} label="Mistakes" value={dashboardFilters.mistakeFilter} onChange={(value) => update({ mistakeFilter: value })} options={['none', ...mistakeOptions].map((value) => [value, value === 'none' ? 'None' : humanize(value)])} tooltipPlacement="left" />,
    ...(marketOptions.length > 1
      ? [<CompactFilterSelect key="market" dropdownId="market" openDropdownId={openDropdownId} setOpenDropdownId={setOpenDropdownId} label="Market" value={dashboardFilters.marketFilter} onChange={(value) => update({ marketFilter: value })} options={marketOptions.map((value) => [value, humanize(value)])} tooltipPlacement="left" />]
      : []),
    <button
      key="advanced"
      type="button"
      onClick={() => setShowAdvanced((value) => !value)}
      className={`h-[22px] w-full rounded-[10px] border px-1.5 text-sm font-semibold leading-none transition ${
        advancedVisible
          ? 'border-[#ff5900] bg-[#ff5900] text-white dark:border-[#ff5900] dark:bg-[#ff5900] dark:text-white'
          : 'border-black/10 bg-white text-[#0d0d0d] hover:border-[#ff5900] hover:bg-[#ff5900] hover:text-[#0d0d0d] dark:border-white/10 dark:bg-[#1a1a1a] dark:text-white dark:hover:border-[#ff5900] dark:hover:bg-[#ff5900] dark:hover:text-white'
      }`}
    >
      Advanced
    </button>,
  ];

  const rowTwo: React.ReactNode[] = [
    <CompactFilterSelect key="time" dropdownId="time" openDropdownId={openDropdownId} setOpenDropdownId={setOpenDropdownId} label="Time" value={dashboardFilters.timeFilter} onChange={(value) => update({ timeFilter: value })} options={TIME_OPTIONS} />,
    <CompactFilterSelect key="day" dropdownId="day" openDropdownId={openDropdownId} setOpenDropdownId={setOpenDropdownId} label="Day" value={dashboardFilters.dayFilter} onChange={(value) => update({ dayFilter: value })} options={DAY_OPTIONS} />,
    <BucketOrCustomFilter key="spread" dropdownId="spread" openDropdownId={openDropdownId} setOpenDropdownId={setOpenDropdownId} label="Spread" value={dashboardFilters.spreadFilter} onChange={(value) => update({ spreadFilter: value })} options={spreadBucketOptions} />,
    <BucketOrCustomFilter key="slippage" dropdownId="slippage" openDropdownId={openDropdownId} setOpenDropdownId={setOpenDropdownId} label="Slippage" value={dashboardFilters.slippageFilter} onChange={(value) => update({ slippageFilter: value })} options={slippageBucketOptions} />,
    <CompactFilterSelect key="holdTime" dropdownId="holdTime" openDropdownId={openDropdownId} setOpenDropdownId={setOpenDropdownId} label="Hold Time" value={dashboardFilters.holdTimeFilter} onChange={(value) => update({ holdTimeFilter: value })} options={HOLD_TIME_OPTIONS} />,
    <CompactFilterSelect key="exitReason" dropdownId="exitReason" openDropdownId={openDropdownId} setOpenDropdownId={setOpenDropdownId} label="Exit Reason" value={dashboardFilters.exitReasonFilter} onChange={(value) => update({ exitReasonFilter: value })} options={exitReasonOptions.map((value) => [value, humanize(value)])} />,
    <BucketOrCustomFilter key="quantity" dropdownId="quantity" openDropdownId={openDropdownId} setOpenDropdownId={setOpenDropdownId} label="Quantity" value={dashboardFilters.quantityFilter} onChange={(value) => update({ quantityFilter: value })} options={quantityBucketOptions} />,
    <CompactFilterSelect key="lotSize" dropdownId="lotSize" openDropdownId={openDropdownId} setOpenDropdownId={setOpenDropdownId} label="Lot Size" value={dashboardFilters.lotSizeFilter} onChange={(value) => update({ lotSizeFilter: value })} options={lotSizeOptions.map((value) => [value, value])} />,
    <CompactFilterSelect key="leverage" dropdownId="leverage" openDropdownId={openDropdownId} setOpenDropdownId={setOpenDropdownId} label="Leverage" value={dashboardFilters.leverageFilter} onChange={(value) => update({ leverageFilter: value })} options={leverageOptions.map((value) => [value, `${value}x`])} />,
    <BucketOrCustomFilter key="cost" dropdownId="cost" openDropdownId={openDropdownId} setOpenDropdownId={setOpenDropdownId} label="Costs" value={dashboardFilters.costFilter} onChange={(value) => update({ costFilter: value })} options={costBucketOptions} />,
  ];

  const rowThree: React.ReactNode[] = [
    <BucketOrCustomFilter key="netPnl" dropdownId="netPnl" openDropdownId={openDropdownId} setOpenDropdownId={setOpenDropdownId} label="Net PnL" value={dashboardFilters.netPnlFilter} onChange={(value) => update({ netPnlFilter: value })} options={netPnlBucketOptions} />,
    <BucketOrCustomFilter key="riskAmount" dropdownId="riskAmount" openDropdownId={openDropdownId} setOpenDropdownId={setOpenDropdownId} label="Risk Amount" value={dashboardFilters.riskAmountFilter} onChange={(value) => update({ riskAmountFilter: value })} options={riskAmountBucketOptions} />,
    <BucketOrCustomFilter key="rrr" dropdownId="rrr" openDropdownId={openDropdownId} setOpenDropdownId={setOpenDropdownId} label="RRR" value={dashboardFilters.rrrFilter} onChange={(value) => update({ rrrFilter: value })} options={rrrBucketOptions} />,
    <BucketOrCustomFilter key="rMultiple" dropdownId="rMultiple" openDropdownId={openDropdownId} setOpenDropdownId={setOpenDropdownId} label="R Multiple" value={dashboardFilters.rMultipleFilter} onChange={(value) => update({ rMultipleFilter: value })} options={rMultipleBucketOptions} />,
    <BucketOrCustomFilter key="confidence" dropdownId="confidence" openDropdownId={openDropdownId} setOpenDropdownId={setOpenDropdownId} label="Confidence" value={dashboardFilters.confidenceFilter} onChange={(value) => update({ confidenceFilter: value })} options={confidenceBucketOptions} />,
    <CompactFilterSelect key="emotion" dropdownId="emotion" openDropdownId={openDropdownId} setOpenDropdownId={setOpenDropdownId} label="Emotion" value={dashboardFilters.emotionFilter} onChange={(value) => update({ emotionFilter: value })} options={emotionOptions.map((value) => [value, humanize(value)])} />,
    <CompactFilterSelect key="probability" dropdownId="probability" openDropdownId={openDropdownId} setOpenDropdownId={setOpenDropdownId} label="Probability" value={dashboardFilters.probabilityFilter} onChange={(value) => update({ probabilityFilter: value })} options={probabilityOptions.map((value) => [value, value])} />,
    <CompactFilterSelect key="closedEarly" dropdownId="closedEarly" openDropdownId={openDropdownId} setOpenDropdownId={setOpenDropdownId} label="Closed Early" value={dashboardFilters.closedEarlyFilter} onChange={(value) => update({ closedEarlyFilter: value })} options={YES_NO_OPTIONS} />,
    <CompactFilterSelect key="status" dropdownId="status" openDropdownId={openDropdownId} setOpenDropdownId={setOpenDropdownId} label="Status" value={dashboardFilters.statusFilter} onChange={(value) => update({ statusFilter: value })} options={STATUS_OPTIONS} />,
  ];

  return (
    <div ref={controlsRef} className="space-y-0.5">
      <FilterRow
        items={rowOne}
        trailing={(
          <div className="flex items-center gap-1.5">
            <AccountSelectControl
              accountId={accountId}
              accounts={accounts}
              onChooseAccount={onChooseAccount}
              onOpenAccountPicker={onOpenAccountPicker}
            />
            <ThemeToggle />
          </div>
        )}
      />
      <FilterRow items={rowTwo} />
      {advancedVisible ? <FilterRow items={rowThree} /> : null}
    </div>
  );
}

function FilterRow({ items, trailing }: { items: React.ReactNode[]; trailing?: React.ReactNode }) {
  return (
    <div className="flex items-start gap-0.5">
      <div
        className="grid min-w-0 flex-1 items-start gap-0.5"
        style={{ gridTemplateColumns: `repeat(${items.length}, minmax(0, 1fr))` }}
      >
        {items.map((item, index) => (
          <div key={index} className="min-w-0">
            {item}
          </div>
        ))}
      </div>
      {trailing ? <div className="flex shrink-0 items-center gap-0.5">{trailing}</div> : null}
    </div>
  );
}

function CalendarNavButton({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="h-[32px] w-[38px] rounded-[10px] border border-black/10 bg-white px-0 text-base font-semibold leading-none text-[#0d0d0d] transition hover:border-[#ff5900] hover:bg-[#ff5900] hover:text-[#0d0d0d] dark:border-white/15 dark:bg-[#1a1a1a] dark:text-white dark:hover:border-[#ff5900] dark:hover:bg-[#ff5900] dark:hover:text-white"
    >
      {label}
    </button>
  );
}

function CalendarTopbarSelect({
  value,
  onChange,
  options,
  minWidthClass,
}: {
  value: string;
  onChange: (value: string) => void;
  options: Array<{ value: string; label: string }>;
  minWidthClass: string;
}) {
  return (
    <label className={`relative block ${minWidthClass}`}>
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="h-[30px] w-full appearance-none rounded-[10px] border border-black/10 bg-white px-2.5 pr-6 text-sm font-semibold leading-none text-[#0d0d0d] outline-none transition hover:border-[#ff5900] hover:bg-[#ff5900] hover:text-[#0d0d0d] dark:border-white/15 dark:bg-[#1a1a1a] dark:text-white dark:hover:border-[#ff5900] dark:hover:bg-[#ff5900] dark:hover:text-white"
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      <span className="pointer-events-none absolute inset-y-0 right-2 flex items-center text-black/65 dark:text-white/65">
        <ChevronDown />
      </span>
    </label>
  );
}

function CompactFilterSelect({
  dropdownId,
  openDropdownId,
  setOpenDropdownId,
  label,
  value,
  onChange,
  options,
  tooltipPlacement = 'top',
}: {
  dropdownId: string;
  openDropdownId: string | null;
  setOpenDropdownId: (value: string | null) => void;
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: Array<[string, string]>;
  tooltipPlacement?: 'top' | 'bottom' | 'left' | 'right';
}) {
  const active = value !== 'all';
  const isOpen = openDropdownId === dropdownId;
  const selectedLabel = options.find(([optionValue]) => optionValue === value)?.[1] || label;

  return (
    <FilterFieldShell label={label} active={active} tooltipPlacement={tooltipPlacement}>
      <div
        className="relative"
        onMouseEnter={() => setOpenDropdownId(dropdownId)}
        onMouseLeave={() => {
          if (openDropdownId === dropdownId) {
            setOpenDropdownId(null);
          }
        }}
      >
        <button
          type="button"
          onClick={() => {
            if (active) {
              onChange('all');
              setOpenDropdownId(null);
              return;
            }
            setOpenDropdownId(isOpen ? null : dropdownId);
          }}
          className={`flex h-[22px] w-full items-center justify-between rounded-[10px] border px-1.5 text-[13px] font-semibold leading-none outline-none transition ${
            active
              ? 'border-[#ff5900] bg-[#ff5900] text-white dark:border-[#ff5900] dark:bg-[#ff5900] dark:text-white'
              : 'border-black/10 bg-white text-[#0d0d0d] hover:border-[#ff5900] hover:bg-[#ff5900] hover:text-[#0d0d0d] dark:border-white/10 dark:bg-[#1a1a1a] dark:text-white dark:hover:border-[#ff5900] dark:hover:bg-[#ff5900] dark:hover:text-white'
          }`}
        >
          <span className="truncate">{selectedLabel}</span>
          <ChevronDown />
        </button>
        {isOpen ? (
          <div className="absolute left-0 top-full z-[10050] max-h-64 w-full overflow-y-auto rounded-[11px] border border-black/10 bg-white p-1 shadow-[0_18px_44px_rgba(15,23,42,0.12)] dark:border-white/10 dark:bg-[#1a1a1a]">
            {options.map(([optionValue, optionLabel]) => (
              <DropdownOption
                key={`${label}-${optionValue}`}
                active={optionValue === value}
                label={optionLabel}
                onClick={() => {
                  if (optionValue === value) {
                    onChange('all');
                    setOpenDropdownId(null);
                    return;
                  }
                  onChange(optionValue);
                  setOpenDropdownId(null);
                }}
              />
            ))}
          </div>
        ) : null}
      </div>
    </FilterFieldShell>
  );
}

function AccountSelectControl({
  accountId,
  accounts,
  onChooseAccount,
  onOpenAccountPicker,
}: {
  accountId: string | null;
  accounts: AccountSummary[];
  onChooseAccount: (accountId: string) => void;
  onOpenAccountPicker: () => void;
}) {
  return (
    <div className="relative min-w-[142px]">
      <select
        value={accountId || ''}
        onChange={(event) => {
          if (event.target.value === '__manage__') {
            onOpenAccountPicker();
            return;
          }
          if (event.target.value) onChooseAccount(event.target.value);
        }}
        onMouseEnter={(event) => maybeOpenHoveredSelect(event.currentTarget)}
        className="h-[22px] w-full appearance-none rounded-[10px] border border-[#ff5900] bg-[#ff5900] px-1.5 text-sm font-semibold leading-none text-white outline-none shadow-[0_12px_28px_rgba(255,89,0,0.2)]"
      >
        {!accountId ? <option value="">Select Account</option> : null}
        {accounts.map((item) => (
          <option key={item.account_id} value={item.account_id}>
            {item.account_name || item.account_id}
          </option>
        ))}
        <option value="__manage__">Manage Accounts</option>
      </select>
    </div>
  );
}

function BucketOrCustomFilter({
  dropdownId,
  openDropdownId,
  setOpenDropdownId,
  label,
  value,
  onChange,
  options,
  tooltipPlacement = 'top',
}: {
  dropdownId: string;
  openDropdownId: string | null;
  setOpenDropdownId: (value: string | null) => void;
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: Array<[string, string]>;
  tooltipPlacement?: 'top' | 'bottom' | 'left' | 'right';
}) {
  const mode = value.startsWith('custom:') ? 'custom' : value;
  const [customMin, customMax] = parseCustomRange(value);
  const active = value !== 'all';
  const isOpen = openDropdownId === dropdownId;
  const selectedLabel = options.find(([optionValue]) => optionValue === mode)?.[1] || label;

  return (
    <FilterFieldShell label={label} active={active} tooltipPlacement={tooltipPlacement}>
      <div
        className="relative"
        onMouseEnter={() => setOpenDropdownId(dropdownId)}
        onMouseLeave={() => {
          if (openDropdownId === dropdownId) {
            setOpenDropdownId(null);
          }
        }}
      >
        <button
          type="button"
          onClick={() => {
            if (active) {
              onChange('all');
              setOpenDropdownId(null);
              return;
            }
            setOpenDropdownId(isOpen ? null : dropdownId);
          }}
          className={`flex h-[22px] w-full items-center justify-between rounded-[10px] border px-1.5 text-[13px] font-semibold leading-none outline-none transition ${
            active
              ? 'border-[#ff5900] bg-[#ff5900] text-white dark:border-[#ff5900] dark:bg-[#ff5900] dark:text-white'
              : 'border-black/10 bg-white text-[#0d0d0d] hover:border-[#ff5900] hover:bg-[#ff5900] hover:text-[#0d0d0d] dark:border-white/10 dark:bg-[#1a1a1a] dark:text-white dark:hover:border-[#ff5900] dark:hover:bg-[#ff5900] dark:hover:text-white'
          }`}
        >
          <span className="truncate">{selectedLabel}</span>
          <ChevronDown />
        </button>
        {isOpen ? (
          <div className="absolute left-0 top-full z-[10050] w-full rounded-[11px] border border-black/10 bg-white p-1 shadow-[0_18px_44px_rgba(15,23,42,0.12)] dark:border-white/10 dark:bg-[#1a1a1a]">
            {options.map(([optionValue, optionLabel]) => (
              <DropdownOption
                key={`${label}-${optionValue}`}
                active={optionValue === mode}
                label={optionLabel}
                onClick={() => {
                  if (optionValue === mode) {
                    onChange('all');
                    setOpenDropdownId(null);
                    return;
                  }
                  if (optionValue === 'custom') {
                    onChange(serializeCustomRange(customMin, customMax));
                    return;
                  }
                  onChange(optionValue);
                  setOpenDropdownId(null);
                }}
              />
            ))}
            {mode === 'custom' ? (
              <div className="mt-1 grid grid-cols-2 gap-1 px-1 pb-1">
                <input
                  type="text"
                  inputMode="decimal"
                  value={customMin}
                  onChange={(event) => onChange(serializeCustomRange(event.target.value, customMax))}
                  placeholder="Min"
                  className="h-[22px] w-full rounded-[10px] border border-black/10 bg-white px-1.5 text-[13px] font-semibold leading-none text-[#0d0d0d] outline-none placeholder:text-black/45 hover:border-[#ff5900] hover:bg-[#ff5900] hover:text-[#0d0d0d] dark:border-white/10 dark:bg-[#1a1a1a] dark:text-white dark:placeholder:text-white/40 dark:hover:border-[#ff5900] dark:hover:bg-[#ff5900] dark:hover:text-white"
                />
                <input
                  type="text"
                  inputMode="decimal"
                  value={customMax}
                  onChange={(event) => onChange(serializeCustomRange(customMin, event.target.value))}
                  placeholder="Max"
                  className="h-[22px] w-full rounded-[10px] border border-black/10 bg-white px-1.5 text-[13px] font-semibold leading-none text-[#0d0d0d] outline-none placeholder:text-black/45 hover:border-[#ff5900] hover:bg-[#ff5900] hover:text-[#0d0d0d] dark:border-white/10 dark:bg-[#1a1a1a] dark:text-white dark:placeholder:text-white/40 dark:hover:border-[#ff5900] dark:hover:bg-[#ff5900] dark:hover:text-white"
                />
              </div>
            ) : null}
          </div>
        ) : null}
      </div>
    </FilterFieldShell>
  );
}

function FilterFieldShell({
  label,
  active,
  children,
  tooltipPlacement = 'top',
}: {
  label: string;
  active: boolean;
  children: React.ReactNode;
  tooltipPlacement?: 'top' | 'bottom' | 'left' | 'right';
}) {
  const tooltipPlacementClass =
    tooltipPlacement === 'bottom'
      ? 'top-full mt-1'
      : tooltipPlacement === 'left'
        ? 'right-full top-1/2 mr-2 -translate-y-1/2'
        : tooltipPlacement === 'right'
          ? 'left-full top-1/2 ml-2 -translate-y-1/2'
          : 'bottom-full mb-1';

  return (
    <label className="group relative z-0 block w-full overflow-visible hover:z-30">
      <span className="sr-only">{label}</span>
      {children}
      {active ? (
        <span
          className={`pointer-events-none absolute z-50 whitespace-nowrap rounded-full bg-[#ff5900] px-2 py-[2px] text-[10px] font-semibold text-white opacity-0 shadow-[0_12px_28px_rgba(255,89,0,0.24)] transition duration-75 group-hover:opacity-100 ${tooltipPlacementClass} ${
            tooltipPlacement === 'top' || tooltipPlacement === 'bottom' ? 'left-1/2 -translate-x-1/2' : ''
          }`}
        >
          {label}
        </span>
      ) : null}
    </label>
  );
}

function DropdownOption({
  active,
  label,
  onClick,
}: {
  active: boolean;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onMouseDown={(event) => {
        event.preventDefault();
        onClick();
      }}
      onPointerDown={(event) => {
        event.preventDefault();
        onClick();
      }}
      className={`flex w-full items-center rounded-[8px] px-1.5 py-0.5 text-left text-[13px] font-semibold transition ${
        active
          ? 'bg-[#ff5900] text-white dark:bg-[#ff5900] dark:text-white'
          : 'text-[#0d0d0d] hover:bg-[#ff5900] hover:text-[#0d0d0d] dark:text-white dark:hover:bg-[#ff5900] dark:hover:text-white'
      }`}
    >
      {label}
    </button>
  );
}

function ChevronDown() {
  return (
    <svg viewBox="0 0 20 20" className="h-3.5 w-3.5 shrink-0" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="m6 8 4 4 4-4" />
    </svg>
  );
}

const DATE_OPTIONS: Array<[string, string]> = [
  ['all', 'All Dates'],
  ['today', 'Today'],
  ['yesterday', 'Yesterday'],
  ['this_week', 'This Wk.'],
  ['last_week', 'Last Wk.'],
  ['this_month', 'This Mo.'],
  ['last_month', 'Last Mo.'],
  ['last_3_months', 'Last 3 Mo.'],
  ['this_year', 'This Yr.'],
  ['last_year', 'Last Yr.'],
];
const TIME_OPTIONS = Array.from({ length: 24 }, (_, hour) => {
  const next = (hour + 1) % 24;
  return [String(hour), `${String(hour).padStart(2, '0')}:00-${String(next).padStart(2, '0')}:00`] as [string, string];
});
const DAY_OPTIONS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'].map((day) => [day, day] as [string, string]);
const HOLD_TIME_OPTIONS: Array<[string, string]> = [
  ['under_15m', 'Under 15m'],
  ['15m_1h', '15m-1h'],
  ['1h_4h', '1h-4h'],
  ['4h_plus', '4h+'],
];
const STATUS_OPTIONS: Array<[string, string]> = [
  ['open', 'Open'],
  ['closed', 'Closed'],
];
const YES_NO_OPTIONS: Array<[string, string]> = [
  ['yes', 'Yes'],
  ['no', 'No'],
];

function uniqueSorted(values: string[]) {
  return Array.from(new Set(values.filter(Boolean))).sort((a, b) => a.localeCompare(b));
}

function humanize(value: string) {
  return value.replace(/_/g, ' ').replace(/\b\w/g, (match) => match.toUpperCase());
}

function percentile(values: number[], percentileValue: number) {
  if (!values.length) return 0;
  const sorted = [...values].sort((a, b) => a - b);
  const index = Math.min(sorted.length - 1, Math.max(0, Math.floor((sorted.length - 1) * percentileValue)));
  return sorted[index] ?? 0;
}

function buildBucketOptions(values: number[], formatter: (value: number) => string): Array<[string, string]> {
  if (!values.length) {
    return [
      ['low', 'Low'],
      ['medium', 'Medium'],
      ['high', 'High'],
      ['custom', 'Custom'],
    ];
  }
  const low = percentile(values, 0.33);
  const high = percentile(values, 0.66);
  return [
    ['low', `Low (<= ${formatter(low)})`],
    ['medium', `Medium (${formatter(low)} to ${formatter(high)})`],
    ['high', `High (>= ${formatter(high)})`],
    ['custom', 'Custom'],
  ];
}

function formatBucketNumber(value: number) {
  if (!Number.isFinite(value)) return '0';
  if (Math.abs(value) >= 1000) return value.toLocaleString(undefined, { maximumFractionDigits: 0 });
  if (Math.abs(value) >= 10) return value.toLocaleString(undefined, { maximumFractionDigits: 1 });
  return value.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

function formatCurrencyBucket(value: number) {
  if (!Number.isFinite(value)) return '$0';
  return `$${formatBucketNumber(value)}`;
}

function parseCustomRange(value: string): [string, string] {
  if (!value.startsWith('custom:')) return ['', ''];
  const [min = '', max = ''] = value.slice('custom:'.length).split(':');
  return [min, max];
}

function serializeCustomRange(min: string, max: string) {
  return `custom:${min.trim()}:${max.trim()}`;
}

function getSpreadValues(trades: TradeRecord[]) {
  return trades.map((trade) => Number(trade.entry_spread || 0)).filter((value) => Number.isFinite(value));
}
function getSlippageValues(trades: TradeRecord[]) {
  return trades.map((trade) => Math.abs(Number(trade.slippage_at_entry || 0)) + Math.abs(Number(trade.slippage_at_exit || 0))).filter((value) => Number.isFinite(value));
}
function getQuantityValues(trades: TradeRecord[]) {
  return trades.map((trade) => Number(trade.quantity || 0)).filter((value) => Number.isFinite(value));
}
function getCostValues(trades: TradeRecord[]) {
  return trades.map((trade) => Number(trade.fees || 0) + Number(trade.commission || 0) + Number(trade.swaps || 0) + Number(trade.slippage_cost || 0)).filter((value) => Number.isFinite(value));
}
function getNetPnlValues(trades: TradeRecord[]) {
  return trades.map((trade) => Number(trade.net_pnl || 0)).filter((value) => Number.isFinite(value));
}
function getRiskAmountValues(trades: TradeRecord[]) {
  return trades.map((trade) => Number(trade.risk_amount || 0)).filter((value) => Number.isFinite(value));
}
function getRrrValues(trades: TradeRecord[]) {
  return trades.map((trade) => Number(trade.rrr_at_entry || 0)).filter((value) => Number.isFinite(value));
}
function getRMultipleValues(trades: TradeRecord[]) {
  return trades.map((trade) => Number(trade.r_multiple || 0)).filter((value) => Number.isFinite(value));
}
function getConfidenceValues(trades: TradeRecord[]) {
  return trades.map((trade) => Number(trade.confidence_score || 0)).filter((value) => Number.isFinite(value));
}

function maybeOpenHoveredSelect(selectElement: HTMLSelectElement) {
  if (typeof document === 'undefined') return;
  const activeElement = document.activeElement;
  if (!(activeElement instanceof HTMLSelectElement)) return;
  if (activeElement === selectElement) return;

  selectElement.focus();
  const pickerCapable = selectElement as HTMLSelectElement & { showPicker?: () => void };
  if (typeof pickerCapable.showPicker === 'function') {
    try {
      pickerCapable.showPicker();
    } catch {
      // Native picker opening is browser-restricted; focus is the best fallback.
    }
  }
}
