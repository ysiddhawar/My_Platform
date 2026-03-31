import { Panel } from '@/components/ui/Panel';

export function PortfolioDashboard() {
  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Panel title="Allocation" subtitle="Current portfolio weights">
        <ul className="space-y-2 text-sm text-slate-700">
          <li>Tech Momentum: 34%</li>
          <li>Mean Reversion: 28%</li>
          <li>Event Driven: 22%</li>
          <li>Macro Overlay: 16%</li>
        </ul>
      </Panel>
      <Panel title="Diversification" subtitle="Risk concentration indicators">
        <ul className="space-y-2 text-sm text-slate-700">
          <li>Effective number of bets: 7.4</li>
          <li>Avg pairwise correlation: 0.31</li>
          <li>Systemic fragility index: 0.26</li>
        </ul>
      </Panel>
    </div>
  );
}
