import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import { ChartFrame } from '@/components/charts/ChartFrame';

type Point = { bucket: string; value: number };

export function HoldingTimeChart({ data }: { data: Point[] }) {
  return (
    <ChartFrame className="h-52">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data}>
          <XAxis dataKey="bucket" stroke="#64748b" />
          <YAxis stroke="#64748b" />
          <Tooltip />
          <Area type="monotone" dataKey="value" stroke="#8b5cf6" fill="rgba(139,92,246,0.22)" />
        </AreaChart>
      </ResponsiveContainer>
    </ChartFrame>
  );
}
