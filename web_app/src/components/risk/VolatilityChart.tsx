import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import { ChartFrame } from '@/components/charts/ChartFrame';

type Point = { t: string; value: number };

export function VolatilityChart({ data }: { data: Point[] }) {
  return (
    <ChartFrame className="h-52">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data}>
          <XAxis dataKey="t" stroke="#64748b" />
          <YAxis stroke="#64748b" />
          <Tooltip />
          <Area type="monotone" dataKey="value" stroke="#f59e0b" fill="rgba(245,158,11,0.22)" />
        </AreaChart>
      </ResponsiveContainer>
    </ChartFrame>
  );
}
