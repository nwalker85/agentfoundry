/**
 * Agent Foundry - Page Header Component
 * Standardized page header with title, description, and actions
 */

import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { LucideIcon } from 'lucide-react';

interface PageHeaderProps {
  title: string;
  description?: string;
  icon?: LucideIcon;
  badge?: {
    label: string;
    variant?: 'default' | 'secondary' | 'outline';
  };
  actions?: React.ReactNode;
  className?: string;
}

export function PageHeader({
  title,
  description,
  icon: Icon,
  badge,
  actions,
  className,
}: PageHeaderProps) {
  return (
    <div className={cn('border-b border-white/10 bg-bg-1 px-8 py-6', className)}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 mb-2">
            {Icon && <Icon className="w-6 h-6 text-fg-1" />}
            <h1 className="text-2xl font-bold text-fg-0">{title}</h1>
            {badge && (
              <span
                className={cn(
                  'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                  badge.variant === 'secondary'
                    ? 'bg-fg-2/10 text-fg-2'
                    : badge.variant === 'outline'
                      ? 'border border-white/20 text-fg-1'
                      : 'bg-blue-600/10 text-blue-500'
                )}
              >
                {badge.label}
              </span>
            )}
          </div>
          {description && <p className="text-sm text-fg-2 max-w-3xl">{description}</p>}
        </div>
        {actions && <div className="flex items-center gap-2">{actions}</div>}
      </div>
    </div>
  );
}
