'use client';

import { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Database, FileArchive } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

export const ContextManagerNode = memo(({ data, selected }: NodeProps) => {
  return (
    <div
      className={`
        px-4 py-3 rounded-lg border-2 bg-bg-1 min-w-[200px]
        ${selected ? 'border-rose-500 shadow-lg shadow-rose-500/20' : 'border-rose-600/50'}
      `}
    >
      {/* Input handle */}
      <Handle
        type="target"
        position={Position.Top}
        className="w-3 h-3 bg-rose-500 border-2 border-bg-0"
      />

      <div className="flex items-center gap-2 mb-1">
        <Database className="w-4 h-4 text-rose-500" />
        <div className="font-semibold text-fg-0 text-sm">Context Manager</div>
      </div>

      <div className="text-xs text-fg-2">{data.label || 'Offload & summarize large outputs'}</div>

      {/* Size threshold badge */}
      {data.size_threshold && (
        <div className="mt-2 flex items-center gap-1.5">
          <FileArchive className="w-3 h-3 text-rose-400" />
          <Badge
            variant="outline"
            className="text-xs bg-rose-500/10 text-rose-300 border-rose-500/30"
          >
            {(data.size_threshold / 1000).toFixed(0)}K threshold
          </Badge>
        </div>
      )}

      {/* Offload strategy badge */}
      {data.offload_strategy && (
        <div className="mt-1.5">
          <Badge
            variant="outline"
            className="text-xs bg-rose-500/10 text-rose-300 border-rose-500/30"
          >
            {data.offload_strategy}
          </Badge>
        </div>
      )}

      {/* Auto-summarize badge */}
      {data.auto_summarize && (
        <div className="mt-1.5">
          <Badge
            variant="outline"
            className="text-xs bg-rose-500/10 text-rose-300 border-rose-500/30"
          >
            Auto-summarize enabled
          </Badge>
        </div>
      )}

      {/* Output handle */}
      <Handle
        type="source"
        position={Position.Bottom}
        className="w-3 h-3 bg-rose-500 border-2 border-bg-0"
      />
    </div>
  );
});

ContextManagerNode.displayName = 'ContextManagerNode';
