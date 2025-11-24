'use client';

import { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { User, Code2 } from 'lucide-react';

export const HumanNode = memo(({ data, selected }: NodeProps) => {
  return (
    <div
      className={`
        px-4 py-3 rounded-lg border-2 bg-gradient-to-br from-cyan-500/10 to-cyan-600/5 backdrop-blur-sm
        ${selected ? 'border-cyan-500 shadow-lg shadow-cyan-500/20' : 'border-cyan-500/30'}
        transition-all duration-200
      `}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!w-3 !h-3 !bg-cyan-500 !border-2 !border-white"
      />

      <div className="flex items-center gap-2 min-w-[160px]">
        <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-cyan-500/20">
          <User className="w-5 h-5 text-cyan-400" />
        </div>

        <div className="flex-1">
          <div className="font-semibold text-sm text-fg-0">{data.label}</div>
          <div className="text-xs text-cyan-400">Human Input</div>
        </div>

        {data.handler && (
          <div
            className="flex items-center justify-center w-5 h-5 rounded bg-purple-500/20 border border-purple-500/30"
            title="Python Implementation Available"
          >
            <Code2 className="w-3 h-3 text-purple-400" />
          </div>
        )}
      </div>

      {data.description && (
        <div className="mt-2 text-xs text-fg-2 border-t border-white/10 pt-2">
          {data.description}
        </div>
      )}

      <Handle
        type="source"
        position={Position.Bottom}
        className="!w-3 !h-3 !bg-cyan-500 !border-2 !border-white"
      />
    </div>
  );
});

HumanNode.displayName = 'HumanNode';
