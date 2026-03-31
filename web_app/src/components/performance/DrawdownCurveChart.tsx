import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import { ChartFrame } from '@/components/charts/ChartFrame';

type Point = {
  t: string;
  value: number;
};

type DrawdownCurveChartProps = {
  data: Point[];
};

export function DrawdownCurveChart({ data }: DrawdownCurveChartProps) {
  return (
    <ChartFrame className="h-56">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data}>
          <XAxis dataKey="t" stroke="#64748b" />
          <YAxis stroke="#64748b" />
          <Tooltip />
          <Area type="monotone" dataKey="value" stroke="#ef4444" fill="rgba(239,68,68,0.25)" strokeWidth={2} />
        </AreaChart>
      </ResponsiveContainer>
    </ChartFrame>
  );
}
