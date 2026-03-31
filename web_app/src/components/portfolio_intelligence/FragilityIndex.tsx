export function FragilityIndex({ value }: { value: string }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-4">
      <p className="text-xs uppercase tracking-[0.16em] text-slate-500">Fragility Index</p>
      <p className="mt-2 font-display text-2xl font-semibold text-white">{value}</p>
      <p className="mt-2 text-sm text-slate-400">Lower is better. Current portfolio remains below alert threshold.</p>
    </div>
  );
}
