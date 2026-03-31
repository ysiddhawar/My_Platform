import { useState } from 'react';
import { useMutation, useQueryClient } from 'react-query';

import { importTradeCsv, rebuildCalendar, seedInvestorDemoPack } from '@/api/prototype';
import { usePrototypeStore } from '@/state/prototypeStore';

export function DemoDataScreen() {
  const accountId = usePrototypeStore((state) => state.accountId);
  const queryClient = useQueryClient();
  const [selectedFileName, setSelectedFileName] = useState<string | null>(null);

  const refreshPrototypeQueries = async () => {
    await Promise.all([
      queryClient.invalidateQueries(['prototype-overview', accountId]),
      queryClient.invalidateQueries(['prototype-trades', accountId]),
      queryClient.invalidateQueries(['prototype-missed-opportunities', accountId]),
      queryClient.invalidateQueries(['prototype-calendar-summaries', accountId]),
    ]);
  };

  const seedMutation = useMutation(() => seedInvestorDemoPack(accountId as string), {
    onSuccess: async () => {
      await refreshPrototypeQueries();
    },
  });

  const rebuildMutation = useMutation(() => rebuildCalendar(accountId as string), {
    onSuccess: async () => {
      await queryClient.invalidateQueries(['prototype-calendar-summaries', accountId]);
    },
  });

  const importMutation = useMutation((csvText: string) => importTradeCsv(csvText, accountId as string), {
    onSuccess: async () => {
      await refreshPrototypeQueries();
    },
  });

  const handleCsvUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    setSelectedFileName(file.name);
    const csvText = await file.text();
    importMutation.mutate(csvText);
  };

  return (
    <div className="space-y-6 text-black dark:text-white">
      <section className="rounded-[26px] border border-black/10 bg-white p-6 dark:border-white/10 dark:bg-[#060606]">
        <h2 className="text-[1.9rem] font-semibold tracking-[-0.05em]">Data</h2>
      </section>

      <section className="grid gap-6 xl:grid-cols-3">
        <Card title="Seed Workspace">
          <p className="text-sm text-black/70 dark:text-white/70">
            Replace the current workspace with 300 seeded trades across stocks, forex, crypto, and futures, plus sessions and missed opportunities.
          </p>
          <button type="button" onClick={() => seedMutation.mutate()} className="mt-6 inline-flex rounded-full bg-black px-5 py-3 text-sm font-semibold text-white transition hover:border-[#ff5900] hover:text-white hover:shadow-[0_10px_24px_-18px_rgba(255,89,0,0.28),0_0_0_1px_rgba(255,89,0,0.26)] dark:bg-white dark:text-black dark:hover:text-black">
            {seedMutation.isLoading ? 'Seeding…' : 'Seed 300 Trades'}
          </button>
          {seedMutation.data ? <p className="mt-4 text-sm text-emerald-700 dark:text-emerald-300">{seedMutation.data.detail}</p> : null}
          {seedMutation.error instanceof Error ? <p className="mt-4 text-sm text-rose-700 dark:text-rose-300">{seedMutation.error.message}</p> : null}
        </Card>

        <Card title="Import CSV">
          <p className="text-sm text-black/70 dark:text-white/70">
            Upload a CSV with trade rows and write them into the journal.
          </p>
          <label className="mt-6 inline-flex cursor-pointer items-center rounded-full border border-black/10 bg-white px-5 py-3 text-sm font-semibold text-black transition hover:border-[#ff5900] hover:text-[#ff5900] dark:border-white/10 dark:bg-[#0b0b0b] dark:text-white dark:hover:border-[#ff5900] dark:hover:text-[#ff5900]">
            Choose CSV File
            <input type="file" accept=".csv,text/csv" className="hidden" onChange={handleCsvUpload} />
          </label>
          {selectedFileName ? <p className="mt-4 text-sm text-black/70 dark:text-white/70">{selectedFileName}</p> : null}
          {importMutation.isLoading ? <p className="mt-4 text-sm text-black/70 dark:text-white/70">Importing…</p> : null}
          {importMutation.data ? (
            <div className="mt-4 text-sm">
              <p className="text-emerald-700 dark:text-emerald-300">Imported {importMutation.data.imported_count} trade(s).</p>
              {importMutation.data.errors.length > 0 ? (
                <ul className="mt-2 space-y-1 text-amber-700 dark:text-amber-300">
                  {importMutation.data.errors.slice(0, 5).map((item) => (
                    <li key={`${item.row}-${item.detail}`}>Row {item.row}: {item.detail}</li>
                  ))}
                </ul>
              ) : null}
            </div>
          ) : null}
          {importMutation.error instanceof Error ? <p className="mt-4 text-sm text-rose-700 dark:text-rose-300">{importMutation.error.message}</p> : null}
        </Card>

        <Card title="Rebuild Calendar">
          <p className="text-sm text-black/70 dark:text-white/70">
            Refresh daily summaries after seed or CSV import.
          </p>
          <button type="button" onClick={() => rebuildMutation.mutate()} className="mt-6 inline-flex rounded-full border border-black/10 bg-white px-5 py-3 text-sm font-semibold text-black transition hover:border-[#ff5900] hover:text-[#ff5900] dark:border-white/10 dark:bg-[#0b0b0b] dark:text-white dark:hover:border-[#ff5900] dark:hover:text-[#ff5900]">
            {rebuildMutation.isLoading ? 'Rebuilding…' : 'Rebuild'}
          </button>
          {rebuildMutation.isSuccess ? <p className="mt-4 text-sm text-emerald-700 dark:text-emerald-300">Calendar rebuilt.</p> : null}
          {rebuildMutation.error instanceof Error ? <p className="mt-4 text-sm text-rose-700 dark:text-rose-300">{rebuildMutation.error.message}</p> : null}
        </Card>
      </section>
    </div>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-[26px] border border-black/10 bg-white p-6 dark:border-white/10 dark:bg-[#060606]">
      <h3 className="text-xl font-semibold text-black dark:text-white">{title}</h3>
      <div className="mt-4">{children}</div>
    </section>
  );
}
