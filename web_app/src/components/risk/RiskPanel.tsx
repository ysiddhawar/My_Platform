import { useQuery } from 'react-query';

import { endpoints } from '@/api/endpoints';
import { Panel } from '@/components/ui/Panel';

import { CVaRChart } from './CVaRChart';
import { RegimeDetectionChart } from './RegimeDetectionChart';
import { VaRChart } from './VaRChart';
import { VolatilityChart } from './VolatilityChart';

const baseMetrics = {
  risk: { max_drawdown: 0.12, volatility: 0.18, rolling_volatility: 0.2 },
  regimes: { volatility_regime: 0.4 },
  survival: { survival_score: 0.88 },
  robustness: { stability_score: 0.81 },
  portfolio: { portfolio_fragility_index: 0.26 }
};

export function RiskPanel() {
  useQuery(
    ['risk-panel'],
    () =>
      endpoints.runRiskModeling({
        metrics: baseMetrics,
        returns: [0.004, -0.002, 0.006, -0.003, 0.003, 0.005, -0.004, 0.002],
        initial_equity: 100000
      }),
    { staleTime: 60000 }
  );

  return (
    <Panel title="Risk Panel" subtitle="Volatility, tails, and regime identification" className="h-full">
      <div className="grid gap-4 xl:grid-cols-2">
        <VolatilityChart
          data={[
            { t: '1', value: 0.12 },
            { t: '2', value: 0.18 },
            { t: '3', value: 0.15 },
            { t: '4', value: 0.22 }
          ]}
        />
        <VaRChart
          data={[
            { t: '95%', value: 1.8 },
            { t: '97%', value: 2.4 },
            { t: '99%', value: 3.2 }
          ]}
        />
        <CVaRChart
          data={[
            { t: '95%', value: 2.2 },
            { t: '97%', value: 2.9 },
            { t: '99%', value: 3.8 }
          ]}
        />
        <RegimeDetectionChart
          data={[
            { t: 1, value: 0.2, regime: 'low' },
            { t: 2, value: 0.5, regime: 'medium' },
            { t: 3, value: 0.8, regime: 'high' },
            { t: 4, value: 0.45, regime: 'medium' }
          ]}
        />
      </div>
    </Panel>
  );
}
