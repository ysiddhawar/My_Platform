import type { BehaviorFinding } from '@/types/prototype';

const severityStyles: Record<string, string> = {
  info: 'bg-sky-500/10 text-sky-700 dark:bg-sky-400/10 dark:text-sky-300',
  low: 'bg-amber-500/10 text-amber-700 dark:bg-amber-400/10 dark:text-amber-300',
  medium: 'bg-orange-500/10 text-orange-700 dark:bg-orange-400/10 dark:text-orange-300',
  high: 'bg-rose-500/10 text-rose-700 dark:bg-rose-400/10 dark:text-rose-300',
};

type InsightListProps = {
  title: string;
  items: BehaviorFinding[];
  emptyMessage: string;
};

export function InsightList({ title, items, emptyMessage }: InsightListProps) {
  return (
    <section className="rounded-[30px] border border-black/5 bg-white/82 p-6 shadow-[0_20px_55px_rgba(15,23,42,0.06)] dark:border-white/8 dark:bg-white/[0.03] dark:shadow-[0_26px_80px_rgba(0,0,0,0.3)]">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-[0.72rem] font-semibold uppercase tracking-[0.22em] text-slate-500 dark:text-slate-500">AI Layer</p>
          <h2 className="mt-2 text-xl font-semibold tracking-[-0.04em] text-slate-950 dark:text-white">{title}</h2>
        </div>
        <div className="rounded-full bg-slate-950 px-3 py-1 text-xs font-semibold text-white dark:bg-white dark:text-slate-950">
          {items.length} items
        </div>
      </div>

      <div className="mt-6 space-y-3">
        {items.length === 0 ? (
          <p className="rounded-[22px] border border-dashed border-black/10 px-4 py-5 text-sm text-slate-500 dark:border-white/10 dark:text-slate-400">
            {emptyMessage}
          </p>
        ) : (
          items.map((item, index) => (
            <article key={`${item.title}-${index}`} className="rounded-[24px] border border-black/5 bg-slate-50/85 p-4 dark:border-white/8 dark:bg-black/30">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h3 className="text-base font-semibold text-slate-950 dark:text-white">{item.title}</h3>
                  <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">{item.description}</p>
                </div>
                <span className={`shrink-0 rounded-full px-3 py-1 text-xs font-semibold capitalize ${severityStyles[item.severity] || severityStyles.info}`}>
                  {item.severity}
                </span>
              </div>
            </article>
          ))
        )}
      </div>
    </section>
  );
}
