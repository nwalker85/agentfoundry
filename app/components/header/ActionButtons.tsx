/**
 * Header Action Buttons Component
 * Consistent toolbar actions for header
 */

import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface HeaderAction {
  id: string;
  label: string;
  icon?: React.ComponentType<{ className?: string }>;
  onClick: () => void;
  variant?: 'default' | 'primary' | 'danger';
  loading?: boolean;
  disabled?: boolean;
}

interface ActionButtonsProps {
  actions: HeaderAction[];
}

export function ActionButtons({ actions }: ActionButtonsProps) {
  return (
    <div className="flex items-center gap-1">
      {actions.map((action) => (
        <button
          key={action.id}
          onClick={action.onClick}
          disabled={action.loading || action.disabled}
          className={cn(
            'px-3 py-1.5 rounded-md text-sm font-medium transition-colors',
            'flex items-center gap-2',
            'disabled:opacity-50 disabled:cursor-not-allowed',
            action.variant === 'primary'
              ? 'bg-blue-600 hover:bg-blue-700 text-white'
              : action.variant === 'danger'
                ? 'bg-red-600 hover:bg-red-700 text-white'
                : 'text-gray-300 hover:bg-gray-800'
          )}
        >
          {action.loading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            action.icon && <action.icon className="w-4 h-4" />
          )}
          <span>{action.label}</span>
        </button>
      ))}
    </div>
  );
}
