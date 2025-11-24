'use client';

import { LucideIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';

export interface ToolbarAction {
  icon: LucideIcon;
  label: string;
  onClick?: () => void;
  href?: string;
  variant?: 'default' | 'ghost' | 'outline' | 'destructive';
  disabled?: boolean;
  tooltip?: string;
}

interface ToolbarProps {
  actions?: ToolbarAction[];
  rightActions?: ToolbarAction[]; // Actions aligned to the right
  title?: string;
  description?: string;
  className?: string;
}

export function Toolbar({
  actions = [],
  rightActions = [],
  title,
  description,
  className,
}: ToolbarProps) {
  if (!actions.length && !rightActions.length && !title) {
    return null;
  }

  const renderActions = (actionList: ToolbarAction[]) => (
    <TooltipProvider delayDuration={300}>
      <div className="flex items-center gap-2">
        {actionList.map((action, index) => {
          const Icon = action.icon;
          const button = (
            <Button
              key={index}
              variant={action.variant || 'ghost'}
              size="sm"
              onClick={action.onClick}
              disabled={action.disabled}
              aria-label={action.label}
              className={cn('gap-2 h-9', action.variant === 'ghost' && 'hover:bg-bg-2')}
            >
              <Icon className="w-4 h-4" aria-hidden="true" />
              <span className="hidden sm:inline" aria-hidden="true">
                {action.label}
              </span>
              <span className="sr-only">{action.label}</span>
            </Button>
          );

          if (action.tooltip) {
            return (
              <Tooltip key={index}>
                <TooltipTrigger asChild>{button}</TooltipTrigger>
                <TooltipContent>
                  <p>{action.tooltip}</p>
                </TooltipContent>
              </Tooltip>
            );
          }

          return button;
        })}
      </div>
    </TooltipProvider>
  );

  return (
    <div
      className={cn(
        'h-12 bg-bg-0 border-b border-white/10 flex items-center px-6 gap-4',
        className
      )}
    >
      {/* Page Title/Description (optional) */}
      {title && (
        <div className="flex flex-col">
          <h1 className="text-sm font-semibold text-fg-0">{title}</h1>
          {description && <p className="text-xs text-fg-2">{description}</p>}
        </div>
      )}

      {/* Left Action Buttons */}
      {actions.length > 0 && renderActions(actions)}

      {/* Spacer */}
      {(actions.length > 0 || title) && rightActions.length > 0 && <div className="flex-1" />}

      {/* Right Action Buttons */}
      {rightActions.length > 0 && (
        <>
          <div className="h-6 w-px bg-white/20" />
          {renderActions(rightActions)}
        </>
      )}
    </div>
  );
}
