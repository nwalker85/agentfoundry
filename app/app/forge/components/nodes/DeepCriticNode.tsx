'use client';

import { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { ShieldCheck, AlertTriangle } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

export const DeepCriticNode = memo(({ data, selected }: NodeProps) => {
  const criteriaCount = data.validation_criteria?.length || 0;

  return (
    <div
      className={`
        px-4 py-3 rounded-lg border-2 bg-bg-1 min-w-[200px]
        ${selected ? 'border-amber-500 shadow-lg shadow-amber-500/20' : 'border-amber-600/50'}
      `}
    >
      {/* Input handle */}
      <Handle
        type="target"
        position={Position.Top}
        className="w-3 h-3 bg-amber-500 border-2 border-bg-0"
      />

      <div className="flex items-center gap-2 mb-1">
        <ShieldCheck className="w-4 h-4 text-amber-500" />
        <div className="font-semibold text-fg-0 text-sm">Deep Critic</div>
      </div>

      <div className="text-xs text-fg-2">{data.label || 'Quality validation & feedback'}</div>

      {/* Validation criteria badge */}
      {criteriaCount > 0 && (
        <div className="mt-2 flex items-center gap-1.5">
          <AlertTriangle className="w-3 h-3 text-amber-400" />
          <Badge
            variant="outline"
            className="text-xs bg-amber-500/10 text-amber-300 border-amber-500/30"
          >
            {criteriaCount} criteria
          </Badge>
        </div>
      )}

      {/* Quality threshold badge */}
      {data.quality_threshold && (
        <div className="mt-1.5">
          <Badge
            variant="outline"
            className="text-xs bg-amber-500/10 text-amber-300 border-amber-500/30"
          >
            Threshold: {data.quality_threshold}
          </Badge>
        </div>
      )}

      {/* Auto-replan badge */}
      {data.auto_replan && (
        <div className="mt-1.5">
          <Badge
            variant="outline"
            className="text-xs bg-amber-500/10 text-amber-300 border-amber-500/30"
          >
            Auto-replan enabled
          </Badge>
        </div>
      )}

      {/* Output handle */}
      <Handle
        type="source"
        position={Position.Bottom}
        className="w-3 h-3 bg-amber-500 border-2 border-bg-0"
      />
    </div>
  );
});

DeepCriticNode.displayName = 'DeepCriticNode';
