import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import { ChartFrame } from './ChartFrame';
import { formatCompactNumber } from '@/utils/format';

type MetricPoint = {
  metric: string;
  value: number;
};

type MetricsBarChartProps = {
  data: MetricPoint[];
  className?: string;
  valueFormatter?: (value: number) => string;
  labelFormatter?: (label: string) => string;
  barColor?: string;
  xAxisInterval?: number;
};

function defaultBarValueFormatter(value: number) {
  if (!Number.isFinite(value)) return '0';
  if (Math.abs(value) >= 1000) return formatCompactNumber(value);
  return Number(value).toFixed(Math.abs(value) >= 10 ? 1 : 2).replace(/\.00$/, '');
}

export function MetricsBarChart({
  data,
  className,
  valueFormatter = defaultBarValueFormatter,
  labelFormatter,
  barColor = '#0f766e',
  xAxisInterval,
}: MetricsBarChartProps) {
  const shouldTiltTicks = data.length > 12;
  return (
    <ChartFrame className={className}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(100,116,139,0.14)" vertical={false} />
          <XAxis
            dataKey="metric"
            stroke="#64748b"
            tickLine={false}
            axisLine={false}
            tickFormatter={labelFormatter}
            interval={xAxisInterval ?? (data.length > 12 ? 1 : 0)}
            angle={shouldTiltTicks ? -18 : 0}
            textAnchor={shouldTiltTicks ? 'end' : 'middle'}
            height={shouldTiltTicks ? 52 : 34}
          />
          <YAxis stroke="#64748b" tickLine={false} axisLine={false} width={88} tickFormatter={(value) => valueFormatter(Number(value))} />
          <Tooltip
            formatter={(value: number) => [valueFormatter(Number(value)), 'Value']}
            labelFormatter={(label: string) => (labelFormatter ? labelFormatter(label) : label)}
            contentStyle={{ borderRadius: 16, border: '1px solid rgba(15,23,42,0.08)' }}
          />
          <Bar dataKey="value" fill={barColor} radius={[6, 6, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </ChartFrame>
  );
}
