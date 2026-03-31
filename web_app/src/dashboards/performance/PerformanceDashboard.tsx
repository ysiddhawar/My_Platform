import { MetricsBarChart } from '@/components/charts/MetricsBarChart';
import { Panel } from '@/components/ui/Panel';
import { StatPill } from '@/components/ui/StatPill';
import { performanceMetrics } from '@/utils/mockData';
import { formatPercent } from '@/utils/format';

export function PerformanceDashboard() {
  return (
    <div className="grid gap-6 lg:grid-cols-3">
      <Panel title="Performance Snapshot" subtitle="Core trading KPIs" action="Refresh">
        <div className="grid grid-cols-3 gap-2">
          <StatPill label="Sharpe" value="1.46" tone="positive" />
          <StatPill label="Sortino" value="2.09" tone="positive" />
          <StatPill label="Max DD" value={formatPercent(0.12)} tone="warning" />
        </div>
      </Panel>
      <div className="lg:col-span-2">
        <Panel title="Metric Distribution" subtitle="Normalized portfolio metrics">
          <MetricsBarChart data={performanceMetrics} />
        </Panel>
      </div>
    </div>
  );
}
