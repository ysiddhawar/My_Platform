import type { CalendarDaySummary } from '@/types/prototype';
import { formatCurrency, formatPercent, formatNumber } from '@/utils/format';

type CalendarMonthGridProps = {
  summaries: CalendarDaySummary[];
  selectedDay: string | null;
  onHoverDay: (day: string, anchorRect: DOMRect) => void;
  onLeaveDay: () => void;
  visibleMonth: number;
  visibleYear: number;
  statsByDay: Record<string, { rMultiple: number; winRate: number }>;
};

const weekdayLabels = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

function toIsoLocalDay(year: number, month: number, day: number) {
  const monthValue = String(month + 1).padStart(2, '0');
  const dayValue = String(day).padStart(2, '0');
  return `${year}-${monthValue}-${dayValue}`;
}

function tone(summary: CalendarDaySummary): { className: string } {
  if (summary.trade_count <= 0) {
    return {
      className: 'border-black/70 bg-transparent text-black dark:border-white/75 dark:text-white',
    };
  }
  if (Number(summary.pnl || 0) > 0) {
    return {
      className: 'border-[#309c30] bg-[#309c30] text-white dark:text-white',
    };
  }
  if (Number(summary.pnl || 0) < 0) {
    return {
      className: 'border-[#ff0000] bg-[#ff0000] text-white dark:text-white',
    };
  }
  return {
    className: 'border-black/70 bg-transparent text-black dark:border-white/75 dark:text-white',
  };
}

export function CalendarMonthGrid({ summaries, selectedDay, onHoverDay, onLeaveDay, visibleMonth, visibleYear, statsByDay }: CalendarMonthGridProps) {
  if (summaries.length === 0) {
    return null;
  }

  const ordered = [...summaries].sort((a, b) => a.day.localeCompare(b.day));
  const startOfMonth = new Date(visibleYear, visibleMonth, 1);
  const endOfMonth = new Date(visibleYear, visibleMonth + 1, 0);
  const leadingBlanks = startOfMonth.getDay();
  const byDay = new Map(ordered.map((summary) => [summary.day, summary]));

  const cells: Array<{ type: 'blank' } | { type: 'day'; summary?: CalendarDaySummary; isoDay: string; dayNumber: number }> = [];
  for (let index = 0; index < leadingBlanks; index += 1) {
    cells.push({ type: 'blank' });
  }
  for (let day = 1; day <= endOfMonth.getDate(); day += 1) {
    const isoDay = toIsoLocalDay(visibleYear, visibleMonth, day);
    cells.push({ type: 'day', summary: byDay.get(isoDay), isoDay, dayNumber: day });
  }

  return (
      <div className="grid grid-cols-7 gap-2.5">
        {weekdayLabels.map((label) => (
          <div key={label} className="px-1 py-0.5 text-center text-[10px] font-bold uppercase tracking-[0.14em] text-black/55 dark:text-white/65">
            {label}
          </div>
        ))}
        {cells.map((cell, index) =>
          cell.type === 'blank' ? (
            <div key={`blank-${index}`} className="h-[96px] rounded-[14px] border border-transparent" />
          ) : (() => {
            const cellTone = cell.summary ? tone(cell.summary) : { className: 'border-black/70 bg-transparent text-black dark:border-white/75 dark:text-white' };
            const selected = cell.isoDay === selectedDay;
            const dayStats = statsByDay[cell.isoDay] || { rMultiple: 0, winRate: 0 };
            return (
            <button
              key={cell.isoDay}
              type="button"
              onMouseEnter={(event) => onHoverDay(cell.isoDay, event.currentTarget.getBoundingClientRect())}
              onMouseLeave={onLeaveDay}
              className={`group h-[96px] rounded-[14px] border px-2.5 py-2.5 text-left transition hover:-translate-y-0.5 hover:border-[#ff5900] hover:bg-[#ff5900] ${
                selected
                  ? 'border-[#ff5900] bg-[#ff5900] text-white ring-2 ring-[#ff5900]/30 dark:border-[#ff5900] dark:bg-[#ff5900] dark:text-white dark:ring-[#ff5900]/35'
                  : cellTone.className
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <span className={`text-[13px] font-bold ${selected ? 'text-white' : 'group-hover:text-black dark:group-hover:text-white'}`}>{cell.dayNumber}</span>
              </div>
              <p className={`mt-3 text-[13px] font-bold ${selected ? 'text-white' : 'group-hover:text-black dark:group-hover:text-white'}`}>{cell.summary ? formatCurrency(Number(cell.summary.pnl || 0)) : '—'}</p>
              <p className={`mt-1 text-[11px] font-bold ${selected ? 'text-white/80' : 'text-black/70 dark:text-white/70 group-hover:text-black dark:group-hover:text-white'}`}>
                {cell.summary && cell.summary.trade_count > 0 ? `${cell.summary.trade_count} trades` : 'No trade'}
              </p>
              <p className={`mt-1 text-[10px] font-bold ${selected ? 'text-white/75' : 'text-black/65 dark:text-white/70 group-hover:text-black dark:group-hover:text-white'}`}>
                {cell.summary && cell.summary.trade_count > 0
                  ? `${formatNumber(dayStats.rMultiple)}R · ${formatPercent(dayStats.winRate)}`
                  : '—R · —%'}
              </p>
            </button>
          )})(),
        )}
      </div>
  );
}
