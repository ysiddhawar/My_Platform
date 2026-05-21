import { useMemo } from 'react';
import { useQuery } from 'react-query';

import { fetchTradeBundle, fetchTrades } from '@/api/prototype';
import type { TradeBundle, TradeRecord } from '@/types/prototype';
import { TradeBundlePanel } from '@/components/prototype/domain/TradeBundlePanel';
import { usePrototypeStore } from '@/state/prototypeStore';

export function TradeDetailScreen() {
  const accountId = usePrototypeStore((state) => state.accountId);
  const selectedTradeId = usePrototypeStore((state) => state.selectedTradeId);
  const setActiveView = usePrototypeStore((state) => state.setActiveView);

  const { data: trades } = useQuery<TradeRecord[]>(
    ['prototype-trades', accountId],
    () => fetchTrades(accountId as string),
    {
      enabled: Boolean(accountId),
      staleTime: 60_000,
    },
  );

  const { data, isLoading, error } = useQuery<TradeBundle>(
    ['prototype-trade-bundle', selectedTradeId],
    () => fetchTradeBundle(selectedTradeId as string),
    { enabled: Boolean(selectedTradeId) },
  );

  const tradeFromList = useMemo(
    () => (trades ?? []).find((trade) => trade.trade_id === selectedTradeId) ?? null,
    [trades, selectedTradeId],
  );

  if (!selectedTradeId) {
    return (
      <section className="rounded-[24px] border border-dashed border-black/10 px-8 py-14 text-center dark:border-white/10">
        <h2 className="text-2xl font-semibold tracking-[-0.05em] text-black dark:text-white">Select a trade first</h2>
        <button
          type="button"
          onClick={() => setActiveView('journal')}
          className="mt-6 inline-flex items-center rounded-full bg-black px-5 py-3 text-sm font-semibold text-white transition hover:brightness-110 dark:bg-white dark:text-black"
        >
          Open Journal
        </button>
      </section>
    );
  }

  if (isLoading) {
    return <p className="text-sm text-gray-600 dark:text-slate-400">Loading trade detail…</p>;
  }

  if (error instanceof Error) {
    return <p className="rounded-[20px] border border-rose-500/20 bg-rose-50 px-5 py-4 text-sm text-rose-700 dark:bg-rose-500/10 dark:text-rose-300">{error.message}</p>;
  }

  if (!data?.trade && !tradeFromList) {
    return <p className="text-sm text-gray-600 dark:text-slate-400">No trade data returned.</p>;
  }

  const mergedBundle: TradeBundle = {
    ...data!,
    trade: tradeFromList ?? data?.trade ?? null,
  };

  if (!mergedBundle.trade) {
    return <p className="text-sm text-gray-600 dark:text-slate-400">No trade data available.</p>;
  }

  return <TradeBundlePanel bundle={mergedBundle} />;
}
