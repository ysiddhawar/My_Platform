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
  tooltipFormatter?: (value: number, name: string, total: number) => [string, string];
};

const defaultColors = ['#0f766e', '#1d4ed8', '#b45309', '#b91c1c', '#7c3aed', '#334155'];

export function PieMetricChart({
  data,
  colors = defaultColors,
  className,
  valueFormatter = (value) => formatCompactNumber(value),
  tooltipFormatter,
}: PieMetricChartProps) {
  const total = data.reduce((sum, item) => sum + item.value, 0);
  const colorsToUse = colors || defaultColors;
  
  if (className?.includes('h-[') || className?.includes('h-[')) {
    // Bypass ChartFrame for custom heights
    return (
      <div className={className}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={data} dataKey="value" nameKey="name" outerRadius={88} innerRadius={36}>
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={colorsToUse[index % colorsToUse.length]} />
              ))}
            </Pie>
            <Tooltip
              formatter={(value: number, name: string) => [
                tooltipFormatter ? tooltipFormatter(value, name, total) : valueFormatter(value),
                name,
              ]}
              contentStyle={{ borderRadius: 16, border: '1px solid rgba(15,23,42,0.08)' }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
    );
  }
  
  // Use ChartFrame for default heights
  return (
    <ChartFrame className={className}>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie data={data} dataKey="value" nameKey="name" outerRadius={88} innerRadius={36}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={colorsToUse[index % colorsToUse.length]} />
            ))}
          </Pie>
          <Tooltip
            formatter={(value: number, name: string) => [
              tooltipFormatter ? tooltipFormatter(value, name, total) : valueFormatter(value),
              name,
            ]}
            contentStyle={{ borderRadius: 16, border: '1px solid rgba(15,23,42,0.08)' }}
          />
        </PieChart>
      </ResponsiveContainer>
    </ChartFrame>
  );
}
