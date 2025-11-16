/**
 * Agent Foundry - Loading State Component
 * Standardized loading indicator with optional message
 */

import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface LoadingStateProps {
  message?: string;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

export function LoadingState({
  message,
  className,
  size = 'md',
}: LoadingStateProps) {
  const iconSizes = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  };

  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center py-16 px-4",
        className
      )}
    >
      <Loader2 className={cn("animate-spin text-blue-500", iconSizes[size])} />
      {message && (
        <p className="text-sm text-fg-2 mt-4">{message}</p>
      )}
    </div>
  );
}

/**
 * Inline loading spinner for buttons or inline elements
 */
export function LoadingSpinner({ className }: { className?: string }) {
  return <Loader2 className={cn("w-4 h-4 animate-spin", className)} />;
}
