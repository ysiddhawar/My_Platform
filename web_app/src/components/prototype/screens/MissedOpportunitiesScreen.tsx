import { useMemo } from 'react';
import { useQuery } from 'react-query';

import { fetchMissedOpportunities } from '@/api/prototype';
import { MissedOpportunityTable } from '@/components/prototype/domain/MissedOpportunityTable';
import { StatCard } from '@/components/prototype/domain/StatCard';
import { usePrototypeStore } from '@/state/prototypeStore';

export function MissedOpportunitiesScreen() {
  const accountId = usePrototypeStore((state) => state.accountId);
  const searchText = usePrototypeStore((state) => state.missedOpportunitySearchText);
  const setSearchText = usePrototypeStore((state) => state.setMissedOpportunitySearchText);
  const { data, isLoading, error } = useQuery(['prototype-missed-opportunities', accountId], () => fetchMissedOpportunities(accountId as string), {
    enabled: Boolean(accountId),
  });

  const opportunities = data || [];
  const filteredOpportunities = useMemo(() => {
    const query = searchText.trim().toLowerCase();
    if (!query) return opportunities;
    return opportunities.filter((item) =>
      [
        item.symbol,
        item.strategy_name,
        item.market_type,
        item.notes || '',
        item.local_date,
        item.local_day_of_week,
      ]
        .join(' ')
        .toLowerCase()
        .includes(query),
    );
  }, [opportunities, searchText]);

  if (isLoading) {
    return <p className="text-sm text-black/70 dark:text-white/70">Loading missed opportunities…</p>;
  }

  if (error instanceof Error) {
    return <p className="rounded-[20px] border border-rose-500/20 bg-rose-50 px-5 py-4 text-sm text-rose-700 dark:bg-rose-500/10 dark:text-rose-300">{error.message}</p>;
  }

  return (
    <div className="space-y-6 text-black dark:text-white">
      <section className="grid gap-4 md:grid-cols-3">
        <StatCard label="Recorded Opportunities" value={String(opportunities.length)} helper="All missed opportunities stored for this account." />
        <StatCard label="Latest Day" value={opportunities[0]?.local_date || '—'} helper="Most recent opportunity date in the loaded list." />
        <StatCard label="Latest Setup" value={opportunities[0]?.strategy_name || '—'} helper="Latest recorded setup name." />
      </section>

      <section className="max-w-xl">
        <label htmlFor="missed-opportunity-search" className="mb-2 block text-sm font-medium text-black/80 dark:text-white/80">
          Search missed opportunities
        </label>
        <input
          id="missed-opportunity-search"
          value={searchText}
          onChange={(event) => setSearchText(event.target.value)}
          placeholder="Search by symbol, strategy, note, or date"
          className="w-full rounded-[18px] border border-black/10 bg-white px-4 py-3 text-sm text-black outline-none transition placeholder:text-gray-400 hover:border-[#ff5900] focus:border-black focus:bg-black focus:text-white dark:border-white/10 dark:bg-[#090909] dark:text-white dark:placeholder:text-slate-500 dark:hover:border-[#ff5900] dark:focus:border-white dark:focus:bg-white dark:focus:text-black"
        />
      </section>

      {filteredOpportunities.length === 0 ? (
        <p className="rounded-[20px] border border-dashed border-black/10 px-5 py-6 text-sm text-gray-600 dark:border-white/10 dark:text-slate-400">
          {searchText.trim() ? 'No missed opportunities matched the current search.' : 'No missed opportunities recorded.'}
        </p>
      ) : (
        <MissedOpportunityTable opportunities={filteredOpportunities} />
      )}
    </div>
  );
}
