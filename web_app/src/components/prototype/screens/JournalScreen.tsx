import { useMemo } from 'react';
import { useQuery } from 'react-query';

import { fetchTrades, searchTrades } from '@/api/prototype';
import { TradeTable } from '@/components/prototype/domain/TradeTable';
import { usePrototypeStore } from '@/state/prototypeStore';
import type { TradeRecord } from '@/types/prototype';

function sortTradesNewestFirst(trades: TradeRecord[]): TradeRecord[] {
  return [...trades].sort((a, b) => {
    const dateA = a.entry_date || a.entry_time?.slice(0, 10) || '';
    const dateB = b.entry_date || b.entry_time?.slice(0, 10) || '';
    const cmp = dateB.localeCompare(dateA);
    if (cmp !== 0) return cmp;
    const timeA = a.entry_time || '';
    const timeB = b.entry_time || '';
    return timeB.localeCompare(timeA);
  });
}

export function JournalScreen() {
  const accountId = usePrototypeStore((state) => state.accountId);
  const selectedTradeId = usePrototypeStore((state) => state.selectedTradeId);
  const selectTrade = usePrototypeStore((state) => state.selectTrade);
  const searchText = usePrototypeStore((state) => state.journalSearchText);
  const setSearchText = usePrototypeStore((state) => state.setJournalSearchText);

  const { data, isLoading, error, refetch, isFetching } = useQuery(['prototype-trades', accountId], () => fetchTrades(accountId as string), {
    enabled: Boolean(accountId),
  });
  const { data: searchedData, isFetching: isSearching } = useQuery(
    ['prototype-trade-search', accountId, searchText],
    () => searchTrades(accountId as string, searchText),
    { enabled: Boolean(accountId) && searchText.trim().length >= 2 },
  );

  const trades = useMemo(() => {
    const raw = searchText.trim().length >= 2 ? (searchedData || []) : (data || []);
    return sortTradesNewestFirst(raw);
  }, [data, searchedData, searchText]);

  return (
    <div className="flex flex-col h-full gap-4 text-black dark:text-white">
      <div className="flex items-center justify-between gap-4 flex-shrink-0">
        <input
          id="trade-search"
          value={searchText}
          onChange={(event) => setSearchText(event.target.value)}
          placeholder="Search by symbol, strategy, notes, or trade id"
          className="w-full rounded-[18px] border border-black/10 bg-white px-4 py-3 text-sm text-black outline-none transition placeholder:text-gray-400 hover:border-[#ff5900] focus:border-black focus:bg-black focus:text-white dark:border-white/10 dark:bg-[#090909] dark:text-white dark:placeholder:text-slate-500 dark:hover:border-[#ff5900] dark:focus:border-white dark:focus:bg-white dark:focus:text-black"
        />
        <div className="shrink-0 text-sm text-black/65 dark:text-white/65">
          {isSearching ? 'Searching…' : `${trades.length} trade${trades.length === 1 ? '' : 's'}`}
        </div>
      </div>

      {isLoading ? <p className="text-sm text-black/70 dark:text-white/70">Loading trades…</p> : null}
      {error instanceof Error ? <p className="rounded-[20px] border border-rose-500/20 bg-rose-50 px-5 py-4 text-sm text-rose-700 dark:bg-rose-500/10 dark:text-rose-300">{error.message}</p> : null}
      {!isLoading && !error && trades.length === 0 ? (
        <p className="rounded-[20px] border border-dashed border-black/10 px-5 py-6 text-sm text-gray-600 dark:border-white/10 dark:text-slate-400">
          No trades available.
        </p>
      ) : null}

      {trades.length > 0 ? (
        <div className="flex-1 min-h-0">
        <TradeTable
          trades={trades}
          selectedTradeId={selectedTradeId}
          onSelectTrade={selectTrade}
          isRefetching={isFetching}
          onRefresh={() => void refetch()}
        />
      </div>
      ) : null}
    </div>
  );
}
