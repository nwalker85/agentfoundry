'use client';

import { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { GitBranch } from 'lucide-react';

export const RouterNode = memo(({ data, selected }: NodeProps) => {
  const routeCount = data.routes?.length || 0;

  return (
    <div
      className={`
        px-4 py-3 rounded-lg border-2 bg-gradient-to-br from-orange-500/10 to-orange-600/5 backdrop-blur-sm
        ${selected ? 'border-orange-500 shadow-lg shadow-orange-500/20' : 'border-orange-500/30'}
        transition-all duration-200
      `}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!w-3 !h-3 !bg-orange-500 !border-2 !border-white"
      />

      <div className="flex items-center gap-2 min-w-[160px]">
        <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-orange-500/20">
          <GitBranch className="w-5 h-5 text-orange-400" />
        </div>

        <div className="flex-1">
          <div className="font-semibold text-sm text-fg-0">{data.label}</div>
          <div className="text-xs text-orange-400">
            {routeCount} {routeCount === 1 ? 'route' : 'routes'}
          </div>
        </div>
      </div>

      {data.description && (
        <div className="mt-2 text-xs text-fg-2 border-t border-white/10 pt-2">
          {data.description}
        </div>
      )}

      <Handle
        type="source"
        position={Position.Bottom}
        className="!w-3 !h-3 !bg-orange-500 !border-2 !border-white"
      />
    </div>
  );
});

RouterNode.displayName = 'RouterNode';
