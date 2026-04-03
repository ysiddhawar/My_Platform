import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import { ChartFrame } from './ChartFrame';
import { formatCompactNumber, formatCurrency } from '@/utils/format';

type Point = {
  t: string;
  equity: number;
};

type EquityCurveChartProps = {
  data: Point[];
  className?: string;
};

export function EquityCurveChart({ data, className }: EquityCurveChartProps) {
  const formatAxisDate = (value: string) => {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
    }).format(date);
  };

  const formatTooltipDate = (value: string) => {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    }).format(date);
  };

  if (className) {
    // Bypass ChartFrame for custom heights
    return (
      <div className={className}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(100,116,139,0.14)" vertical={false} />
            <XAxis dataKey="t" stroke="#64748b" tickLine={false} axisLine={false} minTickGap={24} tickFormatter={formatAxisDate} height={42} />
            <YAxis
              stroke="#64748b"
              tickLine={false}
              axisLine={false}
              width={72}
              tickFormatter={(value) => {
                const numeric = Number(value);
                return Math.abs(numeric) >= 1000 ? `$${formatCompactNumber(numeric)}` : formatCurrency(numeric);
              }}
            />
            <Tooltip
              formatter={(value: number) => [formatCurrency(Number(value)), 'Equity']}
              labelFormatter={(label: string) => formatTooltipDate(label)}
              contentStyle={{ borderRadius: 16, border: '1px solid rgba(15,23,42,0.08)' }}
            />
            <Line type="monotone" dataKey="equity" stroke="#0f766e" strokeWidth={3} dot={false} />
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
          <XAxis dataKey="t" stroke="#64748b" tickLine={false} axisLine={false} minTickGap={24} tickFormatter={formatAxisDate} height={42} />
          <YAxis
            stroke="#64748b"
            tickLine={false}
            axisLine={false}
            width={72}
            tickFormatter={(value) => {
              const numeric = Number(value);
              return Math.abs(numeric) >= 1000 ? `$${formatCompactNumber(numeric)}` : formatCurrency(numeric);
            }}
          />
          <Tooltip
            formatter={(value: number) => [formatCurrency(Number(value)), 'Equity']}
            labelFormatter={(label: string) => formatTooltipDate(label)}
            contentStyle={{ borderRadius: 16, border: '1px solid rgba(15,23,42,0.08)' }}
          />
          <Line type="monotone" dataKey="equity" stroke="#0f766e" strokeWidth={3} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </ChartFrame>
  );
}
