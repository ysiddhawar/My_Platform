import { useEffect } from 'react';
import { useQuery } from 'react-query';

import { fetchCalendarDayDetail, fetchCalendarSummaries } from '@/api/prototype';
import { CalendarDayDrawer } from '@/components/prototype/domain/CalendarDayDrawer';
import { CalendarMonthGrid } from '@/components/prototype/domain/CalendarMonthGrid';
import { usePrototypeStore } from '@/state/prototypeStore';

export function CalendarScreen() {
  const accountId = usePrototypeStore((state) => state.accountId);
  const selectedDay = usePrototypeStore((state) => state.selectedDay);
  const selectDay = usePrototypeStore((state) => state.selectDay);
  const visibleMonth = usePrototypeStore((state) => state.calendarVisibleMonth);
  const visibleYear = usePrototypeStore((state) => state.calendarVisibleYear);
  const setCalendarVisibleMonthYear = usePrototypeStore((state) => state.setCalendarVisibleMonthYear);

  const {
    data: summaries,
    isLoading,
    error,
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
    setCalendarVisibleMonthYear(date.getMonth(), date.getFullYear());
  }, [selectedDay, summaries, visibleMonth, visibleYear, setCalendarVisibleMonthYear]);

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

  return (
    <div className="space-y-6 text-black dark:text-white">
      {isLoading ? <p className="text-sm text-black/70 dark:text-white/70">Loading calendar…</p> : null}
      {error instanceof Error ? <p className="rounded-[20px] border border-rose-500/20 bg-rose-50 px-5 py-4 text-sm text-rose-700 dark:bg-rose-500/10 dark:text-rose-300">{error.message}</p> : null}
      {detailError instanceof Error ? <p className="rounded-[20px] border border-rose-500/20 bg-rose-50 px-5 py-4 text-sm text-rose-700 dark:bg-rose-500/10 dark:text-rose-300">{detailError.message}</p> : null}

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1.5fr)_320px] 2xl:grid-cols-[minmax(0,1.55fr)_340px]">
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
