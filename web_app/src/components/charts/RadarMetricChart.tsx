import { PolarAngleAxis, PolarGrid, PolarRadiusAxis, Radar, RadarChart, ResponsiveContainer, Tooltip } from 'recharts';

import { ChartFrame } from './ChartFrame';

type RadarPoint = {
  metric: string;
  value: number;
};

type RadarMetricChartProps = {
  data: RadarPoint[];
  color?: string;
};

export function RadarMetricChart({ data, color = '#0f766e' }: RadarMetricChartProps) {
  return (
    <ChartFrame>
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart data={data}>
          <PolarGrid stroke="#cbd5e1" />
          <PolarAngleAxis dataKey="metric" stroke="#64748b" />
          <PolarRadiusAxis stroke="#94a3b8" />
          <Radar dataKey="value" stroke={color} fill={color} fillOpacity={0.28} />
          <Tooltip />
        </RadarChart>
      </ResponsiveContainer>
    </ChartFrame>
  );
}
