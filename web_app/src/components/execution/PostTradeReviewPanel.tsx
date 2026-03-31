import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from 'react-query';

import { endpoints } from '@/api/endpoints';
import { Panel } from '@/components/ui/Panel';

const probabilityOptions = ['<40%', '40%', '50%', '60%', '>60%'];

type JournalTrade = {
  trade_id: string;
  symbol: string;
  setup_name: string;
  is_closed: boolean;
  entry_price: number;
  target_at_entry?: number;
  stop_loss_at_entry?: number;
  pre_trade_capture?: {
    strategy_name?: string;
    selected_checklist?: string[];
  };
};

type StrategyRecord = {
  name: string;
  checklist_items: string[];
};

export function PostTradeReviewPanel() {
  const queryClient = useQueryClient();
  const [tradeId, setTradeId] = useState('');
  const [exitPrice, setExitPrice] = useState('');
  const [exitReason, setExitReason] = useState('manual_exit');
  const [strategySetup, setStrategySetup] = useState('');
  const [probabilityBucket, setProbabilityBucket] = useState('');
  const [selectedChecklist, setSelectedChecklist] = useState<string[]>([]);
  const [notes, setNotes] = useState('');

  const { data: tradeData } = useQuery('journal-trades', async () => {
    const response = await endpoints.getJournalTrades();
    return (response.data?.trades || []) as JournalTrade[];
  });

  const { data: strategies } = useQuery('strategies', async () => {
    const response = await endpoints.listStrategies();
    return (response.data?.strategies || []) as StrategyRecord[];
  });

  const selectedTrade = useMemo(
    () => (tradeData || []).find((trade) => trade.trade_id === tradeId),
    [tradeData, tradeId]
  );

  const selectedStrategy = useMemo(
    () => (strategies || []).find((strategy) => strategy.name === strategySetup),
    [strategies, strategySetup]
  );

  const closeTradeMutation = useMutation(async () => {
    return endpoints.closeTrade({
      trade_id: tradeId,
      exit_price: Number(exitPrice),
      exit_reason: exitReason,
      strategy_setup: strategySetup,
      probability_bucket: probabilityBucket,
      selected_checklist: selectedChecklist,
      notes,
    });
  }, {
    onSuccess: () => {
      queryClient.invalidateQueries('journal-trades');
    }
  });

  return (
    <Panel title="Post-Trade Capture" subtitle="Record post-trade discipline, notes, and close classification">
      <div className="grid gap-4 lg:grid-cols-2">
        <label className="text-sm text-slate-300">
          Trade
          <select className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100" value={tradeId} onChange={(event) => {
            const nextTradeId = event.target.value;
            setTradeId(nextTradeId);
            const trade = (tradeData || []).find((item) => item.trade_id === nextTradeId);
            if (trade) {
              setStrategySetup(trade.setup_name || trade.pre_trade_capture?.strategy_name || '');
              setSelectedChecklist(trade.pre_trade_capture?.selected_checklist || []);
            }
          }}>
            <option value="">Select trade</option>
            {(tradeData || []).map((trade) => (
              <option key={trade.trade_id} value={trade.trade_id}>
                {trade.symbol} · {trade.trade_id.slice(0, 8)} · {trade.is_closed ? 'Closed' : 'Open'}
              </option>
            ))}
          </select>
        </label>
        <label className="text-sm text-slate-300">
          Exit Price
          <input className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100" value={exitPrice} onChange={(event) => setExitPrice(event.target.value)} />
        </label>
        <label className="text-sm text-slate-300">
          Exit Reason
          <select className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100" value={exitReason} onChange={(event) => setExitReason(event.target.value)}>
            <option value="target_hit">Target Hit</option>
            <option value="stop_hit">Stop Hit</option>
            <option value="manual_exit">Manual Exit</option>
          </select>
        </label>
        <label className="text-sm text-slate-300">
          Strategy / Setup
          <select className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100" value={strategySetup} onChange={(event) => setStrategySetup(event.target.value)}>
            <option value="">Select setup</option>
            {(strategies || []).map((strategy) => <option key={strategy.name} value={strategy.name}>{strategy.name}</option>)}
          </select>
        </label>
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
          <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Probability</p>
          <div className="mt-3 grid grid-cols-3 gap-2">
            {probabilityOptions.map((option) => (
              <button key={option} className={`rounded-lg border px-3 py-2 text-sm ${probabilityBucket === option ? 'border-amber-400 bg-amber-950/40 text-amber-200' : 'border-slate-700 bg-slate-900 text-slate-200'}`} onClick={() => setProbabilityBucket(option)}>
                {option}
              </button>
            ))}
          </div>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
          <div className="mb-3 flex items-center justify-between">
            <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Checklist / Criteria</p>
            <button className="text-xs font-semibold text-teal-300" onClick={() => setSelectedChecklist(selectedStrategy?.checklist_items || [])}>Select All</button>
          </div>
          <div className="space-y-2">
            {(selectedStrategy?.checklist_items || []).map((item: string) => (
              <label key={item} className="flex items-center gap-3 rounded-lg border border-slate-800 px-3 py-2 text-sm text-slate-200">
                <input
                  type="checkbox"
                  checked={selectedChecklist.includes(item)}
                  onChange={() =>
                    setSelectedChecklist((current) =>
                      current.includes(item) ? current.filter((value) => value !== item) : [...current, item]
                    )
                  }
                />
                <span>{item}</span>
              </label>
            ))}
          </div>
        </div>
      </div>

      <label className="mt-4 block text-sm text-slate-300">
        Notes
        <textarea className="mt-2 h-24 w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100" value={notes} onChange={(event) => setNotes(event.target.value)} />
      </label>

      {selectedTrade ? (
        <p className="mt-3 text-xs text-slate-400">
          Planned entry {selectedTrade.entry_price} | Stop {selectedTrade.stop_loss_at_entry ?? '--'} | Target {selectedTrade.target_at_entry ?? '--'}
        </p>
      ) : null}

      <div className="mt-4 flex items-center gap-3">
        <button className="rounded-xl bg-accent px-4 py-2 text-sm font-semibold text-white" onClick={() => closeTradeMutation.mutate()}>
          {closeTradeMutation.isLoading ? 'Recording...' : 'Record Post-Trade'}
        </button>
        {closeTradeMutation.isSuccess ? <span className="text-sm text-emerald-300">Post-trade capture recorded.</span> : null}
      </div>
    </Panel>
  );
}
