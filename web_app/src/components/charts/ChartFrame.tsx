import { PropsWithChildren } from 'react';

type ChartFrameProps = PropsWithChildren<{
  className?: string;
}>;

export function ChartFrame({ children, className }: ChartFrameProps) {
  const hasCustomHeight = className?.includes('h-[');
  return <div className={`${hasCustomHeight ? 'w-full' : 'h-64 w-full'} ${className || ''}`.trim()}>{children}</div>;
}
