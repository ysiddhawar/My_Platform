import { useEffect, useMemo, useState } from 'react';
import { useQuery, useQueryClient } from 'react-query';

import { fetchCalendarDayDetail, fetchCalendarSummaries, rebuildCalendar } from '@/api/prototype';
import { CalendarDayDrawer } from '@/components/prototype/domain/CalendarDayDrawer';
import { CalendarMonthGrid } from '@/components/prototype/domain/CalendarMonthGrid';
import { usePrototypeStore } from '@/state/prototypeStore';

export function CalendarScreen() {
  const accountId = usePrototypeStore((state) => state.accountId);
  const selectedDay = usePrototypeStore((state) => state.selectedDay);
  const selectDay = usePrototypeStore((state) => state.selectDay);
  const queryClient = useQueryClient();

  const [visibleMonth, setVisibleMonth] = useState<number | null>(null);
  const [visibleYear, setVisibleYear] = useState<number | null>(null);

  const {
    data: summaries,
    isLoading,
    error,
    isFetching,
  } = useQuery(['prototype-calendar-summaries', accountId], () => fetchCalendarSummaries(accountId as string), { enabled: Boolean(accountId) });

  useEffect(() => {
    if (!selectedDay && summaries && summaries.length > 0) {
      const ordered = [...summaries].sort((a, b) => a.day.localeCompare(b.day));
      selectDay(ordered[ordered.length - 1].day);
    }
  }, [selectedDay, selectDay, summaries]);

  useEffect(() => {
    if (visibleMonth != null && visibleYear != null) {
      return;
    }
    const seedDay = selectedDay || summaries?.[summaries.length - 1]?.day;
    if (!seedDay) {
      return;
    }
    const date = new Date(`${seedDay}T00:00:00`);
    setVisibleMonth(date.getMonth());
    setVisibleYear(date.getFullYear());
  }, [selectedDay, summaries, visibleMonth, visibleYear]);

  const monthLabel = useMemo(() => {
    if (visibleMonth == null || visibleYear == null) return '';
    return new Date(visibleYear, visibleMonth, 1).toLocaleString('en-US', {
      month: 'long',
      year: 'numeric',
    });
  }, [visibleMonth, visibleYear]);

  const shiftMonth = (delta: number) => {
    if (visibleMonth == null || visibleYear == null) return;
    const nextDate = new Date(visibleYear, visibleMonth + delta, 1);
    setVisibleMonth(nextDate.getMonth());
    setVisibleYear(nextDate.getFullYear());
  };

  const shiftSelectedDay = (delta: number) => {
    const seedDay = selectedDay || summaries?.[summaries.length - 1]?.day;
    if (!seedDay) return;
    const nextDate = new Date(`${seedDay}T00:00:00`);
    nextDate.setDate(nextDate.getDate() + delta);
    const nextDay = `${nextDate.getFullYear()}-${String(nextDate.getMonth() + 1).padStart(2, '0')}-${String(nextDate.getDate()).padStart(2, '0')}`;
    selectDay(nextDay);
    setVisibleMonth(nextDate.getMonth());
    setVisibleYear(nextDate.getFullYear());
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

  return (
    <div className="space-y-6 text-black dark:text-white">
      <section className="flex items-center justify-between rounded-[26px] border border-black/10 bg-white p-6 dark:border-white/10 dark:bg-[#060606]">
        <div>
          <h2 className="text-[1.9rem] font-semibold tracking-[-0.05em] text-black dark:text-white">Calendar</h2>
          <p className="mt-2 text-sm text-black/75 dark:text-white/70">Monthly view with daily PnL, trade count, and per-day platform time.</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => shiftMonth(-1)}
            className="inline-flex items-center rounded-full border border-black/10 bg-white px-4 py-3 text-sm font-semibold text-black transition hover:border-[#ff5900] hover:text-[#ff5900] dark:border-white/10 dark:bg-[#0b0b0b] dark:text-white dark:hover:border-[#ff5900] dark:hover:text-[#ff5900]"
          >
            Prev
          </button>
          <div className="min-w-[160px] text-center text-sm font-semibold text-black dark:text-white">{monthLabel || 'Calendar'}</div>
          <button
            type="button"
            onClick={() => shiftMonth(1)}
            className="inline-flex items-center rounded-full border border-black/10 bg-white px-4 py-3 text-sm font-semibold text-black transition hover:border-[#ff5900] hover:text-[#ff5900] dark:border-white/10 dark:bg-[#0b0b0b] dark:text-white dark:hover:border-[#ff5900] dark:hover:text-[#ff5900]"
          >
            Next
          </button>
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
            className="inline-flex items-center rounded-full bg-black px-5 py-3 text-sm font-semibold text-white transition hover:border-[#ff5900] hover:text-white hover:shadow-[0_10px_24px_-18px_rgba(255,89,0,0.28),0_0_0_1px_rgba(255,89,0,0.26)] dark:bg-white dark:text-black dark:hover:text-black"
          >
            {isFetching ? 'Refreshing…' : 'Refresh'}
          </button>
        </div>
      </section>

      {isLoading ? <p className="text-sm text-black/70 dark:text-white/70">Loading calendar…</p> : null}
      {error instanceof Error ? <p className="rounded-[20px] border border-rose-500/20 bg-rose-50 px-5 py-4 text-sm text-rose-700 dark:bg-rose-500/10 dark:text-rose-300">{error.message}</p> : null}
      {detailError instanceof Error ? <p className="rounded-[20px] border border-rose-500/20 bg-rose-50 px-5 py-4 text-sm text-rose-700 dark:bg-rose-500/10 dark:text-rose-300">{detailError.message}</p> : null}

      <section className="grid gap-6 xl:grid-cols-[1.25fr_0.85fr]">
        <div>
          {summaries && summaries.length > 0 && visibleMonth != null && visibleYear != null ? (
            <CalendarMonthGrid
              summaries={summaries}
              selectedDay={selectedDay}
              onSelectDay={selectDay}
              visibleMonth={visibleMonth}
              visibleYear={visibleYear}
            />
          ) : (
            !isLoading && <p className="rounded-[20px] border border-dashed border-black/10 px-5 py-6 text-sm text-gray-600 dark:border-white/10 dark:text-slate-400">No calendar data available.</p>
          )}
        </div>
        <CalendarDayDrawer
          detail={detail || null}
          loading={detailLoading}
          onPrevDay={() => shiftSelectedDay(-1)}
          onNextDay={() => shiftSelectedDay(1)}
        />
      </section>
    </div>
  );
}
