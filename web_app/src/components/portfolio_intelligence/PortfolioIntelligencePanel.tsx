import { Panel } from '@/components/ui/Panel';

import { CorrelationHeatmap } from './CorrelationHeatmap';
import { DiversificationRatio } from './DiversificationRatio';
import { FragilityIndex } from './FragilityIndex';
import { RiskContributionChart } from './RiskContributionChart';

export function PortfolioIntelligencePanel() {
  return (
    <Panel title="Portfolio Intelligence Panel" subtitle="Cross-asset concentration and stability intelligence" className="h-full">
      <div className="grid gap-4 xl:grid-cols-2">
        <CorrelationHeatmap
          data={[
            { x: 'Alpha', y: 'Alpha', z: 1.0 },
            { x: 'Alpha', y: 'Beta', z: 0.28 },
            { x: 'Beta', y: 'Alpha', z: 0.28 },
            { x: 'Beta', y: 'Beta', z: 1.0 }
          ]}
        />
        <RiskContributionChart
          data={[
            { asset: 'Alpha', value: 34 },
            { asset: 'Beta', value: 28 },
            { asset: 'Gamma', value: 22 },
            { asset: 'Macro', value: 16 }
          ]}
        />
        <DiversificationRatio value="1.84" />
        <FragilityIndex value="0.26" />
      </div>
    </Panel>
  );
}
