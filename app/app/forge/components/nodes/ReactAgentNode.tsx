'use client';

import { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Bot, Zap } from 'lucide-react';

export const ReactAgentNode = memo(({ data, selected }: NodeProps) => {
  const toolCount = data.tools?.length || 0;
  const maxIterations = data.max_iterations || 10;

  return (
    <div
      className={`
        px-4 py-3 rounded-lg border-2 bg-gradient-to-br from-indigo-500/10 to-indigo-600/5 backdrop-blur-sm
        ${selected ? 'border-indigo-500 shadow-lg shadow-indigo-500/20' : 'border-indigo-500/30'}
        transition-all duration-200
      `}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!w-3 !h-3 !bg-indigo-500 !border-2 !border-white"
      />

      <div className="flex items-center gap-2 min-w-[160px]">
        <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-indigo-500/20 relative">
          <Bot className="w-5 h-5 text-indigo-400" />
          <Zap className="w-3 h-3 text-yellow-400 absolute -top-0.5 -right-0.5" />
        </div>

        <div className="flex-1">
          <div className="font-semibold text-sm text-fg-0">{data.label}</div>
          <div className="text-xs text-indigo-400">
            ReAct • {toolCount} tools • max {maxIterations} iter
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
        className="!w-3 !h-3 !bg-indigo-500 !border-2 !border-white"
      />
    </div>
  );
});

ReactAgentNode.displayName = 'ReactAgentNode';
