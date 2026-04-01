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
    bg: 'bg-gray-50 dark:bg-gray-900/20',
    border: 'border-gray-200 dark:border-gray-800',
    iconBg: 'bg-gray-100 dark:bg-gray-800',
    iconColor: 'text-gray-600 dark:text-gray-400',
    trendColor: 'text-gray-600 dark:text-gray-400',
  },
};

export function EnhancedMetricCard({ 
  icon, 
  title, 
  value, 
  trend, 
  tone = 'neutral' 
}: EnhancedMetricCardProps) {
  const colors = toneColors[tone];

  return (
    <div className={`flex items-center gap-4 rounded-xl border p-4 ${colors.bg} ${colors.border} dark:bg-opacity-10`}>
      {/* Icon Container */}
      <div className={`flex h-12 w-12 items-center justify-center rounded-lg ${colors.iconBg}`}>
        <div className={colors.iconColor}>
          {icon}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1">
        <p className="text-xs font-medium text-gray-600 dark:text-gray-400">{title}</p>
        <p className="text-xl font-bold text-gray-900 dark:text-white">{value}</p>
        
        {/* Trend Indicator */}
        {trend && (
          <div className={`flex items-center gap-1 text-xs ${colors.trendColor}`}>
            {trendIcons[trend.direction]}
            <span>{trend.label}</span>
            <span className="font-medium">{trend.value}</span>
          </div>
        )}
      </div>
    </div>
  );
}
