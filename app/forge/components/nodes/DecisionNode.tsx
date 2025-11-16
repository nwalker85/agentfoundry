'use client';

import { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { GitBranch } from 'lucide-react';

export const DecisionNode = memo(({ data, selected }: NodeProps) => {
  return (
    <div
      className={`
        px-4 py-3 rounded-lg border-2 bg-bg-1 min-w-[180px]
        ${selected ? 'border-yellow-500 shadow-lg shadow-yellow-500/20' : 'border-yellow-600/50'}
      `}
    >
      {/* Input handle */}
      <Handle
        type="target"
        position={Position.Top}
        className="w-3 h-3 bg-yellow-500 border-2 border-bg-0"
      />

      <div className="flex items-center gap-2 mb-2">
        <GitBranch className="w-4 h-4 text-yellow-500" />
        <div className="font-semibold text-fg-0 text-sm">{data.label || 'Decision'}</div>
      </div>

      {data.description && (
        <div className="text-xs text-fg-2 mb-2">{data.description}</div>
      )}

      {data.conditions && data.conditions.length > 0 && (
        <div className="text-xs text-fg-2">
          {data.conditions.length} condition{data.conditions.length !== 1 ? 's' : ''}
        </div>
      )}

      {/* Output handles - multiple for different branches */}
      <Handle
        type="source"
        position={Position.Bottom}
        id="default"
        className="w-3 h-3 bg-yellow-500 border-2 border-bg-0"
        style={{ left: '50%' }}
      />
      <Handle
        type="source"
        position={Position.Right}
        id="true"
        className="w-3 h-3 bg-green-500 border-2 border-bg-0"
      />
      <Handle
        type="source"
        position={Position.Left}
        id="false"
        className="w-3 h-3 bg-red-500 border-2 border-bg-0"
      />
    </div>
  );
});

DecisionNode.displayName = 'DecisionNode';
