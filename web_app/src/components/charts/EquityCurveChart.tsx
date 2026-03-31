import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import { ChartFrame } from './ChartFrame';
import { formatCompactNumber, formatCurrency } from '@/utils/format';

type Point = {
  t: string;
  equity: number;
};

type EquityCurveChartProps = {
  data: Point[];
};

export function EquityCurveChart({ data }: EquityCurveChartProps) {
  return (
    <ChartFrame>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(100,116,139,0.14)" vertical={false} />
          <XAxis dataKey="t" stroke="#64748b" tickLine={false} axisLine={false} minTickGap={24} />
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
            labelFormatter={(label: string) => label}
            contentStyle={{ borderRadius: 16, border: '1px solid rgba(15,23,42,0.08)' }}
          />
          <Line type="monotone" dataKey="equity" stroke="#0f766e" strokeWidth={3} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </ChartFrame>
  );
}
