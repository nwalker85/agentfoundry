'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import type { Node, Edge } from 'reactflow';
import { GraphEditor } from '../forge/components/GraphEditor';
import { NodeEditor } from '../forge/components/NodeEditor';
import { StateDesignerPanel, type StateSchemaDraft } from '../forge/components/StateDesignerPanel';
import { TriggerRegistryDrawer } from '../forge/components/TriggerRegistryDrawer';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { AlertCircle, Plug, RefreshCw, Save, Workflow as WorkflowIcon } from 'lucide-react';
import {
  listChannelWorkflows,
  saveChannelWorkflow,
  listStateSchemas,
  saveStateSchema as apiSaveStateSchema,
  deleteStateSchema as apiDeleteStateSchema,
  listTriggers,
  saveTrigger,
  deleteTrigger,
  listGraphTriggers,
  saveGraphTriggers,
} from '../forge/lib/designer-api';
import type { ChannelWorkflow, StateSchema, TriggerDefinition } from '@/types';

const CHANNELS: Array<{ value: 'chat' | 'voice' | 'api'; label: string }> = [
  { value: 'chat', label: 'Chat' },
  { value: 'voice', label: 'Voice' },
  { value: 'api', label: 'API' },
];

interface DefaultWorkflow {
  nodes: Node[];
  edges: Edge[];
}

function createDefaultWorkflow(channel: string): DefaultWorkflow {
  const channelName = channel.charAt(0).toUpperCase() + channel.slice(1);
  return {
    nodes: [
      {
        id: 'entry',
        type: 'entryPoint',
        position: { x: 100, y: 120 },
        data: { label: `${channelName} Entry`, description: 'Channel ingress' },
      },
      {
        id: 'io-agent',
        type: 'process',
        position: { x: 320, y: 120 },
        data: {
          label: 'IO Agent',
          description: 'Handles channel-specific IO',
          model: 'gpt-4o-mini',
          temperature: 0.2,
          maxTokens: 512,
        },
      },
      {
        id: 'supervisor',
        type: 'process',
        position: { x: 560, y: 120 },
        data: {
          label: 'Supervisor Agent',
          description: 'Routes to workers',
          model: 'gpt-4o',
          temperature: 0.4,
          maxTokens: 800,
        },
      },
      {
        id: 'goal-manager',
        type: 'process',
        position: { x: 800, y: 120 },
        data: {
          label: 'Goal Manager',
          description: 'Tracks goals & subgoals',
          model: 'gpt-4o-mini',
          temperature: 0.3,
          maxTokens: 400,
        },
      },
      {
        id: 'observability',
        type: 'process',
        position: { x: 560, y: 320 },
        data: {
          label: 'Observability Agent',
          description: 'Telemetry + reporting',
          model: 'gpt-4o-mini',
          temperature: 0.2,
          maxTokens: 200,
        },
      },
      {
        id: 'end',
        type: 'end',
        position: { x: 1040, y: 120 },
        data: { label: 'Complete' },
      },
    ],
    edges: [
      { id: 'entry-io', source: 'entry', target: 'io-agent' },
      { id: 'io-supervisor', source: 'io-agent', target: 'supervisor' },
      { id: 'supervisor-goal', source: 'supervisor', target: 'goal-manager' },
      { id: 'goal-end', source: 'goal-manager', target: 'end' },
      { id: 'supervisor-observability', source: 'supervisor', target: 'observability' },
      { id: 'observability-supervisor', source: 'observability', target: 'supervisor' },
    ],
  };
}

export default function WorkflowsPage() {
  const [channel, setChannel] = useState<'chat' | 'voice' | 'api'>('chat');
  const [workflows, setWorkflows] = useState<ChannelWorkflow[]>([]);
  const [currentWorkflowId, setCurrentWorkflowId] = useState<string | null>(null);
  const [workflowName, setWorkflowName] = useState('Channel Orchestration');
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const [stateSchemas, setStateSchemas] = useState<StateSchema[]>([]);
  const [activeStateSchemaId, setActiveStateSchemaId] = useState<string | null>(null);
  const [isStatePanelOpen, setIsStatePanelOpen] = useState(false);

  const [triggers, setTriggers] = useState<TriggerDefinition[]>([]);
  const [selectedTriggerIds, setSelectedTriggerIds] = useState<string[]>([]);
  const [isTriggerDrawerOpen, setIsTriggerDrawerOpen] = useState(false);

  const activeStateSchema = useMemo(
    () => stateSchemas.find((schema) => schema.id === activeStateSchemaId) ?? null,
    [stateSchemas, activeStateSchemaId]
  );

  const selectedTriggersList = useMemo(
    () => triggers.filter((trigger) => trigger.id && selectedTriggerIds.includes(trigger.id)),
    [triggers, selectedTriggerIds]
  );

  const loadStateSchemas = useCallback(async () => {
    try {
      const schemas = await listStateSchemas();
      setStateSchemas(schemas);
      if (!activeStateSchemaId && schemas.length > 0) {
        setActiveStateSchemaId(schemas[0].id);
      }
    } catch (err) {
      console.error('Failed to load state schemas', err);
      setError('Failed to load state schemas');
    }
  }, [activeStateSchemaId]);

  const loadTriggers = useCallback(async () => {
    try {
      const triggerList = await listTriggers();
      setTriggers(triggerList);
    } catch (err) {
      console.error('Failed to load triggers', err);
      setError('Failed to load triggers');
    }
  }, []);

  const loadChannelWorkflow = useCallback(async (targetChannel: 'chat' | 'voice' | 'api') => {
    setIsLoading(true);
    setError(null);
    try {
      const list = await listChannelWorkflows(targetChannel);
      setWorkflows(list);
      if (list.length > 0) {
        const workflow = list[0];
        setNodes(workflow.nodes as Node[]);
        setEdges(workflow.edges as Edge[]);
        setCurrentWorkflowId(workflow.id);
        setWorkflowName(workflow.name);
        setActiveStateSchemaId(workflow.stateSchemaId ?? null);
      } else {
        const defaults = createDefaultWorkflow(targetChannel);
        setNodes(defaults.nodes);
        setEdges(defaults.edges);
        setCurrentWorkflowId(null);
        setWorkflowName(`${targetChannel.toUpperCase()} Orchestrator`);
      }
      const assignments = await listGraphTriggers('channel', targetChannel);
      setSelectedTriggerIds(assignments.map((assignment) => assignment.triggerId));
    } catch (err) {
      console.error('Failed to load workflow', err);
      setError('Unable to load workflow');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadStateSchemas();
    loadTriggers();
  }, [loadStateSchemas, loadTriggers]);

  useEffect(() => {
    loadChannelWorkflow(channel);
  }, [channel, loadChannelWorkflow]);

  const handleSaveWorkflow = async () => {
    setError(null);
    setSuccessMessage(null);
    setIsLoading(true);
    try {
      const saved = await saveChannelWorkflow({
        id: currentWorkflowId ?? undefined,
        channel,
        name: workflowName || `${channel.toUpperCase()} Orchestrator`,
        description: `${channel} channel orchestrator`,
        nodes,
        edges,
        stateSchemaId: activeStateSchemaId ?? undefined,
        metadata: {},
      });
      setCurrentWorkflowId(saved.id);
      setSuccessMessage('Workflow saved');
    } catch (err) {
      console.error('Failed to save workflow', err);
      setError('Unable to save workflow');
    } finally {
      setIsLoading(false);
      setTimeout(() => setSuccessMessage(null), 3000);
    }
  };

  const handleReset = () => {
    const defaults = createDefaultWorkflow(channel);
    setNodes(defaults.nodes);
    setEdges(defaults.edges);
    setSuccessMessage('Workflow reset to default');
    setTimeout(() => setSuccessMessage(null), 2000);
  };

  const handleStateSchemaSave = async (schemaDraft: StateSchemaDraft) => {
    try {
      const saved = await apiSaveStateSchema({
        id: schemaDraft.id,
        name: schemaDraft.name,
        description: schemaDraft.description,
        version: schemaDraft.version,
        fields: schemaDraft.fields,
        initialState: schemaDraft.initialState,
        tags: schemaDraft.tags,
      });
      setStateSchemas((prev) => {
        const idx = prev.findIndex((schema) => schema.id === saved.id);
        if (idx >= 0) {
          const copy = [...prev];
          copy[idx] = saved;
          return copy;
        }
        return [...prev, saved];
      });
      setActiveStateSchemaId(saved.id);
    } catch (err) {
      console.error('Failed to save schema', err);
      setError('Unable to save state schema');
    }
  };

  const handleStateSchemaDelete = async (schemaId: string) => {
    try {
      await apiDeleteStateSchema(schemaId);
      setStateSchemas((prev) => {
        const filtered = prev.filter((schema) => schema.id !== schemaId);
        if (activeStateSchemaId === schemaId) {
          setActiveStateSchemaId(filtered[0]?.id ?? null);
        }
        return filtered;
      });
    } catch (err) {
      console.error('Failed to delete schema', err);
      setError('Unable to delete state schema');
    }
  };

  const handleTriggerSave = async (triggerDraft: {
    id?: string;
    name: string;
    type: TriggerDefinition['type'];
    description?: string;
    channel?: string;
    config: Record<string, any>;
    isActive: boolean;
  }) => {
    try {
      const saved = await saveTrigger({
        id: triggerDraft.id,
        name: triggerDraft.name,
        type: triggerDraft.type,
        description: triggerDraft.description,
        channel: triggerDraft.channel,
        config: triggerDraft.config,
        isActive: triggerDraft.isActive,
      });
      setTriggers((prev) => {
        const idx = prev.findIndex((trigger) => trigger.id === saved.id);
        if (idx >= 0) {
          const copy = [...prev];
          copy[idx] = saved;
          return copy;
        }
        return [...prev, saved];
      });
    } catch (err) {
      console.error('Failed to save trigger', err);
      setError('Unable to save trigger');
    }
  };

  const handleTriggerDelete = async (triggerId: string) => {
    try {
      await deleteTrigger(triggerId);
      setTriggers((prev) => prev.filter((trigger) => trigger.id !== triggerId));
      setSelectedTriggerIds((prev) => prev.filter((id) => id !== triggerId));
    } catch (err) {
      console.error('Failed to delete trigger', err);
      setError('Unable to delete trigger');
    }
  };

  const handleTriggerAssignment = async (triggerId: string, selected: boolean) => {
    setSelectedTriggerIds((prev) => {
      const exists = prev.includes(triggerId);
      let next = prev;
      if (selected && !exists) {
        next = [...prev, triggerId];
      } else if (!selected && exists) {
        next = prev.filter((id) => id !== triggerId);
      }
      saveGraphTriggers({
        targetType: 'channel',
        targetId: channel,
        triggerIds: next,
      }).catch((err) => {
        console.error('Failed to save channel triggers', err);
        setError('Unable to save channel triggers');
      });
      return next;
    });
  };

  return (
    <div className="flex flex-col h-full">
      <div className="h-12 bg-bg-0 border-b border-white/10 flex items-center px-6 gap-4">
        <WorkflowIcon className="w-4 h-4 text-fg-3" />
        <span className="text-sm font-medium">Core Workflow Designer</span>
        <div className="flex items-center gap-2">
          <span className="text-xs text-fg-3 uppercase tracking-wide">Channel</span>
          <Select
            value={channel}
            onValueChange={(value) => setChannel(value as 'chat' | 'voice' | 'api')}
          >
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {CHANNELS.map((item) => (
                <SelectItem key={item.value} value={item.value}>
                  {item.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="flex-1" />
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={handleReset}>
            <RefreshCw className="w-4 h-4 mr-1" />
            Reset
          </Button>
          <Button
            variant="default"
            size="sm"
            onClick={handleSaveWorkflow}
            disabled={isLoading || nodes.length === 0}
          >
            <Save className="w-4 h-4 mr-1" />
            Save Workflow
          </Button>
        </div>
      </div>

      {(error || successMessage) && (
        <div
          className={`${error ? 'bg-red-500/10 border-red-500/20' : 'bg-green-500/10 border-green-500/20'} border-b px-6 py-3 flex items-center gap-2 text-sm`}
        >
          <AlertCircle className="w-4 h-4" />
          {error ?? successMessage}
        </div>
      )}

      <div className="border-b border-white/10 bg-bg-1 px-6 py-3 flex flex-wrap items-center gap-6">
        <div>
          <div className="text-xs text-fg-3 uppercase tracking-wide">Workflow Name</div>
          <input
            className="bg-bg-0 border border-white/10 rounded px-3 py-1 text-sm"
            value={workflowName}
            onChange={(e) => setWorkflowName(e.target.value)}
          />
        </div>
        <div>
          <div className="text-xs text-fg-3 uppercase tracking-wide">State Schema</div>
          <div className="flex items-center gap-2">
            <Select
              value={activeStateSchemaId ?? 'none'}
              onValueChange={(value) => setActiveStateSchemaId(value === 'none' ? null : value)}
            >
              <SelectTrigger className="w-56">
                <SelectValue placeholder="Select schema" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">No schema</SelectItem>
                {stateSchemas.map((schema) => (
                  <SelectItem key={schema.id} value={schema.id}>
                    {schema.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button size="sm" variant="ghost" onClick={() => setIsStatePanelOpen(true)}>
              Manage
            </Button>
          </div>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <div className="text-xs text-fg-3 uppercase tracking-wide flex items-center gap-2">
            <Plug className="w-4 h-4 text-indigo-400" />
            Channel Triggers
          </div>
          {selectedTriggersList.length === 0 && (
            <Badge variant="outline" className="border-amber-500/40 text-amber-300">
              None
            </Badge>
          )}
          {selectedTriggersList.map((trigger) => (
            <Badge
              key={trigger.id}
              variant="outline"
              className="bg-indigo-500/10 border-indigo-400/30"
            >
              {trigger.name}
            </Badge>
          ))}
          <Button size="sm" variant="ghost" onClick={() => setIsTriggerDrawerOpen(true)}>
            Configure
          </Button>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden relative min-h-0">
        {isLoading && (
          <div className="absolute inset-0 z-10 bg-bg-0/70 backdrop-blur-sm flex items-center justify-center text-sm text-fg-3">
            Loading workflow...
          </div>
        )}
        <div className="flex-1 relative">
          <GraphEditor
            nodes={nodes}
            edges={edges}
            onNodesChange={setNodes}
            onEdgesChange={setEdges}
            onNodeSelect={setSelectedNode}
          />
        </div>
        {selectedNode && (
          <div className="w-80 border-l border-white/10 bg-bg-1 overflow-y-auto">
            <NodeEditor
              node={selectedNode}
              onNodeUpdate={(updatedNode) => {
                setNodes((prev) =>
                  prev.map((node) => (node.id === updatedNode.id ? updatedNode : node))
                );
                setSelectedNode(updatedNode);
              }}
              onNodeDelete={(nodeId) => {
                setNodes((prev) => prev.filter((node) => node.id !== nodeId));
                setEdges((prev) =>
                  prev.filter((edge) => edge.source !== nodeId && edge.target !== nodeId)
                );
                setSelectedNode(null);
              }}
              onClose={() => setSelectedNode(null)}
            />
          </div>
        )}
      </div>

      <StateDesignerPanel
        open={isStatePanelOpen}
        onOpenChange={setIsStatePanelOpen}
        schemas={stateSchemas}
        activeSchemaId={activeStateSchemaId}
        onSelectSchema={(id) => setActiveStateSchemaId(id || null)}
        onSaveSchema={handleStateSchemaSave}
        onDeleteSchema={handleStateSchemaDelete}
      />
      <TriggerRegistryDrawer
        open={isTriggerDrawerOpen}
        onOpenChange={setIsTriggerDrawerOpen}
        triggers={triggers}
        selectedTriggerIds={selectedTriggerIds}
        onToggleTriggerSelection={handleTriggerAssignment}
        onSaveTrigger={handleTriggerSave}
        onDeleteTrigger={handleTriggerDelete}
      />
    </div>
  );
}
