import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts';

import { ChartFrame } from './ChartFrame';
import { formatCompactNumber } from '@/utils/format';

type Slice = {
  name: string;
  value: number;
};

type PieMetricChartProps = {
  data: Slice[];
  colors?: string[];
  className?: string;
  valueFormatter?: (value: number) => string;
};

const defaultColors = ['#0f766e', '#1d4ed8', '#b45309', '#b91c1c', '#7c3aed', '#334155'];

export function PieMetricChart({
  data,
  colors = defaultColors,
  className,
  valueFormatter = (value) => formatCompactNumber(value),
}: PieMetricChartProps) {
  const total = data.reduce((sum, item) => sum + item.value, 0);
  return (
    <ChartFrame className={className}>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie data={data} dataKey="value" nameKey="name" outerRadius={88} innerRadius={36}>
            {data.map((entry, index) => (
              <Cell key={`${entry.name}-${index}`} fill={colors[index % colors.length]} />
            ))}
          </Pie>
          <Tooltip
            formatter={(value: number) => {
              const share = total > 0 ? `${((Number(value) / total) * 100).toFixed(1)}%` : '0%';
              return [`${valueFormatter(Number(value))} · ${share}`, 'Value'];
            }}
            contentStyle={{ borderRadius: 16, border: '1px solid rgba(15,23,42,0.08)' }}
          />
        </PieChart>
      </ResponsiveContainer>
    </ChartFrame>
  );
}
