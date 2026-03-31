import { useQuery } from 'react-query';

import { endpoints } from '@/api/endpoints';
import { Panel } from '@/components/ui/Panel';

export function BehavioralDisciplinePanel() {
  const { data } = useQuery('behavioral-snapshot', async () => {
    const response = await endpoints.getBehavioralSnapshot();
    return response.data || { signals: {} };
  });

  const signals = data?.signals || {};

  return (
    <Panel title="Behavioral Discipline Signals" subtitle="AI-ready raw behavioral telemetry from pre and post-trade captures">
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <SignalCard title="Early Exit Rate" value={signals.early_exit_rate} />
        <SignalCard title="Checklist Compliance" value={signals.checklist_compliance_rate} />
        <SignalCard title="Setup Drift Rate" value={signals.setup_drift_rate} />
        <SignalCard title="Violation Frequency" value={signals.violation_frequency} />
      </div>
    </Panel>
  );
}

function SignalCard({ title, value }: { title: string; value?: number }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
      <p className="text-xs uppercase tracking-[0.16em] text-slate-500">{title}</p>
      <p className="mt-3 font-display text-2xl font-semibold text-white">
        {typeof value === 'number' ? value.toFixed(2) : '--'}
      </p>
    </div>
  );
}
