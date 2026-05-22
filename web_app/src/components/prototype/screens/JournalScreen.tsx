import { useMemo } from 'react';
import { useQuery } from 'react-query';

import { fetchTrades, searchTrades } from '@/api/prototype';
import { TradeTable } from '@/components/prototype/domain/TradeTable';
import { usePrototypeStore } from '@/state/prototypeStore';

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
    if (searchText.trim().length >= 2) {
      return searchedData || [];
    }
    return data || [];
  }, [data, searchedData, searchText]);

  return (
    <div className="space-y-6 text-black dark:text-white">
      <section className="flex flex-col gap-4 rounded-[26px] border border-black/10 bg-white p-6 dark:border-white/10 dark:bg-[#060606] lg:flex-row lg:items-end lg:justify-between">
        <h2 className="text-[1.9rem] font-semibold tracking-[-0.05em] text-black dark:text-white">Journal</h2>
        <button
          type="button"
          onClick={() => void refetch()}
          className="inline-flex items-center rounded-full bg-black px-5 py-3 text-sm font-semibold text-white transition hover:border-[#ff5900] hover:text-white hover:shadow-[0_10px_24px_-18px_rgba(255,89,0,0.28),0_0_0_1px_rgba(255,89,0,0.26)] dark:bg-white dark:text-black dark:hover:text-black"
        >
          {isFetching ? 'Refreshing…' : 'Refresh'}
        </button>
      </section>

      <section className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="max-w-xl">
          <label htmlFor="trade-search" className="mb-2 block text-sm font-medium text-black/80 dark:text-white/80">
            Search
          </label>
          <input
            id="trade-search"
            value={searchText}
            onChange={(event) => setSearchText(event.target.value)}
            placeholder="Search by symbol, strategy, notes, or trade id"
            className="w-full rounded-[18px] border border-black/10 bg-white px-4 py-3 text-sm text-black outline-none transition placeholder:text-gray-400 hover:border-[#ff5900] focus:border-black focus:bg-black focus:text-white dark:border-white/10 dark:bg-[#090909] dark:text-white dark:placeholder:text-slate-500 dark:hover:border-[#ff5900] dark:focus:border-white dark:focus:bg-white dark:focus:text-black"
          />
        </div>
        <div className="text-sm text-black/65 dark:text-white/65">
          {isSearching ? 'Searching…' : `${trades.length} trade${trades.length === 1 ? '' : 's'}`}
        </div>
      </section>

      {isLoading ? <p className="text-sm text-black/70 dark:text-white/70">Loading trades…</p> : null}
      {error instanceof Error ? <p className="rounded-[20px] border border-rose-500/20 bg-rose-50 px-5 py-4 text-sm text-rose-700 dark:bg-rose-500/10 dark:text-rose-300">{error.message}</p> : null}
      {!isLoading && !error && trades.length === 0 ? (
        <p className="rounded-[20px] border border-dashed border-black/10 px-5 py-6 text-sm text-gray-600 dark:border-white/10 dark:text-slate-400">
          No trades available.
        </p>
      ) : null}

      {trades.length > 0 ? (
        <TradeTable trades={trades} selectedTradeId={selectedTradeId} onSelectTrade={selectTrade} />
      ) : null}
    </div>
  );
}
