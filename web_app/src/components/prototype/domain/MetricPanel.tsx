import type { ReactNode } from 'react';

type MetricPanelProps = {
  eyebrow: string;
  title: string;
  body: string;
  action?: ReactNode;
  children?: ReactNode;
};

export function MetricPanel({ eyebrow, title, body, action, children }: MetricPanelProps) {
  return (
    <section className="rounded-[30px] border border-black/8 bg-white p-6 shadow-[0_20px_55px_rgba(15,23,42,0.06)] dark:border-white/10 dark:bg-[#050505] dark:shadow-[0_26px_80px_rgba(0,0,0,0.3)]">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-[0.72rem] font-semibold uppercase tracking-[0.22em] text-[var(--color-muted)]">{eyebrow}</p>
          <h2 className="mt-2 text-[1.45rem] font-semibold tracking-[-0.04em] text-black dark:text-white">{title}</h2>
          <p className="mt-3 max-w-3xl text-sm leading-7 text-[var(--color-muted)]">{body}</p>
        </div>
        {action ? <div className="shrink-0">{action}</div> : null}
      </div>
      {children ? <div className="mt-6">{children}</div> : null}
    </section>
  );
}
