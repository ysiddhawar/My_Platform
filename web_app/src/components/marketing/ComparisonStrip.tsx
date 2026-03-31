const items = [
  'Position sizing and discipline capture in one flow',
  'Pre-trade and post-trade evidence instead of hindsight journaling',
  'Screenshot markers linked to AI diagnosis',
  'Lightweight layout that explains value without clutter'
];

export function ComparisonStrip() {
  return (
    <section className="rounded-[2rem] border border-slate-200 bg-slate-950 px-8 py-8 text-white shadow-[0_28px_80px_rgba(15,23,42,0.16)]">
      <div className="grid gap-6 lg:grid-cols-[0.8fr_1.2fr] lg:items-center">
        <div>
          <p className="text-[0.7rem] font-semibold uppercase tracking-[0.28em] text-teal-300">Competitive position</p>
          <h3 className="mt-4 font-display text-3xl font-semibold tracking-tight">Built for traders who want behavior explained, not just trades logged.</h3>
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          {items.map((item) => (
            <div key={item} className="rounded-[1.2rem] border border-white/10 bg-white/5 px-4 py-4 text-sm leading-7 text-slate-200">
              {item}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
