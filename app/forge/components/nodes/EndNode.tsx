'use client';

import { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Circle } from 'lucide-react';

export const EndNode = memo(({ data, selected }: NodeProps) => {
  return (
    <div
      className={`
        px-4 py-3 rounded-lg border-2 bg-bg-1 min-w-[180px]
        ${selected ? 'border-red-500 shadow-lg shadow-red-500/20' : 'border-red-600/50'}
      `}
    >
      {/* Input handle */}
      <Handle
        type="target"
        position={Position.Top}
        className="w-3 h-3 bg-red-500 border-2 border-bg-0"
      />

      <div className="flex items-center gap-2 mb-1">
        <Circle className="w-4 h-4 text-red-500" />
        <div className="font-semibold text-fg-0 text-sm">End</div>
      </div>
      <div className="text-xs text-fg-2">{data.label || 'End of workflow'}</div>
    </div>
  );
});

EndNode.displayName = 'EndNode';
