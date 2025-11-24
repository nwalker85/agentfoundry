'use client';

import { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Users, Wrench } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

export const SubAgentNode = memo(({ data, selected }: NodeProps) => {
  const toolsCount = data.tools?.length || 0;

  return (
    <div
      className={`
        px-4 py-3 rounded-lg border-2 bg-bg-1 min-w-[200px]
        ${selected ? 'border-cyan-500 shadow-lg shadow-cyan-500/20' : 'border-cyan-600/50'}
      `}
    >
      {/* Input handle */}
      <Handle
        type="target"
        position={Position.Top}
        className="w-3 h-3 bg-cyan-500 border-2 border-bg-0"
      />

      <div className="flex items-center gap-2 mb-1">
        <Users className="w-4 h-4 text-cyan-500" />
        <div className="font-semibold text-fg-0 text-sm">Sub-Agent</div>
      </div>

      <div className="text-xs text-fg-2">{data.label || 'Delegate to specialized agent'}</div>

      {/* Specialization badge */}
      {data.specialization && (
        <div className="mt-2">
          <Badge
            variant="outline"
            className="text-xs bg-cyan-500/10 text-cyan-300 border-cyan-500/30"
          >
            {data.specialization}
          </Badge>
        </div>
      )}

      {/* Tools badge */}
      {toolsCount > 0 && (
        <div className="mt-1.5 flex items-center gap-1.5">
          <Wrench className="w-3 h-3 text-cyan-400" />
          <Badge
            variant="outline"
            className="text-xs bg-cyan-500/10 text-cyan-300 border-cyan-500/30"
          >
            {toolsCount} tools
          </Badge>
        </div>
      )}

      {/* Max depth badge */}
      {data.max_depth && (
        <div className="mt-1.5">
          <Badge
            variant="outline"
            className="text-xs bg-cyan-500/10 text-cyan-300 border-cyan-500/30"
          >
            Max depth: {data.max_depth}
          </Badge>
        </div>
      )}

      {/* Output handle */}
      <Handle
        type="source"
        position={Position.Bottom}
        className="w-3 h-3 bg-cyan-500 border-2 border-bg-0"
      />
    </div>
  );
});

SubAgentNode.displayName = 'SubAgentNode';
