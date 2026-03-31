type StatPillProps = {
  label: string;
  value: string;
  tone?: 'normal' | 'positive' | 'warning' | 'danger';
};

const toneStyles: Record<NonNullable<StatPillProps['tone']>, string> = {
  normal: 'border border-slate-700 bg-slate-900/80 text-slate-100',
  positive: 'border border-emerald-800 bg-emerald-950/80 text-emerald-200',
  warning: 'border border-amber-800 bg-amber-950/80 text-amber-200',
  danger: 'border border-rose-800 bg-rose-950/80 text-rose-200'
};

export function StatPill({ label, value, tone = 'normal' }: StatPillProps) {
  return (
    <div className={`rounded-xl px-3 py-2 ${toneStyles[tone]}`}>
      <p className="text-[10px] uppercase tracking-[0.18em] opacity-75">{label}</p>
      <p className="font-display text-lg font-semibold">{value}</p>
    </div>
  );
}
