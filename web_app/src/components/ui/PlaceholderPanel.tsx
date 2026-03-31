import { PropsWithChildren } from 'react';

import { Panel } from './Panel';

type PlaceholderPanelProps = PropsWithChildren<{
  title: string;
  subtitle?: string;
}>;

export function PlaceholderPanel({ title, subtitle, children }: PlaceholderPanelProps) {
  return (
    <Panel title={title} subtitle={subtitle}>
      <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50/70 p-3">{children}</div>
    </Panel>
  );
}
