import { Panel } from '@/components/ui/Panel';

export function RiskDashboard() {
  return (
    <div className="grid gap-6 lg:grid-cols-3">
      <Panel title="Risk Limits" subtitle="Guardrail status">
        <p className="text-sm text-slate-700">Daily DD: 1.2% / 3.0%</p>
        <p className="text-sm text-slate-700">Weekly DD: 2.1% / 8.0%</p>
        <p className="text-sm text-slate-700">Open positions: 4 / 10</p>
      </Panel>
      <Panel title="Volatility Regime" subtitle="Current market regime">
        <p className="font-display text-2xl font-semibold text-accent">Moderate</p>
        <p className="text-sm text-slate-600">Adaptive volatility signals remain contained.</p>
      </Panel>
      <Panel title="Stress Readiness" subtitle="Shock scenario posture">
        <p className="text-sm text-slate-700">Worst-case DD estimate: -14.8%</p>
        <p className="text-sm text-slate-700">Liquidity pressure score: 0.34</p>
      </Panel>
    </div>
  );
}
