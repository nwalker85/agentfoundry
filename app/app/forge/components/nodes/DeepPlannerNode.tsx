'use client';

import { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { ClipboardList, CheckSquare } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

export const DeepPlannerNode = memo(({ data, selected }: NodeProps) => {
  return (
    <div
      className={`
        px-4 py-3 rounded-lg border-2 bg-bg-1 min-w-[200px]
        ${selected ? 'border-purple-500 shadow-lg shadow-purple-500/20' : 'border-purple-600/50'}
      `}
    >
      {/* Input handle */}
      <Handle
        type="target"
        position={Position.Top}
        className="w-3 h-3 bg-purple-500 border-2 border-bg-0"
      />

      <div className="flex items-center gap-2 mb-1">
        <ClipboardList className="w-4 h-4 text-purple-500" />
        <div className="font-semibold text-fg-0 text-sm">Deep Planner</div>
      </div>

      <div className="text-xs text-fg-2">{data.label || 'Task decomposition & planning'}</div>

      {/* Strategy badge */}
      {data.strategy && (
        <div className="mt-2 flex items-center gap-1.5">
          <CheckSquare className="w-3 h-3 text-purple-400" />
          <Badge
            variant="outline"
            className="text-xs bg-purple-500/10 text-purple-300 border-purple-500/30"
          >
            {data.strategy}
          </Badge>
        </div>
      )}

      {/* Max subtasks badge */}
      {data.max_subtasks && (
        <div className="mt-1.5">
          <Badge
            variant="outline"
            className="text-xs bg-purple-500/10 text-purple-300 border-purple-500/30"
          >
            Max tasks: {data.max_subtasks}
          </Badge>
        </div>
      )}

      {/* Output handle */}
      <Handle
        type="source"
        position={Position.Bottom}
        className="w-3 h-3 bg-purple-500 border-2 border-bg-0"
      />
    </div>
  );
});

DeepPlannerNode.displayName = 'DeepPlannerNode';
