import { Fragment } from 'react';

import { ChartFrame } from './ChartFrame';

type HeatmapChartProps = {
  labelsX: string[];
  labelsY: string[];
  matrix: number[][];
};

function heatColor(value: number, maxMagnitude: number) {
  if (!Number.isFinite(value) || maxMagnitude <= 0) return 'rgba(148, 163, 184, 0.18)';
  const intensity = Math.min(1, Math.abs(value) / maxMagnitude);
  if (value >= 0) return `rgba(15, 118, 110, ${0.18 + intensity * 0.62})`;
  return `rgba(185, 28, 28, ${0.18 + intensity * 0.62})`;
}

export function HeatmapChart({ labelsX, labelsY, matrix }: HeatmapChartProps) {
  const maxMagnitude = matrix.flat().reduce((max, value) => Math.max(max, Math.abs(value || 0)), 0);

  return (
    <ChartFrame className="overflow-auto">
      <div
        className="grid gap-2"
        style={{ gridTemplateColumns: `92px repeat(${labelsX.length}, minmax(50px, 1fr))` }}
      >
        <div />
        {labelsX.map((label) => (
          <div key={label} className="text-center text-xs font-semibold text-black/65 dark:text-white/65">
            {label}
          </div>
        ))}
        {labelsY.map((label, rowIndex) => (
          <Fragment key={label}>
            <div key={`${label}-label`} className="flex items-center text-xs font-semibold text-black/65 dark:text-white/65">
              {label}
            </div>
            {labelsX.map((_, colIndex) => {
              const value = matrix[rowIndex]?.[colIndex] || 0;
              return (
                <div
                  key={`${label}-${colIndex}`}
                  className="flex h-12 items-center justify-center rounded-xl text-[11px] font-semibold text-black dark:text-white"
                  style={{ backgroundColor: heatColor(value, maxMagnitude) }}
                  title={`${label} -> ${labelsX[colIndex]}: ${value.toFixed(2)}`}
                >
                  {value.toFixed(2)}
                </div>
              );
            })}
          </Fragment>
        ))}
      </div>
    </ChartFrame>
  );
}
