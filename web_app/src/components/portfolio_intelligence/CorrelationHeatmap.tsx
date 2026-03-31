import { ResponsiveContainer, Tooltip, XAxis, YAxis, ScatterChart, Scatter, Cell } from 'recharts';

import { ChartFrame } from '@/components/charts/ChartFrame';

type Point = { x: string; y: string; z: number };

function colorForValue(z: number) {
  if (z > 0.7) return '#ef4444';
  if (z > 0.4) return '#f59e0b';
  return '#14b8a6';
}

export function CorrelationHeatmap({ data }: { data: Point[] }) {
  return (
    <ChartFrame className="h-56">
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart>
          <XAxis dataKey="x" type="category" stroke="#64748b" />
          <YAxis dataKey="y" type="category" stroke="#64748b" />
          <Tooltip />
          <Scatter data={data}>
            {data.map((item, index) => (
              <Cell key={`${item.x}-${item.y}-${index}`} fill={colorForValue(item.z)} />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>
    </ChartFrame>
  );
}
