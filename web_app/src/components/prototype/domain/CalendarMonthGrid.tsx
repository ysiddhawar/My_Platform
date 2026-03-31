import type { CalendarDaySummary } from '@/types/prototype';
import { formatCurrency, formatMinutes } from '@/utils/format';

type CalendarMonthGridProps = {
  summaries: CalendarDaySummary[];
  selectedDay: string | null;
  onSelectDay: (day: string) => void;
  visibleMonth: number;
  visibleYear: number;
};

const weekdayLabels = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

function toIsoLocalDay(year: number, month: number, day: number) {
  const monthValue = String(month + 1).padStart(2, '0');
  const dayValue = String(day).padStart(2, '0');
  return `${year}-${monthValue}-${dayValue}`;
}

function tone(summary: CalendarDaySummary, maxMagnitude: number) {
  if (summary.trade_count <= 0) {
    return 'border-black/10 bg-white text-black dark:border-white/10 dark:bg-[#060606] dark:text-white';
  }
  const magnitude = Math.min(Math.abs(Number(summary.pnl || 0)) / Math.max(maxMagnitude, 1), 1);
  const alpha = 0.12 + magnitude * 0.18;
  if (Number(summary.pnl || 0) > 0) {
    return `border-emerald-500/20 bg-[rgba(16,185,129,${alpha.toFixed(3)})] text-black dark:text-white`;
  }
  if (Number(summary.pnl || 0) < 0) {
    return `border-rose-500/20 bg-[rgba(244,63,94,${alpha.toFixed(3)})] text-black dark:text-white`;
  }
  return 'border-black/10 bg-gray-50 text-black dark:border-white/10 dark:bg-[#0b0b0b] dark:text-white';
}

export function CalendarMonthGrid({ summaries, selectedDay, onSelectDay, visibleMonth, visibleYear }: CalendarMonthGridProps) {
  if (summaries.length === 0) {
    return null;
  }

  const ordered = [...summaries].sort((a, b) => a.day.localeCompare(b.day));
  const startOfMonth = new Date(visibleYear, visibleMonth, 1);
  const endOfMonth = new Date(visibleYear, visibleMonth + 1, 0);
  const leadingBlanks = startOfMonth.getDay();
  const maxMagnitude = ordered.reduce((max, summary) => Math.max(max, Math.abs(Number(summary.pnl || 0))), 0);
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
    <div className="rounded-[26px] border border-black/10 bg-white p-6 dark:border-white/10 dark:bg-[#060606]">
      <div className="grid grid-cols-7 gap-3">
        {weekdayLabels.map((label) => (
          <div key={label} className="px-2 py-1 text-center text-[11px] font-semibold uppercase tracking-[0.16em] text-black/55 dark:text-white/55">
            {label}
          </div>
        ))}
        {cells.map((cell, index) =>
          cell.type === 'blank' ? (
            <div key={`blank-${index}`} className="min-h-[118px] rounded-[18px] border border-transparent" />
          ) : (
            <button
              key={cell.isoDay}
              type="button"
              onClick={() => onSelectDay(cell.isoDay)}
              className={`min-h-[118px] rounded-[18px] border p-3 text-left transition hover:-translate-y-0.5 ${
                cell.isoDay === selectedDay ? 'border-black bg-black text-white ring-2 ring-black dark:border-white dark:bg-white dark:text-black dark:ring-white' : ''
              } ${cell.isoDay === selectedDay ? '' : cell.summary ? tone(cell.summary, maxMagnitude) : 'border-black/10 bg-white text-black dark:border-white/10 dark:bg-[#060606] dark:text-white'}`}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="text-sm font-semibold">{cell.dayNumber}</span>
                <span className={`text-[11px] ${cell.isoDay === selectedDay ? 'text-white/70 dark:text-black/70' : 'text-black/55 dark:text-white/55'}`}>{cell.summary?.trade_count || 0}T</span>
              </div>
              <p className="mt-3 text-sm font-semibold">{cell.summary ? formatCurrency(Number(cell.summary.pnl || 0)) : '—'}</p>
              <p className={`mt-1 text-xs ${cell.isoDay === selectedDay ? 'text-white/75 dark:text-black/75' : 'text-black/70 dark:text-white/70'}`}>
                {cell.summary ? `${cell.summary.trade_count} trades` : 'No trade'}
              </p>
              <p className={`mt-1 text-xs ${cell.isoDay === selectedDay ? 'text-white/75 dark:text-black/75' : 'text-black/70 dark:text-white/70'}`}>
                {cell.summary ? formatMinutes(Number(cell.summary.total_platform_time_minutes || 0)) : '0m'}
              </p>
            </button>
          ),
        )}
      </div>
    </div>
  );
}
