import { ReactNode } from 'react';

type TrendDirection = 'up' | 'down' | 'neutral';

type EnhancedMetricCardProps = {
  icon: ReactNode;
  title: string;
  value: string;
  trend?: {
    direction: TrendDirection;
    value: string;
    label: string;
  };
  tone?: 'good' | 'caution' | 'risk' | 'neutral';
  compact?: boolean;
  showTrend?: boolean;
};

const trendIcons = {
  up: (
    <svg className="h-3 w-3 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
    </svg>
  ),
  down: (
    <svg className="h-3 w-3 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
    </svg>
  ),
  neutral: (
    <svg className="h-3 w-3 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14" />
    </svg>
  ),
};

const toneColors = {
  good: {
    bg: 'bg-green-50 dark:bg-green-900/20',
    border: 'border-green-200 dark:border-green-800',
    iconBg: 'bg-green-100 dark:bg-green-800',
    iconColor: 'text-green-600 dark:text-green-400',
    trendColor: 'text-green-600 dark:text-green-400',
  },
  caution: {
    bg: 'bg-amber-50 dark:bg-amber-900/20',
    border: 'border-amber-200 dark:border-amber-800',
    iconBg: 'bg-amber-100 dark:bg-amber-800',
    iconColor: 'text-amber-600 dark:text-amber-400',
    trendColor: 'text-amber-600 dark:text-amber-400',
  },
  risk: {
    bg: 'bg-red-50 dark:bg-red-900/20',
    border: 'border-red-200 dark:border-red-800',
    iconBg: 'bg-red-100 dark:bg-red-800',
    iconColor: 'text-red-600 dark:text-red-400',
    trendColor: 'text-red-600 dark:text-red-400',
  },
  neutral: {
    bg: 'bg-[#e0f2fe] dark:bg-[#082f49]/55',
    border: 'border-[#7dd3fc] dark:border-[#38bdf8]/40',
    iconBg: 'bg-[#dbeafe] dark:bg-[#0c4a6e]',
    iconColor: 'text-[#0284c7] dark:text-[#7dd3fc]',
    trendColor: 'text-[#0369a1] dark:text-[#bae6fd]',
  },
};

export function EnhancedMetricCard({ 
  icon, 
  title, 
  value, 
  trend, 
  tone = 'neutral',
  compact = false,
  showTrend = true,
}: EnhancedMetricCardProps) {
  const colors = toneColors[tone];
  const containerClass = compact
    ? 'gap-2 rounded-[14px] p-2'
    : 'gap-4 rounded-xl p-4';
  const iconWrapClass = compact
    ? 'h-7 w-7 rounded-md'
    : 'h-12 w-12 rounded-lg';
  const titleClass = compact
    ? 'text-[9px]'
    : 'text-xs';
  const valueClass = compact
    ? 'text-[16px]'
    : 'text-xl';
  const trendClass = compact
    ? 'text-[10px]'
    : 'text-xs';

  return (
    <div className={`flex items-center ${containerClass} border transition-all duration-200 hover:border-[#ff5900] hover:shadow-[0_18px_44px_rgba(255,89,0,0.12)] dark:hover:border-[#ff5900] dark:hover:shadow-[0_18px_44px_rgba(255,89,0,0.12)] ${colors.bg} ${colors.border} dark:bg-opacity-10`}>
      {/* Icon Container */}
      <div className={`flex ${iconWrapClass} items-center justify-center ${colors.iconBg}`}>
        <div className={colors.iconColor}>
          {icon}
        </div>
      </div>

      {/* Content */}
      <div className="min-w-0 flex-1">
        <p className={`${titleClass} truncate font-medium text-gray-600 dark:text-gray-400`}>{title}</p>
        <p className={`${valueClass} truncate font-bold text-gray-900 dark:text-white`}>{value}</p>
        
        {/* Trend Indicator */}
        {showTrend && trend && (
          <div className={`flex items-center gap-1 ${trendClass} ${colors.trendColor}`}>
            {trendIcons[trend.direction]}
            <span className="truncate">{trend.label}</span>
            <span className="truncate font-medium">{trend.value}</span>
          </div>
        )}
      </div>
    </div>
  );
}
