export function DiversificationRatio({ value }: { value: string }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-4">
      <p className="text-xs uppercase tracking-[0.16em] text-slate-500">Diversification Ratio</p>
      <p className="mt-2 font-display text-2xl font-semibold text-white">{value}</p>
      <p className="mt-2 text-sm text-slate-400">Cross-strategy spread remains healthy relative to concentration.</p>
    </div>
  );
}
