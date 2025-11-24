'use client';

import { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Play, Layers } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

export const DeepExecutorNode = memo(({ data, selected }: NodeProps) => {
  const middlewareCount = [
    data.enable_todos,
    data.enable_filesystem,
    data.enable_subagents,
    data.enable_summarization,
  ].filter(Boolean).length;

  return (
    <div
      className={`
        px-4 py-3 rounded-lg border-2 bg-bg-1 min-w-[200px]
        ${selected ? 'border-blue-500 shadow-lg shadow-blue-500/20' : 'border-blue-600/50'}
      `}
    >
      {/* Input handle */}
      <Handle
        type="target"
        position={Position.Top}
        className="w-3 h-3 bg-blue-500 border-2 border-bg-0"
      />

      <div className="flex items-center gap-2 mb-1">
        <Play className="w-4 h-4 text-blue-500" />
        <div className="font-semibold text-fg-0 text-sm">Deep Executor</div>
      </div>

      <div className="text-xs text-fg-2">{data.label || 'Execute tasks with middleware'}</div>

      {/* Model badge */}
      {data.model && (
        <div className="mt-2 flex items-center gap-1.5">
          <Badge
            variant="outline"
            className="text-xs bg-blue-500/10 text-blue-300 border-blue-500/30"
          >
            {data.model}
          </Badge>
        </div>
      )}

      {/* Middleware badge */}
      {middlewareCount > 0 && (
        <div className="mt-1.5 flex items-center gap-1.5">
          <Layers className="w-3 h-3 text-blue-400" />
          <Badge
            variant="outline"
            className="text-xs bg-blue-500/10 text-blue-300 border-blue-500/30"
          >
            {middlewareCount} middleware
          </Badge>
        </div>
      )}

      {/* Max iterations badge */}
      {data.max_iterations && (
        <div className="mt-1.5">
          <Badge
            variant="outline"
            className="text-xs bg-blue-500/10 text-blue-300 border-blue-500/30"
          >
            Max iterations: {data.max_iterations}
          </Badge>
        </div>
      )}

      {/* Output handle */}
      <Handle
        type="source"
        position={Position.Bottom}
        className="w-3 h-3 bg-blue-500 border-2 border-bg-0"
      />
    </div>
  );
});

DeepExecutorNode.displayName = 'DeepExecutorNode';
