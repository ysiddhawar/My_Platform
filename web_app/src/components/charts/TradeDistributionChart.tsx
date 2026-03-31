import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts';

import { ChartFrame } from './ChartFrame';

type Slice = {
  name: string;
  value: number;
};

type TradeDistributionChartProps = {
  data: Slice[];
};

const colors = ['#0f766e', '#b45309', '#b91c1c'];

export function TradeDistributionChart({ data }: TradeDistributionChartProps) {
  return (
    <ChartFrame>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie data={data} dataKey="value" nameKey="name" outerRadius={90}>
            {data.map((entry, index) => (
              <Cell key={`${entry.name}-${index}`} fill={colors[index % colors.length]} />
            ))}
          </Pie>
          <Tooltip />
        </PieChart>
      </ResponsiveContainer>
    </ChartFrame>
  );
}
