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
  tooltipLabelFormatter?: (label: string) => string;
  barColor?: string;
  xAxisInterval?: number;
  tickAngle?: number;
  tickHeight?: number;
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
  tooltipLabelFormatter,
  barColor = '#0f766e',
  xAxisInterval,
  tickAngle,
  tickHeight,
}: MetricsBarChartProps) {
  const shouldTiltTicks = tickAngle != null || data.length > 12;
  const resolvedTickAngle = tickAngle ?? (shouldTiltTicks ? -18 : 0);
  const resolvedTickHeight = tickHeight ?? (shouldTiltTicks ? 72 : 50);
  
  if (className) {
    // Bypass ChartFrame for custom heights
    return (
      <div className={className}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(100,116,139,0.14)" vertical={false} />
            <XAxis
              dataKey="metric"
              stroke="#64748b"
              tickLine={false}
              axisLine={false}
              interval={xAxisInterval ?? (data.length > 12 ? 1 : 0)}
              angle={resolvedTickAngle}
              textAnchor={shouldTiltTicks ? 'end' : 'middle'}
              height={resolvedTickHeight}
            />
            <YAxis stroke="#64748b" tickLine={false} axisLine={false} width={88} tickFormatter={(value) => valueFormatter(Number(value))} />
            <Tooltip
              formatter={(value: number) => [valueFormatter(Number(value)), 'Value']}
              labelFormatter={(label: string) => (tooltipLabelFormatter ? tooltipLabelFormatter(label) : labelFormatter ? labelFormatter(label) : label)}
              contentStyle={{ borderRadius: 16, border: '1px solid rgba(15,23,42,0.08)' }}
            />
            <Bar dataKey="value" fill={barColor} radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  }
  
  // Use ChartFrame for default heights
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
            interval={xAxisInterval ?? (data.length > 12 ? 1 : 0)}
            angle={resolvedTickAngle}
            textAnchor={shouldTiltTicks ? 'end' : 'middle'}
            height={resolvedTickHeight}
          />
          <YAxis stroke="#64748b" tickLine={false} axisLine={false} width={88} tickFormatter={(value) => valueFormatter(Number(value))} />
          <Tooltip
            formatter={(value: number) => [valueFormatter(Number(value)), 'Value']}
            labelFormatter={(label: string) => (tooltipLabelFormatter ? tooltipLabelFormatter(label) : labelFormatter ? labelFormatter(label) : label)}
            contentStyle={{ borderRadius: 16, border: '1px solid rgba(15,23,42,0.08)' }}
          />
          <Bar dataKey="value" fill={barColor} radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </ChartFrame>
  );
}
