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
    <aside className="rounded-[22px] border border-white/10 bg-[#333333] p-5 text-white dark:border-white/10 dark:bg-[#333333]">
      {loading ? <p className="text-sm text-black/70 dark:text-white/70">Loading day detail…</p> : null}
      {!loading && !detail ? <p className="text-sm text-black/70 dark:text-white/70">Select a day to inspect it.</p> : null}
      {detail ? (
        <div className="space-y-4 text-white dark:text-white">
          <div className="space-y-2">
            <div className="grid grid-cols-[auto_1fr_auto] items-center gap-2 rounded-[18px] border border-white/10 bg-[#404040] px-3 py-2.5 dark:border-white/10 dark:bg-[#404040]">
              <button
                type="button"
                onClick={onPrevDay}
                className="inline-flex items-center rounded-full border border-white/10 bg-black px-3 py-1.5 text-[11px] font-semibold text-white transition hover:border-[#ff5900] hover:text-[#ff5900] dark:border-white/10 dark:bg-black dark:text-white dark:hover:border-[#ff5900] dark:hover:text-[#ff5900]"
              >
                Prev
              </button>
              <h3 className="text-center text-[1.45rem] font-semibold tracking-[-0.04em]">{detail.day}</h3>
              <button
                type="button"
                onClick={onNextDay}
                className="inline-flex items-center justify-self-end rounded-full border border-white/10 bg-black px-3 py-1.5 text-[11px] font-semibold text-white transition hover:border-[#ff5900] hover:text-[#ff5900] dark:border-white/10 dark:bg-black dark:text-white dark:hover:border-[#ff5900] dark:hover:text-[#ff5900]"
              >
                Next
              </button>
            </div>
            <p className="mt-1 text-[13px] text-white/72 dark:text-white/72">
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
    <div className="rounded-[16px] border border-white/10 bg-[#404040] px-3 py-3 transition hover:border-[#ff5900] hover:shadow-[0_10px_24px_-18px_rgba(255,89,0,0.28),0_0_0_1px_rgba(255,89,0,0.26)] dark:border-white/10 dark:bg-[#404040]">
      <p className="text-[10px] font-semibold uppercase tracking-[0.15em] text-white/60 dark:text-white/60">{label}</p>
      <p className="mt-1.5 text-[13px] font-semibold text-white dark:text-white">{value}</p>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section>
      <h4 className="text-[11px] font-semibold uppercase tracking-[0.16em] text-white/60 dark:text-white/60">{title}</h4>
      <div className="mt-2.5 space-y-2.5">{children}</div>
    </section>
  );
}

function Row({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <div className="rounded-[16px] border border-white/10 bg-[#404040] px-3 py-3 transition hover:border-[#ff5900] hover:shadow-[0_10px_24px_-18px_rgba(255,89,0,0.28),0_0_0_1px_rgba(255,89,0,0.26)] dark:border-white/10 dark:bg-[#404040]">
      <p className="text-[13px] font-semibold text-white dark:text-white">{title}</p>
      <p className="mt-1 text-[11px] leading-5 text-white/72 dark:text-white/72">{subtitle}</p>
    </div>
  );
}

function EmptyRow({ text }: { text: string }) {
  return <p className="text-sm text-white/70 dark:text-white/70">{text}</p>;
}
