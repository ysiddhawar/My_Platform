import { PropsWithChildren } from 'react';

type ChartFrameProps = PropsWithChildren<{
  className?: string;
}>;

export function ChartFrame({ children, className }: ChartFrameProps) {
  return <div className={`h-64 w-full ${className || ''}`.trim()}>{children}</div>;
}
