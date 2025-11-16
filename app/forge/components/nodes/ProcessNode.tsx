'use client';

import { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Square, Brain } from 'lucide-react';

export const ProcessNode = memo(({ data, selected }: NodeProps) => {
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

      <div className="flex items-center gap-2 mb-2">
        <Brain className="w-4 h-4 text-blue-500" />
        <div className="font-semibold text-fg-0 text-sm">{data.label || 'Process'}</div>
      </div>

      {data.description && (
        <div className="text-xs text-fg-2 mb-2">{data.description}</div>
      )}

      <div className="flex flex-wrap gap-1">
        {data.model && (
          <div className="text-xs px-2 py-0.5 rounded bg-blue-600/10 text-blue-400 border border-blue-600/30">
            {data.model}
          </div>
        )}
        {data.temperature !== undefined && (
          <div className="text-xs px-2 py-0.5 rounded bg-bg-2 text-fg-2">
            temp: {data.temperature}
          </div>
        )}
      </div>

      {/* Output handle */}
      <Handle
        type="source"
        position={Position.Bottom}
        className="w-3 h-3 bg-blue-500 border-2 border-bg-0"
      />
    </div>
  );
});

ProcessNode.displayName = 'ProcessNode';
