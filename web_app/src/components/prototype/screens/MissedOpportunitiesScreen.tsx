import { useQuery } from 'react-query';

import { fetchMissedOpportunities } from '@/api/prototype';
import { MissedOpportunityTable } from '@/components/prototype/domain/MissedOpportunityTable';
import { StatCard } from '@/components/prototype/domain/StatCard';
import { usePrototypeStore } from '@/state/prototypeStore';

export function MissedOpportunitiesScreen() {
  const accountId = usePrototypeStore((state) => state.accountId);
  const { data, isLoading, error } = useQuery(['prototype-missed-opportunities', accountId], () => fetchMissedOpportunities(accountId as string), {
    enabled: Boolean(accountId),
  });

  if (isLoading) {
    return <p className="text-sm text-black/70 dark:text-white/70">Loading missed opportunities…</p>;
  }

  if (error instanceof Error) {
    return <p className="rounded-[20px] border border-rose-500/20 bg-rose-50 px-5 py-4 text-sm text-rose-700 dark:bg-rose-500/10 dark:text-rose-300">{error.message}</p>;
  }

  const opportunities = data || [];

  return (
    <div className="space-y-6 text-black dark:text-white">
      <section className="grid gap-4 md:grid-cols-3">
        <StatCard label="Recorded Opportunities" value={String(opportunities.length)} helper="All missed opportunities stored for this account." />
        <StatCard label="Latest Day" value={opportunities[0]?.local_date || '—'} helper="Most recent opportunity date in the loaded list." />
        <StatCard label="Latest Setup" value={opportunities[0]?.strategy_name || '—'} helper="Latest recorded setup name." />
      </section>

      {opportunities.length === 0 ? (
        <p className="rounded-[20px] border border-dashed border-black/10 px-5 py-6 text-sm text-gray-600 dark:border-white/10 dark:text-slate-400">
          No missed opportunities recorded.
        </p>
      ) : (
        <MissedOpportunityTable opportunities={opportunities} />
      )}
    </div>
  );
}
