import type { TradeBundle } from '@/types/prototype';
import { asArray, asRecord, formatCurrency, formatDate, formatDateTime, formatNumber, formatRatio, formatTime } from '@/utils/format';

type TradeBundlePanelProps = {
  bundle: TradeBundle;
};

export function TradeBundlePanel({ bundle }: TradeBundlePanelProps) {
  const trade = bundle.trade;
  if (!trade) {
    return null;
  }

  const preTrade = asRecord(trade.pre_trade_capture);
  const postTrade = asRecord(trade.post_trade_capture);
  const screenshot = bundle.attachments[0];
  const screenshotMeta = asRecord(screenshot?.metadata);
  const preChecklist = asArray<string>(preTrade.selected_checklist);
  const preMandatory = asArray<string>(preTrade.mandatory_checklist);
  const postChecklist = asArray<string>(postTrade.selected_checklist);
  const postMandatory = asArray<string>(postTrade.mandatory_checklist);

  return (
    <div className="space-y-6 text-black dark:text-white">
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <SummaryCard label="Trade ID" value={(trade.trade_id || '').replace(/^mt5_/, '')} helper={`${trade.symbol} · ${trade.market_type || '—'} · ${trade.side}`} />
        <SummaryCard label="Net PnL" value={formatCurrency(Number(trade.net_pnl || 0))} helper={`Gross ${formatCurrency(Number(trade.gross_pnl || 0))} · Cost ${formatCurrency(Number(trade.total_cost || 0))}`} />
        <SummaryCard label="Entry / Exit" value={formatDateTime(trade.entry_time, trade.entry_timezone || 'UTC')} helper={trade.exit_time ? `Exit ${formatDateTime(trade.exit_time, trade.entry_timezone || 'UTC')}` : 'Trade still open'} />
        <SummaryCard label="Setup" value={(() => { const tag = trade.strategy_tag && trade.strategy_tag !== 'MT5 Historical Sync' ? trade.strategy_tag : null; const strat = trade.strategy && trade.strategy !== 'MT5 Historical Sync' ? trade.strategy : null; return tag || strat || '—'; })()} helper={`${trade.probability_bucket || '—'} · ${trade.is_closed ? 'Closed' : 'Open'}`} />
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <div className="space-y-6">
          <Group title="Trade Overview">
            <FieldGrid
              items={[
                ['Account', trade.account_id],
                ['Broker', trade.broker_id || '—'],
                ['Symbol', trade.symbol],
                ['Market Type', trade.market_type || '—'],
                ['Side', trade.side],
                ['Setup', (() => {
                  const tag = trade.strategy_tag && trade.strategy_tag !== 'MT5 Historical Sync' ? trade.strategy_tag : null;
                  const strat = trade.strategy && trade.strategy !== 'MT5 Historical Sync' ? trade.strategy : null;
                  return tag || strat || '—';
                })()],
              ]}
            />
          </Group>

          <Group title="Entry Snapshot">
            <FieldGrid
              items={[
                ['Entry Price', formatNumber(Number(trade.entry_price || 0))],
                ['Entry Time', formatDateTime(trade.entry_time)],
                ['Entry Date', formatDate(trade.entry_time)],
                ['Entry Day', trade.entry_day_of_week || '—'],
                ['Stop Loss at Entry', formatNumber(Number(trade.stop_loss_at_entry || 0))],
                ['Target at Entry', formatNumber(Number(trade.target_at_entry || 0))],
                ['Minimum Target Price', trade.minimum_target_price != null ? formatNumber(Number(trade.minimum_target_price)) : '—'],
              ]}
            />
          </Group>

          <Group title="Exit Snapshot">
            <FieldGrid
              items={[
                ['Exit Price', trade.exit_price != null ? formatNumber(Number(trade.exit_price)) : '—'],
                ['Exit Time', formatDateTime(trade.exit_time)],
                ['Exit Date', formatDate(trade.exit_time)],
                ['Exit Day', trade.exit_day_of_week || '—'],
                ['Exit Reason', trade.exit_reason || '—'],
                ['Closed Before Plan', trade.closed_before_plan ? 'Yes' : 'No'],
              ]}
            />
          </Group>

          <Group title="Economics">
            <FieldGrid
              items={[
                ['Quantity', formatNumber(Number(trade.quantity || 0))],
                ['Commission', formatCurrency(Number(trade.commission || 0))],
                ['Swaps', formatCurrency(Number(trade.swaps || 0))],
                ['Slippage Cost', formatCurrency(Number(trade.slippage_cost || 0))],
                ['Gross PnL', formatCurrency(Number(trade.gross_pnl || 0))],
                ['Net PnL', formatCurrency(Number(trade.net_pnl || 0))],
                ['Risk Amount', formatCurrency(Number(trade.risk_amount || 0))],
                ['Risk Reward Ratio', formatRatio(Number(trade.rrr_at_entry || 0))],
                ['R Multiple', formatRatio(Number(trade.r_multiple || 0))],
              ]}
            />
          </Group>

          <Group title="Execution and Rule Tracking">
            <FieldGrid
              items={[
                ['Checklist Before', asArray<string>(trade.checklist_before).join(', ') || '—'],
                ['Checklist After', asArray<string>(trade.checklist_after).join(', ') || '—'],
                ['Rule Violation Snapshot', asArray<string>(trade.rule_violations_snapshot).join(', ') || '—'],
                ['Notes', trade.notes || bundle.notes[0]?.body || '—'],
                ['Rating', bundle.rating?.value != null ? String(bundle.rating.value) : '—'],
                ['Rating Rationale', bundle.rating?.rationale || '—'],
                ['Tags', bundle.tags.map((tag) => tag.name).join(', ') || '—'],
              ]}
            />
          </Group>
        </div>

        <div className="space-y-6">
          <Group title="Pre-Trade Capture">
            <FieldGrid
              items={[
                ['Strategy', String(preTrade.strategy_name || '—')],
                ['Probability', String(preTrade.probability_bucket || '—')],
                ['Confidence Score', trade.confidence_score != null ? formatNumber(Number(trade.confidence_score)) : '—'],
                ['Checklist Selected', preChecklist.join(', ') || '—'],
                ['Mandatory Checklist', preMandatory.join(', ') || '—'],
                ['All Criteria Selected', preTrade.all_criteria_selected ? 'Yes' : 'No'],
              ]}
            />
          </Group>

          <Group title="Post-Trade Capture">
            <FieldGrid
              items={[
                ['Strategy', String(postTrade.strategy_name || '—')],
                ['Probability', String(postTrade.probability_bucket || '—')],
                ['Confidence Score', trade.confidence_score != null ? formatNumber(Number(trade.confidence_score)) : '—'],
                ['Checklist Selected', postChecklist.join(', ') || '—'],
                ['Mandatory Checklist', postMandatory.join(', ') || '—'],
                ['All Criteria Selected', postTrade.all_criteria_selected ? 'Yes' : 'No'],
                ['Notes', String(postTrade.notes || '—')],
              ]}
            />
          </Group>

          <Group title="Screenshot / Attachment">
            <FieldGrid
              items={[
                ['Attachment Type', screenshot?.attachment_type || '—'],
                ['File Path', screenshot?.file_path || '—'],
                ['Content Type', screenshot?.content_type || '—'],
                ['Capture Request', String(screenshotMeta.capture_request_id || '—')],
              ]}
            />
          </Group>
        </div>
      </section>
    </div>
  );
}

function SummaryCard({ label, value, helper }: { label: string; value: string; helper: string }) {
  return (
    <article className="rounded-[22px] border border-black/10 bg-white p-5 dark:border-white/10 dark:bg-[#060606]">
      <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-gray-500 dark:text-slate-400">{label}</p>
      <p className="mt-3 break-all text-lg font-semibold text-black dark:text-white">{value}</p>
      <p className="mt-2 text-sm text-gray-600 dark:text-slate-300">{helper}</p>
    </article>
  );
}

function Group({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-[26px] border border-black/10 bg-white p-6 dark:border-white/10 dark:bg-[#060606]">
      <h2 className="text-lg font-semibold text-black dark:text-white">{title}</h2>
      <div className="mt-4">{children}</div>
    </section>
  );
}

function FieldGrid({ items }: { items: Array<[string, string]> }) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      {items.map(([label, value]) => (
        <div key={label} className="rounded-[18px] border border-black/8 bg-gray-50 px-4 py-3 dark:border-white/10 dark:bg-[#0b0b0b]">
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-gray-500 dark:text-slate-400">{label}</p>
          <p className="mt-2 break-words text-sm text-black dark:text-white">{value}</p>
        </div>
      ))}
    </div>
  );
}
