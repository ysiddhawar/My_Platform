import { Cell, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis } from 'recharts';

import { ChartFrame } from '@/components/charts/ChartFrame';

type Point = { t: number; value: number; regime: string };

const regimeColor: Record<string, string> = {
  low: '#22c55e',
  medium: '#f59e0b',
  high: '#ef4444'
};

export function RegimeDetectionChart({ data }: { data: Point[] }) {
  return (
    <ChartFrame className="h-52">
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart>
          <XAxis dataKey="t" stroke="#64748b" />
          <YAxis dataKey="value" stroke="#64748b" />
          <Tooltip />
          <Scatter data={data}>
            {data.map((item, index) => (
              <Cell key={`${item.t}-${index}`} fill={regimeColor[item.regime] || '#38bdf8'} />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>
    </ChartFrame>
  );
}
