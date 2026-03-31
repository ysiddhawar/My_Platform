import { Panel } from '@/components/ui/Panel';

export function AIDashboard() {
  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Panel title="AI Diagnosis" subtitle="Model-generated findings">
        <ul className="space-y-2 text-sm text-slate-700">
          <li>Strength: Stable risk-adjusted performance</li>
          <li>Warning: Elevated drawdown clustering in regime transitions</li>
          <li>Action: Reduce risk allocation by 10% in high-vol regime</li>
        </ul>
      </Panel>
      <Panel title="AI Follow-ups" subtitle="Recommended next actions" action="Execute">
        <ul className="space-y-2 text-sm text-slate-700">
          <li>Run stress profile on updated strategy set</li>
          <li>Apply tighter spread guard for next 3 sessions</li>
          <li>Schedule discipline review after next loss cluster</li>
        </ul>
      </Panel>
    </div>
  );
}
