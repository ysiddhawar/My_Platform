import { PropsWithChildren } from 'react';

type PanelProps = PropsWithChildren<{
  title: string;
  subtitle?: string;
  action?: string;
  className?: string;
}>;

export function Panel({ title, subtitle, action, className, children }: PanelProps) {
  return (
    <section
      className={`rounded-2xl border border-slate-800/60 bg-panel p-5 shadow-panel ring-1 ring-white/5 ${className || ''}`.trim()}
    >
      <header className="mb-4 flex items-start justify-between gap-4">
        <div>
          <h3 className="font-display text-lg font-semibold text-ink">{title}</h3>
          {subtitle ? <p className="text-sm text-slate-400">{subtitle}</p> : null}
        </div>
        {action ? (
          <button className="rounded-full border border-accent/60 bg-accent/10 px-3 py-1 text-xs font-medium text-accent transition hover:bg-accent hover:text-white">
            {action}
          </button>
        ) : null}
      </header>
      {children}
    </section>
  );
}
