import { useQuery } from 'react-query';

import { endpoints } from '@/api/endpoints';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { Panel } from '@/components/ui/Panel';

type JournalTrade = {
  trade_id: string;
  symbol: string;
  setup_name: string;
  is_closed: boolean;
  net_pnl?: number;
  pre_trade_capture?: Record<string, unknown>;
  post_trade_capture?: Record<string, unknown>;
  line_history?: unknown[];
  notes?: string;
  exit_reason?: string;
  closed_before_plan?: boolean;
  probability_bucket?: string;
};

export default function JournalPage() {
  const { data } = useQuery('journal-trades', async () => {
    const response = await endpoints.getJournalTrades();
    return (response.data?.trades || []) as JournalTrade[];
  });

  const trades = data || [];

  return (
    <DashboardLayout>
      <Panel title="Trade Journal" subtitle="Raw pre-trade, post-trade, and execution records">
        <div className="space-y-4">
          {trades.length === 0 ? <p className="text-sm text-slate-500">No trades recorded yet.</p> : null}
          {trades.map((trade) => (
            <div key={trade.trade_id} className="rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="font-display text-lg font-semibold text-white">{trade.symbol} · {trade.setup_name}</p>
                  <p className="text-xs uppercase tracking-[0.16em] text-slate-500">{trade.trade_id}</p>
                </div>
                <div className="text-right text-sm text-slate-300">
                  <p>{trade.is_closed ? 'closed' : 'open'}</p>
                  <p className="text-xs text-slate-500">Net PnL: {trade.net_pnl ?? '--'}</p>
                </div>
              </div>

              <div className="mt-4 grid gap-4 lg:grid-cols-2">
                <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-3">
                  <p className="text-xs uppercase tracking-[0.16em] text-slate-500">Pre-Trade Capture</p>
                  <pre className="mt-2 overflow-auto whitespace-pre-wrap text-xs text-slate-300">
                    {JSON.stringify(trade.pre_trade_capture || {}, null, 2)}
                  </pre>
                </div>
                <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-3">
                  <p className="text-xs uppercase tracking-[0.16em] text-slate-500">Post-Trade Capture</p>
                  <pre className="mt-2 overflow-auto whitespace-pre-wrap text-xs text-slate-300">
                    {JSON.stringify(trade.post_trade_capture || {}, null, 2)}
                  </pre>
                </div>
              </div>

              <div className="mt-4 grid gap-4 lg:grid-cols-3">
                <DataTile title="Line History" value={JSON.stringify(trade.line_history || [])} />
                <DataTile title="Notes" value={trade.notes || 'No notes'} />
                <DataTile title="Execution Outcome" value={JSON.stringify({
                  exit_reason: trade.exit_reason,
                  closed_before_plan: trade.closed_before_plan,
                  probability_bucket: trade.probability_bucket,
                }, null, 2)} />
              </div>
            </div>
          ))}
        </div>
      </Panel>
    </DashboardLayout>
  );
}

function DataTile({ title, value }: { title: string; value: string }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-3">
      <p className="text-xs uppercase tracking-[0.16em] text-slate-500">{title}</p>
      <pre className="mt-2 overflow-auto whitespace-pre-wrap text-xs text-slate-300">{value}</pre>
    </div>
  );
}
