import { useEffect, useMemo, useRef, useState } from 'react';
import { useQuery } from 'react-query';

import { fetchCalendarDayDetail, fetchCalendarSummaries, fetchTrades } from '@/api/prototype';
import { CalendarDayDrawer } from '@/components/prototype/domain/CalendarDayDrawer';
import { CalendarMonthGrid } from '@/components/prototype/domain/CalendarMonthGrid';
import type { CalendarDaySummary, TradeRecord } from '@/types/prototype';
import { usePrototypeStore } from '@/state/prototypeStore';
import { formatCurrency } from '@/utils/format';
import { summarizeTradeOutcomes } from '@/utils/tradeOutcome';

export function CalendarScreen() {
  const accountId = usePrototypeStore((state) => state.accountId);
  const selectedDay = usePrototypeStore((state) => state.selectedDay);
  const selectDay = usePrototypeStore((state) => state.selectDay);
  const visibleMonth = usePrototypeStore((state) => state.calendarVisibleMonth);
  const visibleYear = usePrototypeStore((state) => state.calendarVisibleYear);
  const setCalendarVisibleMonthYear = usePrototypeStore((state) => state.setCalendarVisibleMonthYear);
  const [detailOpen, setDetailOpen] = useState(false);
  const [detailVisible, setDetailVisible] = useState(false);
  const [detailAnchor, setDetailAnchor] = useState<{ top: number; left: number; width: number; height: number } | null>(null);
  const [isHoveringDetail, setIsHoveringDetail] = useState(false);
  const detailCloseTimer = useRef<number | null>(null);
  const hoverBridgeTimer = useRef<number | null>(null);

  const {
    data: summaries,
    isLoading,
    error,
  } = useQuery(['prototype-calendar-summaries', accountId], () => fetchCalendarSummaries(accountId as string), { enabled: Boolean(accountId) });
  const { data: trades = [] } = useQuery(['prototype-calendar-trades', accountId], () => fetchTrades(accountId as string), { enabled: Boolean(accountId) });

  const today = new Date();
  const currentMonth = today.getMonth();
  const currentYear = today.getFullYear();
  const todayIso = `${currentYear}-${String(currentMonth + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;

  useEffect(() => {
    if (visibleMonth != null && visibleYear != null) {
      return;
    }
    setCalendarVisibleMonthYear(currentMonth, currentYear);
  }, [currentMonth, currentYear, visibleMonth, visibleYear, setCalendarVisibleMonthYear]);

  useEffect(() => {
    if (selectedDay || visibleMonth == null || visibleYear == null) {
      return;
    }
    const nextSelectedDay =
      visibleMonth === currentMonth && visibleYear === currentYear
        ? todayIso
        : `${visibleYear}-${String(visibleMonth + 1).padStart(2, '0')}-01`;
    selectDay(nextSelectedDay);
  }, [currentMonth, currentYear, selectedDay, selectDay, todayIso, visibleMonth, visibleYear]);

  useEffect(() => {
    if (!selectedDay || visibleMonth == null || visibleYear == null) {
      return;
    }
    const selectedDate = new Date(`${selectedDay}T00:00:00`);
    if (selectedDate.getMonth() === visibleMonth && selectedDate.getFullYear() === visibleYear) {
      return;
    }
    delayedLeaveDay();
    setDetailAnchor(null);
    selectDay(`${visibleYear}-${String(visibleMonth + 1).padStart(2, '0')}-01`);
  }, [selectedDay, selectDay, visibleMonth, visibleYear]);

  useEffect(() => {
    if (detailCloseTimer.current) {
      window.clearTimeout(detailCloseTimer.current);
    }
    if (hoverBridgeTimer.current) {
      window.clearTimeout(hoverBridgeTimer.current);
    }
  }, []);

  const shiftSelectedDay = (delta: number) => {
    const seedDay = selectedDay || summaries?.[summaries.length - 1]?.day;
    if (!seedDay) return;
    const nextDate = new Date(`${seedDay}T00:00:00`);
    nextDate.setDate(nextDate.getDate() + delta);
    const nextDay = `${nextDate.getFullYear()}-${String(nextDate.getMonth() + 1).padStart(2, '0')}-${String(nextDate.getDate()).padStart(2, '0')}`;
    selectDay(nextDay);
    setCalendarVisibleMonthYear(nextDate.getMonth(), nextDate.getFullYear());
  };

  const {
    data: detail,
    isLoading: detailLoading,
    error: detailError,
  } = useQuery(
    ['prototype-calendar-day-detail', accountId, selectedDay],
    () => fetchCalendarDayDetail(selectedDay as string, accountId as string),
    { enabled: Boolean(selectedDay && accountId) },
  );

  const visibleSummaries = useMemo(() => {
    if (!summaries || visibleMonth == null || visibleYear == null) {
      return [];
    }
    return summaries.filter((summary) => {
      const day = new Date(`${summary.day}T00:00:00`);
      return day.getMonth() === visibleMonth && day.getFullYear() === visibleYear;
    });
  }, [summaries, visibleMonth, visibleYear]);

  const dayStatsMap = useMemo(() => {
    const map = new Map<string, TradeRecord[]>();
    trades.forEach((trade) => {
      const dayKey = trade.exit_date || (trade.exit_time ? trade.exit_time.slice(0, 10) : null) || trade.entry_date || trade.entry_time.slice(0, 10);
      if (!dayKey) {
        return;
      }
      const bucket = map.get(dayKey) || [];
      bucket.push(trade);
      map.set(dayKey, bucket);
    });

    return Object.fromEntries(
      Array.from(map.entries()).map(([day, entries]) => {
        const closed = entries.filter((trade) => trade.is_closed);
        const outcomeSummary = summarizeTradeOutcomes(closed);
        const winRate = outcomeSummary.winRate;
        const rMultiple = closed.reduce((sum, trade) => sum + resolveTradeRMultiple(trade), 0);
        return [day, { rMultiple, winRate }];
      }),
    ) as Record<string, { rMultiple: number; winRate: number }>;
  }, [trades]);

  const weeklyStats = useMemo(() => {
    if (visibleMonth == null || visibleYear == null) {
      return [];
    }
    const startOfMonth = new Date(visibleYear, visibleMonth, 1);
    const leadingBlanks = startOfMonth.getDay();
    const buckets = new Map<number, CalendarDaySummary[]>();

    visibleSummaries.forEach((summary) => {
      const day = new Date(`${summary.day}T00:00:00`).getDate();
      const weekIndex = Math.floor((leadingBlanks + day - 1) / 7) + 1;
      const existing = buckets.get(weekIndex) || [];
      existing.push(summary);
      buckets.set(weekIndex, existing);
    });

    const maxWeek = Math.max(1, ...Array.from(buckets.keys()));
    return Array.from({ length: maxWeek }, (_, index) => {
      const week = index + 1;
      const entries = buckets.get(week) || [];
      const totalPnl = entries.reduce((sum, item) => sum + Number(item.pnl || 0), 0);
      const tradedDays = entries.filter((item) => item.trade_count > 0).length;
      return {
        week,
        totalPnl,
        tradedDays,
      };
    });
  }, [visibleMonth, visibleYear, visibleSummaries]);

  const floatingCardPosition = useMemo(() => {
    if (!detailAnchor || !detailOpen) {
      return null;
    }
    const cardWidth = 430;
    const viewportWidth = typeof window !== 'undefined' ? window.innerWidth : 1440;
    const viewportHeight = typeof window !== 'undefined' ? window.innerHeight : 900;
    const prefersRight = detailAnchor.left + detailAnchor.width + cardWidth + 24 < viewportWidth;
    const left = prefersRight
      ? detailAnchor.left + detailAnchor.width + 14
      : Math.max(18, detailAnchor.left - cardWidth - 14);
    const top = Math.min(Math.max(18, detailAnchor.top + detailAnchor.height / 2 - 210), viewportHeight - 580);
    return { top, left, width: cardWidth, side: prefersRight ? 'left' : 'right' as 'left' | 'right' };
  }, [detailAnchor, detailOpen]);

  const cancelFloatingDetailClose = () => {
    if (detailCloseTimer.current) {
      window.clearTimeout(detailCloseTimer.current);
      detailCloseTimer.current = null;
    }
  };

  const openFloatingDetail = (day: string, anchorRect: DOMRect) => {
    cancelFloatingDetailClose();
    selectDay(day);
    setDetailAnchor({
      top: anchorRect.top,
      left: anchorRect.left,
      width: anchorRect.width,
      height: anchorRect.height,
    });
    setDetailOpen(true);
    requestAnimationFrame(() => setDetailVisible(true));
  };

  const delayedLeaveDay = () => {
    if (!detailOpen) return;
    // Start delayed close timer when leaving cell
    detailCloseTimer.current = window.setTimeout(() => {
      if (!isHoveringDetail) {
        setDetailOpen(false);
        setDetailVisible(false);
        detailCloseTimer.current = null;
      }
    }, 200);
  };

  const startHoverBridge = () => {
    cancelFloatingDetailClose();
    setIsHoveringDetail(true);
    // Cancel any pending close timer
    if (detailCloseTimer.current) {
      window.clearTimeout(detailCloseTimer.current);
      detailCloseTimer.current = null;
    }
  };

  const endHoverBridge = () => {
    setIsHoveringDetail(false);
    // Start close timer after leaving detail
    if (detailOpen) {
      detailCloseTimer.current = window.setTimeout(() => {
        setDetailOpen(false);
        setDetailVisible(false);
        detailCloseTimer.current = null;
      }, 150);
    }
  };

  return (
    <div className="space-y-6 text-black dark:text-white">
      {isLoading ? <p className="text-sm text-black/70 dark:text-white/70">Loading calendar…</p> : null}
      {error instanceof Error ? <p className="rounded-[20px] border border-rose-500/20 bg-rose-50 px-5 py-4 text-sm text-rose-700 dark:bg-rose-500/10 dark:text-rose-300">{error.message}</p> : null}
      {detailError instanceof Error ? <p className="rounded-[20px] border border-rose-500/20 bg-rose-50 px-5 py-4 text-sm text-rose-700 dark:bg-rose-500/10 dark:text-rose-300">{detailError.message}</p> : null}

      <section className="grid gap-2.5 xl:grid-cols-[minmax(0,1.72fr)_220px] 2xl:grid-cols-[minmax(0,1.8fr)_220px]">
        <div>
          {summaries && summaries.length > 0 && visibleMonth != null && visibleYear != null ? (
            <CalendarMonthGrid
              summaries={summaries}
              selectedDay={selectedDay}
              onHoverDay={openFloatingDetail}
              onLeaveDay={delayedLeaveDay}
              visibleMonth={visibleMonth}
              visibleYear={visibleYear}
              statsByDay={dayStatsMap}
            />
          ) : (
            !isLoading && <p className="rounded-[20px] border border-dashed border-black/10 px-5 py-6 text-sm text-gray-600 dark:border-white/10 dark:text-slate-400">No calendar data available.</p>
          )}
        </div>
        <CalendarWeeklyRail weeklyStats={weeklyStats} />
      </section>

      {detailOpen && floatingCardPosition ? (
        <div
          onMouseEnter={startHoverBridge}
          onMouseLeave={endHoverBridge}
          className={`fixed z-[12000] transition-all duration-200 ease-out ${
            detailVisible ? 'pointer-events-auto opacity-100 translate-y-0 scale-100' : 'pointer-events-none opacity-0 translate-y-2 scale-[0.98]'
          }`}
          style={{ top: floatingCardPosition.top, left: floatingCardPosition.left, width: floatingCardPosition.width }}
        >
          <div className="relative">
            <CalendarDayDrawer
              detail={detail || null}
              loading={detailLoading}
              onPrevDay={() => shiftSelectedDay(-1)}
              onNextDay={() => shiftSelectedDay(1)}
              onClose={delayedLeaveDay}
              className="max-h-[80vh] w-full overflow-y-auto shadow-[0_28px_80px_rgba(0,0,0,0.32)]"
            />
            <div
              className={`absolute top-[44px] h-4 w-4 rotate-45 bg-[#333333] ${
                floatingCardPosition.side === 'left'
                  ? '-left-2 border-l border-t border-white/10'
                  : '-right-2 border-r border-t border-white/10'
              }`}
            />
          </div>
        </div>
      ) : null}
    </div>
  );
}

function CalendarWeeklyRail({
  weeklyStats,
}: {
  weeklyStats: Array<{ week: number; totalPnl: number; tradedDays: number }>;
}) {
  return (
    <aside className="space-y-2.5 pt-[24px]">
      <div className="space-y-2">
        {weeklyStats.map((item) => (
          <div
            key={`week-${item.week}`}
            className="h-[96px] rounded-[18px] border border-black/10 bg-white p-3 text-[#0d0d0d] dark:border-white/10 dark:bg-[#2b2b2b] dark:text-white"
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-black/50 dark:text-white/60">Week {item.week}</p>
                <p
                  className={`mt-1 text-[1.2rem] font-semibold tracking-[-0.03em] ${
                    item.totalPnl >= 0
                      ? 'text-[#309c30]'
                      : 'text-[#ff0000]'
                  }`}
                >
                  {formatCurrency(item.totalPnl)}
                </p>
              </div>
            </div>
            <div className="mt-3 flex flex-wrap gap-1.5 text-[11px] font-semibold text-black/65 dark:text-white/70">
              <MiniChip label={`${item.tradedDays} days`} />
            </div>
          </div>
        ))}
      </div>
    </aside>
  );
}

function MiniChip({ label }: { label: string }) {
  return (
    <span className="rounded-full bg-black/6 px-2 py-1 text-black/65 dark:bg-white/10 dark:text-white/70">
      {label}
    </span>
  );
}

function resolveTradeRMultiple(trade: TradeRecord): number {
  const direct = Number(trade.r_multiple);
  if (Number.isFinite(direct)) {
    return direct;
  }
  const netPnl = Number(trade.net_pnl);
  const riskAmount = Number(trade.risk_amount);
  if (Number.isFinite(netPnl) && Number.isFinite(riskAmount) && riskAmount > 0) {
    return netPnl / riskAmount;
  }
  return 0;
}

function MonthStat({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone: 'good' | 'risk' | 'neutral';
}) {
  const toneClass =
    tone === 'good'
      ? 'border-[#309c30]/35 bg-[#309c30]/14 text-[#1f7a1f] dark:text-[#8de08d]'
      : tone === 'risk'
        ? 'border-[#ff0000]/35 bg-[#ff0000]/12 text-[#b30000] dark:text-[#ff8d8d]'
        : 'border-black/10 bg-white text-[#0d0d0d] dark:border-white/10 dark:bg-[#1a1a1a] dark:text-white';

  return (
    <div className={`rounded-[14px] border px-3 py-3 ${toneClass}`}>
      <p className="text-[10px] font-semibold uppercase tracking-[0.15em] opacity-70">{label}</p>
      <p className="mt-1 text-[1.05rem] font-semibold">{value}</p>
    </div>
  );
}
