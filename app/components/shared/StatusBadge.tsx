/**
 * Agent Foundry - Status Badge Component
 * Standardized status indicator with color coding
 */

import { cn } from "@/lib/utils";
import { Circle } from "lucide-react";

type StatusType =
  | 'active'
  | 'inactive'
  | 'success'
  | 'error'
  | 'warning'
  | 'pending'
  | 'running'
  | 'complete'
  | 'failed'
  | 'draft'
  | 'archived'
  | 'connected'
  | 'disconnected'
  | 'rolled_back'
  | 'cancelled';

interface StatusBadgeProps {
  status: StatusType;
  label?: string;
  showDot?: boolean;
  className?: string;
}

const statusConfig: Record<
  StatusType,
  { color: string; bgColor: string; label: string }
> = {
  active: {
    color: "text-green-500",
    bgColor: "bg-green-500/10",
    label: "Active",
  },
  inactive: {
    color: "text-fg-2",
    bgColor: "bg-fg-2/10",
    label: "Inactive",
  },
  success: {
    color: "text-green-500",
    bgColor: "bg-green-500/10",
    label: "Success",
  },
  error: {
    color: "text-red-500",
    bgColor: "bg-red-500/10",
    label: "Error",
  },
  warning: {
    color: "text-yellow-500",
    bgColor: "bg-yellow-500/10",
    label: "Warning",
  },
  pending: {
    color: "text-blue-500",
    bgColor: "bg-blue-500/10",
    label: "Pending",
  },
  running: {
    color: "text-blue-500",
    bgColor: "bg-blue-500/10",
    label: "Running",
  },
  complete: {
    color: "text-green-500",
    bgColor: "bg-green-500/10",
    label: "Complete",
  },
  failed: {
    color: "text-red-500",
    bgColor: "bg-red-500/10",
    label: "Failed",
  },
  draft: {
    color: "text-fg-2",
    bgColor: "bg-fg-2/10",
    label: "Draft",
  },
  archived: {
    color: "text-fg-2",
    bgColor: "bg-fg-2/10",
    label: "Archived",
  },
  connected: {
    color: "text-green-500",
    bgColor: "bg-green-500/10",
    label: "Connected",
  },
  disconnected: {
    color: "text-red-500",
    bgColor: "bg-red-500/10",
    label: "Disconnected",
  },
  rolled_back: {
    color: "text-yellow-500",
    bgColor: "bg-yellow-500/10",
    label: "Rolled Back",
  },
  cancelled: {
    color: "text-fg-2",
    bgColor: "bg-fg-2/10",
    label: "Cancelled",
  },
};

export function StatusBadge({
  status,
  label,
  showDot = true,
  className,
}: StatusBadgeProps) {
  const config = statusConfig[status];
  const displayLabel = label || config.label;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium",
        config.bgColor,
        config.color,
        className
      )}
    >
      {showDot && <Circle className="w-2 h-2 fill-current" />}
      {displayLabel}
    </span>
  );
}
