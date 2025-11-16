/**
 * Agent Foundry - Metric Card Component
 * Standardized metric display card with optional trend indicator
 */

import { LucideIcon, TrendingUp, TrendingDown, Minus } from "lucide-react";
import { cn } from "@/lib/utils";

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: LucideIcon;
  trend?: {
    value: number;
    direction: 'up' | 'down' | 'neutral';
    label?: string;
  };
  className?: string;
}

export function MetricCard({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  className,
}: MetricCardProps) {
  const getTrendIcon = () => {
    if (!trend) return null;
    switch (trend.direction) {
      case 'up':
        return <TrendingUp className="w-4 h-4" />;
      case 'down':
        return <TrendingDown className="w-4 h-4" />;
      case 'neutral':
        return <Minus className="w-4 h-4" />;
    }
  };

  const getTrendColor = () => {
    if (!trend) return '';
    switch (trend.direction) {
      case 'up':
        return 'text-green-500';
      case 'down':
        return 'text-red-500';
      case 'neutral':
        return 'text-fg-2';
    }
  };

  return (
    <div
      className={cn(
        "bg-bg-1 border border-white/10 rounded-lg p-6 hover:border-white/20 transition-colors",
        className
      )}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-fg-2 mb-1">{title}</p>
          <p className="text-2xl font-bold text-fg-0 tabular-nums">{value}</p>
          {subtitle && (
            <p className="text-xs text-fg-2 mt-1">{subtitle}</p>
          )}
        </div>
        {Icon && (
          <div className="w-10 h-10 rounded-lg bg-blue-600/10 flex items-center justify-center flex-shrink-0">
            <Icon className="w-5 h-5 text-blue-500" />
          </div>
        )}
      </div>
      {trend && (
        <div className={cn("flex items-center gap-1 text-sm", getTrendColor())}>
          {getTrendIcon()}
          <span className="font-medium">
            {trend.value > 0 ? '+' : ''}
            {trend.value}%
          </span>
          {trend.label && (
            <span className="text-fg-2 ml-1">{trend.label}</span>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * Compact version for tighter layouts
 */
export function CompactMetricCard({
  label,
  value,
  className,
}: {
  label: string;
  value: string | number;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-col gap-1", className)}>
      <span className="text-xs text-fg-2">{label}</span>
      <span className="text-lg font-semibold text-fg-0 tabular-nums">{value}</span>
    </div>
  );
}
