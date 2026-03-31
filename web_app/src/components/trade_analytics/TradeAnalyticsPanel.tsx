import { TradeDistributionChart } from '@/components/charts/TradeDistributionChart';
import { Panel } from '@/components/ui/Panel';

import { HoldingTimeChart } from './HoldingTimeChart';
import { WinLossChart } from './WinLossChart';

export function TradeAnalyticsPanel() {
  return (
    <Panel title="Trade Analytics Panel" subtitle="Distribution, outcomes, and holding structure" className="h-full">
      <div className="grid gap-4 xl:grid-cols-2">
        <TradeDistributionChart
          data={[
            { name: 'Wins', value: 62 },
            { name: 'Losses', value: 38 }
          ]}
        />
        <WinLossChart
          data={[
            { name: 'Gross Wins', value: 84 },
            { name: 'Gross Losses', value: 51 }
          ]}
        />
        <div className="xl:col-span-2">
          <HoldingTimeChart
            data={[
              { bucket: '<1h', value: 9 },
              { bucket: '1-4h', value: 22 },
              { bucket: '4-24h', value: 16 },
              { bucket: '>1d', value: 7 }
            ]}
          />
        </div>
      </div>
    </Panel>
  );
}
