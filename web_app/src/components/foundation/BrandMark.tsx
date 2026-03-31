export function BrandMark({ compact = false }: { compact?: boolean }) {
  return (
    <div className={`inline-flex items-center ${compact ? 'justify-center' : 'gap-4'}`}>
      <div className="relative flex h-12 w-12 items-center justify-center overflow-hidden rounded-2xl bg-[linear-gradient(145deg,#07111d_0%,#123b50_42%,#0fa6b0_100%)] shadow-[0_16px_34px_rgba(15,23,42,0.16)]">
        <div className="absolute inset-[1px] rounded-[15px] border border-white/15 bg-[radial-gradient(circle_at_28%_24%,rgba(255,255,255,0.28),transparent_34%),rgba(255,255,255,0.04)]" />
        <span className="relative text-sm font-bold tracking-[0.28em] text-white">MP</span>
      </div>
      {!compact ? (
      <div>
        <p className="text-[1.02rem] font-semibold tracking-[-0.03em] text-[var(--color-ink)]">My Platform</p>
        <p className="mt-0.5 text-[0.66rem] uppercase tracking-[0.32em] text-[var(--color-muted)]">Trading intelligence, not clutter</p>
      </div>
      ) : null}
    </div>
  );
}
