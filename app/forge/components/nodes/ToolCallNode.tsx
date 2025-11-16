'use client';

import { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Wrench } from 'lucide-react';

export const ToolCallNode = memo(({ data, selected }: NodeProps) => {
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

      <div className="flex items-center gap-2 mb-2">
        <Wrench className="w-4 h-4 text-purple-500" />
        <div className="font-semibold text-fg-0 text-sm">{data.label || 'Tool Call'}</div>
      </div>

      {data.description && (
        <div className="text-xs text-fg-2 mb-2">{data.description}</div>
      )}

      {data.tool && (
        <div className="text-xs px-2 py-0.5 rounded bg-purple-600/10 text-purple-400 border border-purple-600/30">
          {data.tool}
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

ToolCallNode.displayName = 'ToolCallNode';
