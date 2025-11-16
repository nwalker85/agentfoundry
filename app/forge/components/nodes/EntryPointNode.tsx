'use client';

import { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Circle } from 'lucide-react';

export const EntryPointNode = memo(({ data, selected }: NodeProps) => {
  return (
    <div
      className={`
        px-4 py-3 rounded-lg border-2 bg-bg-1 min-w-[180px]
        ${selected ? 'border-green-500 shadow-lg shadow-green-500/20' : 'border-green-600/50'}
      `}
    >
      <div className="flex items-center gap-2 mb-1">
        <Circle className="w-4 h-4 text-green-500" />
        <div className="font-semibold text-fg-0 text-sm">Entry Point</div>
      </div>
      <div className="text-xs text-fg-2">{data.label || 'Start of workflow'}</div>

      {/* Output handle */}
      <Handle
        type="source"
        position={Position.Bottom}
        className="w-3 h-3 bg-green-500 border-2 border-bg-0"
      />
    </div>
  );
});

EntryPointNode.displayName = 'EntryPointNode';
