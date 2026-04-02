import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import { ChartFrame } from './ChartFrame';
import { formatCompactNumber } from '@/utils/format';

type TimeSeriesPoint = {
  label: string;
  [key: string]: string | number;
};

type SeriesConfig = {
  key: string;
  color: string;
  name?: string;
};

type GenericTimeSeriesChartProps = {
  data: TimeSeriesPoint[];
  series: SeriesConfig[];
  className?: string;
  valueFormatter?: (value: number) => string;
  xTickFormatter?: (value: string) => string;
  tooltipLabelFormatter?: (label: string) => string;
};

function defaultValueFormatter(value: number) {
  if (!Number.isFinite(value)) return '0';
  const abs = Math.abs(value);
  if (abs >= 1000) return formatCompactNumber(value);
  if (abs <= 1 && abs > 0 && String(value).includes('.')) return Number(value).toFixed(2);
  return abs >= 100 ? formatCompactNumber(value) : Number(value).toFixed(abs >= 10 ? 1 : 2).replace(/\.00$/, '');
}

export function GenericTimeSeriesChart({
  data,
  series,
  className,
  valueFormatter = defaultValueFormatter,
  xTickFormatter,
  tooltipLabelFormatter,
}: GenericTimeSeriesChartProps) {
  if (className?.includes('h-[') || className?.includes('h-[')) {
    // Bypass ChartFrame for custom heights
    return (
      <div className={className}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(100,116,139,0.14)" vertical={false} />
            <XAxis dataKey="label" stroke="#64748b" tickLine={false} axisLine={false} minTickGap={24} tickFormatter={xTickFormatter} />
            <YAxis stroke="#64748b" tickLine={false} axisLine={false} width={64} tickFormatter={(value) => valueFormatter(Number(value))} />
            <Tooltip
              formatter={(value: number, name: string) => [valueFormatter(Number(value)), name]}
              labelFormatter={(label: string) => (tooltipLabelFormatter ? tooltipLabelFormatter(label) : label)}
              contentStyle={{ borderRadius: 16, border: '1px solid rgba(15,23,42,0.08)' }}
            />
            {series.map((item) => (
              <Line
                key={item.key}
                type="monotone"
                dataKey={item.key}
                stroke={item.color}
                strokeWidth={2}
                dot={false}
                name={item.name || item.key}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    );
  }

  // Use ChartFrame for default heights
  return (
    <ChartFrame className={className}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(100,116,139,0.14)" vertical={false} />
          <XAxis dataKey="label" stroke="#64748b" tickLine={false} axisLine={false} minTickGap={24} tickFormatter={xTickFormatter} />
          <YAxis stroke="#64748b" tickLine={false} axisLine={false} width={64} tickFormatter={(value) => valueFormatter(Number(value))} />
          <Tooltip
            formatter={(value: number, name: string) => [valueFormatter(Number(value)), name]}
            labelFormatter={(label: string) => (tooltipLabelFormatter ? tooltipLabelFormatter(label) : label)}
            contentStyle={{ borderRadius: 16, border: '1px solid rgba(15,23,42,0.08)' }}
          />
          {series.map((item) => (
            <Line
              key={item.key}
              type="monotone"
              dataKey={item.key}
              stroke={item.color}
              strokeWidth={2.5}
              dot={false}
              name={item.name || item.key}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </ChartFrame>
  );
}
