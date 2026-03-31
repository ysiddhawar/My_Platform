const rows = [
  { label: 'Checklist completion', value: '7 / 9', tone: 'bg-amber-100 text-amber-700' },
  { label: 'Exit behavior', value: 'Closed early', tone: 'bg-rose-100 text-rose-700' },
  { label: 'Probability confidence', value: '60%', tone: 'bg-sky-100 text-sky-700' },
  { label: 'AI insight', value: 'Target abandonment', tone: 'bg-emerald-100 text-emerald-700' }
];

export function SignalCanvas() {
  return (
    <div className="relative h-full overflow-hidden rounded-[1.7rem] border border-slate-200 bg-[linear-gradient(180deg,#fbfbfd_0%,#eef6f8_100%)] p-6">
      <div className="absolute inset-x-10 top-6 h-32 rounded-full bg-[radial-gradient(circle,rgba(20,184,166,0.16),transparent_60%)] blur-2xl" />
      <div className="relative space-y-4">
        <div className="rounded-[1.3rem] border border-slate-200 bg-white p-5 shadow-[0_16px_40px_rgba(15,23,42,0.06)]">
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">Trade review graph</p>
          <div className="mt-5 grid grid-cols-[1fr_auto] gap-4">
            <div className="h-40 rounded-2xl bg-[linear-gradient(180deg,rgba(15,118,110,0.12),rgba(15,118,110,0.02))] p-4">
              <div className="relative h-full overflow-hidden rounded-xl border border-teal-100 bg-white/70">
                <div className="absolute inset-x-6 top-8 h-[2px] bg-sky-400" />
                <div className="absolute inset-x-6 bottom-10 h-[2px] bg-rose-400" />
                <div className="absolute inset-x-6 top-1/2 h-[2px] bg-emerald-400" />
                <div className="absolute left-[62%] top-[38%] h-14 w-14 rounded-full border border-teal-200 bg-teal-50/80" />
              </div>
            </div>
            <div className="space-y-2">
              <div className="rounded-2xl border border-slate-200 bg-slate-950 px-4 py-3 text-xs uppercase tracking-[0.2em] text-white">Pre-trade</div>
              <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-xs uppercase tracking-[0.2em] text-slate-500">Post-trade</div>
            </div>
          </div>
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          {rows.map((row) => (
            <div key={row.label} className="rounded-[1.2rem] border border-slate-200 bg-white px-4 py-4 shadow-[0_12px_28px_rgba(15,23,42,0.04)]">
              <p className="text-xs uppercase tracking-[0.22em] text-slate-400">{row.label}</p>
              <span className={`mt-3 inline-flex rounded-full px-3 py-1 text-sm font-semibold ${row.tone}`}>{row.value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
