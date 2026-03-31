import type { CalendarDayDetail } from '@/types/prototype';
import { formatCurrency, formatDateTime, formatMinutes } from '@/utils/format';

type CalendarDayDrawerProps = {
  detail: CalendarDayDetail | null;
  loading: boolean;
  onPrevDay: () => void;
  onNextDay: () => void;
};

export function CalendarDayDrawer({ detail, loading, onPrevDay, onNextDay }: CalendarDayDrawerProps) {
  return (
    <aside className="rounded-[26px] border border-black/10 bg-white p-6 dark:border-white/10 dark:bg-[#060606]">
      {loading ? <p className="text-sm text-black/70 dark:text-white/70">Loading day detail…</p> : null}
      {!loading && !detail ? <p className="text-sm text-black/70 dark:text-white/70">Select a day to inspect it.</p> : null}
      {detail ? (
        <div className="space-y-5 text-black dark:text-white">
          <div className="space-y-3">
            <div className="grid grid-cols-[auto_1fr_auto] items-center gap-3 rounded-[20px] border border-black/8 bg-gray-50 px-4 py-3 dark:border-white/10 dark:bg-[#0b0b0b]">
              <button
                type="button"
                onClick={onPrevDay}
                className="inline-flex items-center rounded-full border border-black/10 bg-white px-3 py-2 text-xs font-semibold text-black transition hover:border-[#ff5900] hover:text-[#ff5900] dark:border-white/10 dark:bg-[#101010] dark:text-white dark:hover:border-[#ff5900] dark:hover:text-[#ff5900]"
              >
                Prev
              </button>
              <h3 className="text-center text-2xl font-semibold tracking-[-0.05em]">{detail.day}</h3>
              <button
                type="button"
                onClick={onNextDay}
                className="inline-flex items-center justify-self-end rounded-full border border-black/10 bg-white px-3 py-2 text-xs font-semibold text-black transition hover:border-[#ff5900] hover:text-[#ff5900] dark:border-white/10 dark:bg-[#101010] dark:text-white dark:hover:border-[#ff5900] dark:hover:text-[#ff5900]"
              >
                Next
              </button>
            </div>
            <p className="mt-2 text-sm text-black/70 dark:text-white/70">
              {detail.trade_count} trades · {formatCurrency(detail.net_pnl)} · {formatMinutes(detail.total_platform_time_minutes)}
            </p>
          </div>

          <div className="grid gap-3 md:grid-cols-2">
            <Metric label="Net PnL" value={formatCurrency(detail.net_pnl)} />
            <Metric label="Gross PnL" value={formatCurrency(detail.gross_pnl)} />
            <Metric label="Total Cost" value={formatCurrency(detail.total_cost)} />
            <Metric label="Platform Time" value={formatMinutes(detail.total_platform_time_minutes)} />
          </div>

          <Section title="Platform Sessions">
            {detail.platform_sessions.length === 0 ? (
              <EmptyRow text="No platform sessions recorded." />
            ) : (
              detail.platform_sessions.map((session) => (
                <Row
                  key={session.session_id}
                  title={`${session.platform_name} · ${session.local_day_of_week}`}
                  subtitle={`${formatDateTime(session.opened_at)} to ${formatDateTime(session.closed_at)} · ${formatMinutes(session.minutes_within_day || session.duration_minutes)}`}
                />
              ))
            )}
          </Section>

          <Section title="Trades">
            {detail.trades.length === 0 ? (
              <EmptyRow text="No trades on this day." />
            ) : (
              detail.trades.map((trade) => (
                <Row
                  key={trade.trade_id}
                  title={`${trade.symbol} · ${trade.side} · ${formatCurrency(Number(trade.net_pnl || 0))}`}
                  subtitle={`${trade.setup_name || trade.strategy || '—'} · ${formatDateTime(trade.entry_time)}${trade.exit_time ? ` → ${formatDateTime(trade.exit_time)}` : ''}`}
                />
              ))
            )}
          </Section>

          <Section title="Missed Opportunities">
            {detail.missed_opportunities.length === 0 ? (
              <EmptyRow text="No missed opportunities on this day." />
            ) : (
              detail.missed_opportunities.map((item) => (
                <Row
                  key={item.opportunity_id}
                  title={`${item.symbol} · ${item.strategy_name}`}
                  subtitle={`${formatDateTime(item.observed_at)} · Entry ${item.entry_price} · Stop ${item.stop_loss_price} · Target ${item.target_price}`}
                />
              ))
            )}
          </Section>
        </div>
      ) : null}
    </aside>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[18px] border border-black/8 bg-gray-50 px-4 py-3 transition hover:border-[#ff5900] hover:shadow-[0_10px_24px_-18px_rgba(255,89,0,0.28),0_0_0_1px_rgba(255,89,0,0.26)] dark:border-white/10 dark:bg-[#0b0b0b]">
      <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-black/55 dark:text-white/55">{label}</p>
      <p className="mt-2 text-sm font-semibold text-black dark:text-white">{value}</p>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section>
      <h4 className="text-sm font-semibold uppercase tracking-[0.16em] text-black/55 dark:text-white/55">{title}</h4>
      <div className="mt-3 space-y-3">{children}</div>
    </section>
  );
}

function Row({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <div className="rounded-[18px] border border-black/8 bg-gray-50 px-4 py-3 transition hover:border-[#ff5900] hover:shadow-[0_10px_24px_-18px_rgba(255,89,0,0.28),0_0_0_1px_rgba(255,89,0,0.26)] dark:border-white/10 dark:bg-[#0b0b0b]">
      <p className="text-sm font-semibold text-black dark:text-white">{title}</p>
      <p className="mt-1 text-xs text-black/70 dark:text-white/70">{subtitle}</p>
    </div>
  );
}

function EmptyRow({ text }: { text: string }) {
  return <p className="text-sm text-black/70 dark:text-white/70">{text}</p>;
}
