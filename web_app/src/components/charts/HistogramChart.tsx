import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import { ChartFrame } from './ChartFrame';

type HistogramPoint = {
  bucket: string;
  count: number;
};

type HistogramChartProps = {
  values: number[];
  bins?: number;
};

function buildHistogram(values: number[], bins: number): HistogramPoint[] {
  if (!values.length) return [];
  const min = Math.min(...values);
  const max = Math.max(...values);
  if (min === max) {
    return [{ bucket: min.toFixed(2), count: values.length }];
  }

  const width = (max - min) / bins;
  const counts = new Array(bins).fill(0);
  values.forEach((value) => {
    const rawIndex = Math.floor((value - min) / width);
    const index = Math.min(bins - 1, Math.max(0, rawIndex));
    counts[index] += 1;
  });

  return counts.map((count, index) => {
    const start = min + index * width;
    const end = start + width;
    return {
      bucket: `${start.toFixed(2)}-${end.toFixed(2)}`,
      count,
    };
  });
}

export function HistogramChart({ values, bins = 10 }: HistogramChartProps) {
  const data = buildHistogram(values, bins);

  return (
    <ChartFrame>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="bucket" stroke="#64748b" hide={data.length > 8} />
          <YAxis stroke="#64748b" />
          <Tooltip />
          <Bar dataKey="count" fill="#0f766e" radius={[6, 6, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </ChartFrame>
  );
}
