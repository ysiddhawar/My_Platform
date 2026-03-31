import { useQuery } from 'react-query';

import { endpoints } from '@/api/endpoints';
import { EquityCurveChart } from '@/components/charts/EquityCurveChart';
import { Panel } from '@/components/ui/Panel';

import { DrawdownCurveChart } from './DrawdownCurveChart';
import { RollingSharpeChart } from './RollingSharpeChart';

const fallbackEquity = [
  { t: 'Mon', equity: 100000 },
  { t: 'Tue', equity: 101400 },
  { t: 'Wed', equity: 100850 },
  { t: 'Thu', equity: 102200 },
  { t: 'Fri', equity: 103050 }
];

const fallbackSharpe = [
  { t: 'Mon', value: 1.1 },
  { t: 'Tue', value: 1.25 },
  { t: 'Wed', value: 1.18 },
  { t: 'Thu', value: 1.38 },
  { t: 'Fri', value: 1.46 }
];

const fallbackDrawdown = [
  { t: 'Mon', value: -0.01 },
  { t: 'Tue', value: -0.02 },
  { t: 'Wed', value: -0.015 },
  { t: 'Thu', value: -0.018 },
  { t: 'Fri', value: -0.012 }
];

export function PerformancePanel() {
  useQuery(
    ['performance-panel'],
    () =>
      endpoints.runMetrics({
        category: 'performance',
        data: {
          returns: [0.012, -0.004, 0.008, 0.002, -0.003, 0.011, 0.006, -0.002, 0.007, 0.005]
        },
        phase: 'research'
      }),
    { staleTime: 60000 }
  );

  return (
    <Panel title="Performance Panel" subtitle="Equity path, rolling quality, and drawdown structure" className="h-full">
      <div className="grid gap-4 xl:grid-cols-2">
        <div className="xl:col-span-2">
          <EquityCurveChart data={fallbackEquity} />
        </div>
        <RollingSharpeChart data={fallbackSharpe} />
        <DrawdownCurveChart data={fallbackDrawdown} />
      </div>
    </Panel>
  );
}
