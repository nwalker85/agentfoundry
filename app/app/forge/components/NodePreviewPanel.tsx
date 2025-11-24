'use client';

import {
  X,
  Settings,
  Circle,
  GitBranch,
  Wrench,
  Square,
  User,
  Workflow,
  Bot,
  ClipboardList,
  Play,
  ShieldCheck,
  Users,
  Database,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import type { Node } from 'reactflow';

interface NodePreviewPanelProps {
  node: Node;
  onClose: () => void;
  onConfigure: (node: Node) => void;
}

const nodeTypeConfig: Record<string, { icon: any; color: string; label: string }> = {
  entryPoint: { icon: Play, color: 'text-green-400', label: 'Entry Point' },
  process: { icon: Circle, color: 'text-blue-400', label: 'Process' },
  decision: { icon: GitBranch, color: 'text-amber-400', label: 'Decision' },
  toolCall: { icon: Wrench, color: 'text-purple-400', label: 'Tool Call' },
  router: { icon: Workflow, color: 'text-cyan-400', label: 'Router' },
  parallelGateway: { icon: Users, color: 'text-pink-400', label: 'Parallel Gateway' },
  human: { icon: User, color: 'text-orange-400', label: 'Human Input' },
  reactAgent: { icon: Bot, color: 'text-emerald-400', label: 'ReAct Agent' },
  deepPlanner: { icon: ClipboardList, color: 'text-indigo-400', label: 'Task Planner' },
  deepExecutor: { icon: Play, color: 'text-sky-400', label: 'Task Executor' },
  deepCritic: { icon: ShieldCheck, color: 'text-rose-400', label: 'Quality Critic' },
  subAgent: { icon: Bot, color: 'text-violet-400', label: 'Sub-Agent' },
  contextManager: { icon: Database, color: 'text-teal-400', label: 'Context Manager' },
  end: { icon: Square, color: 'text-red-400', label: 'End' },
};

export function NodePreviewPanel({ node, onClose, onConfigure }: NodePreviewPanelProps) {
  const config = nodeTypeConfig[node.type || 'process'] || nodeTypeConfig.process;
  const Icon = config.icon;

  return (
    <div className="w-80 border-l border-white/10 bg-bg-1 flex flex-col h-full">
      {/* Header */}
      <div className="h-12 border-b border-white/10 flex items-center justify-between px-4">
        <div className="flex items-center gap-2">
          <Icon className={`w-4 h-4 ${config.color}`} />
          <span className="text-sm font-medium text-fg-0">Node Details</span>
        </div>
        <Button variant="ghost" size="icon" onClick={onClose} className="h-7 w-7">
          <X className="w-4 h-4" />
        </Button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Node Type */}
        <div>
          <label className="text-xs text-fg-3 uppercase tracking-wide">Type</label>
          <div className="mt-1">
            <Badge variant="outline" className={`${config.color} border-current/40`}>
              {config.label}
            </Badge>
          </div>
        </div>

        {/* Node ID */}
        <div>
          <label className="text-xs text-fg-3 uppercase tracking-wide">Node ID</label>
          <p className="mt-1 text-sm text-fg-1 font-mono bg-bg-0 px-2 py-1 rounded">{node.id}</p>
        </div>

        {/* Label */}
        <div>
          <label className="text-xs text-fg-3 uppercase tracking-wide">Label</label>
          <p className="mt-1 text-sm text-fg-0">{node.data?.label || 'Untitled'}</p>
        </div>

        {/* Description */}
        {node.data?.description && (
          <div>
            <label className="text-xs text-fg-3 uppercase tracking-wide">Description</label>
            <p className="mt-1 text-sm text-fg-2">{node.data.description}</p>
          </div>
        )}

        {/* Position */}
        <div>
          <label className="text-xs text-fg-3 uppercase tracking-wide">Position</label>
          <p className="mt-1 text-sm text-fg-2">
            x: {Math.round(node.position.x)}, y: {Math.round(node.position.y)}
          </p>
        </div>

        {/* Type-specific preview info */}
        {node.type === 'process' && node.data?.model && (
          <div>
            <label className="text-xs text-fg-3 uppercase tracking-wide">Model</label>
            <p className="mt-1 text-sm text-fg-1">{node.data.model}</p>
          </div>
        )}

        {node.type === 'toolCall' && node.data?.tool && (
          <div>
            <label className="text-xs text-fg-3 uppercase tracking-wide">Tool</label>
            <p className="mt-1 text-sm text-fg-1">{node.data.tool}</p>
          </div>
        )}

        {node.type === 'reactAgent' && node.data?.tools?.length > 0 && (
          <div>
            <label className="text-xs text-fg-3 uppercase tracking-wide">Tools</label>
            <p className="mt-1 text-sm text-fg-1">{node.data.tools.length} configured</p>
          </div>
        )}
      </div>

      {/* Footer with Configure button */}
      <div className="border-t border-white/10 p-4">
        <Button onClick={() => onConfigure(node)} className="w-full gap-2">
          <Settings className="w-4 h-4" />
          Configure Node
        </Button>
      </div>
    </div>
  );
}
