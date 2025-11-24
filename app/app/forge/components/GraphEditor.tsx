'use client';

import { useCallback, useEffect, useMemo } from 'react';
import ReactFlow, {
  Node,
  Edge,
  addEdge,
  Connection,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  MiniMap,
  BackgroundVariant,
  Panel,
  NodeTypes,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { EntryPointNode } from './nodes/EntryPointNode';
import { ProcessNode } from './nodes/ProcessNode';
import { DecisionNode } from './nodes/DecisionNode';
import { ToolCallNode } from './nodes/ToolCallNode';
import { EndNode } from './nodes/EndNode';
import { RouterNode } from './nodes/RouterNode';
import { ParallelGatewayNode } from './nodes/ParallelGatewayNode';
import { HumanNode } from './nodes/HumanNode';
import { ReactAgentNode } from './nodes/ReactAgentNode';
import { DeepPlannerNode } from './nodes/DeepPlannerNode';
import { DeepExecutorNode } from './nodes/DeepExecutorNode';
import { DeepCriticNode } from './nodes/DeepCriticNode';
import { SubAgentNode } from './nodes/SubAgentNode';
import { ContextManagerNode } from './nodes/ContextManagerNode';
import { Button } from '@/components/ui/button';
import {
  Circle,
  Square,
  User,
  GitGraph,
} from 'lucide-react';
import { exportMermaidDiagram } from '../lib/graph-to-mermaid';

interface GraphEditorProps {
  nodes: Node[];
  edges: Edge[];
  onNodesChange: (nodes: Node[]) => void;
  onEdgesChange: (edges: Edge[]) => void;
  onNodeSelect: (node: Node | null) => void;
}

// Memoize nodeTypes to prevent React Flow warning
const nodeTypes: NodeTypes = {
  entryPoint: EntryPointNode,
  process: ProcessNode,
  decision: DecisionNode,
  toolCall: ToolCallNode,
  router: RouterNode,
  parallelGateway: ParallelGatewayNode,
  human: HumanNode,
  reactAgent: ReactAgentNode,
  deepPlanner: DeepPlannerNode,
  deepExecutor: DeepExecutorNode,
  deepCritic: DeepCriticNode,
  subAgent: SubAgentNode,
  contextManager: ContextManagerNode,
  end: EndNode,
};

export function GraphEditor({
  nodes: initialNodes,
  edges: initialEdges,
  onNodesChange,
  onEdgesChange,
  onNodeSelect,
}: GraphEditorProps) {
  const [nodes, setNodes, onNodesChangeInternal] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChangeInternal] = useEdgesState(initialEdges);

  useEffect(() => {
    setNodes(initialNodes);
  }, [initialNodes, setNodes]);

  useEffect(() => {
    setEdges(initialEdges);
  }, [initialEdges, setEdges]);

  // Sync internal state with props
  const handleNodesChange = useCallback(
    (changes: any) => {
      onNodesChangeInternal(changes);
      // Update parent
      setTimeout(() => {
        setNodes((nds) => {
          onNodesChange(nds);
          return nds;
        });
      }, 0);
    },
    [onNodesChangeInternal, onNodesChange]
  );

  const handleEdgesChange = useCallback(
    (changes: any) => {
      onEdgesChangeInternal(changes);
      // Update parent
      setTimeout(() => {
        setEdges((eds) => {
          onEdgesChange(eds);
          return eds;
        });
      }, 0);
    },
    [onEdgesChangeInternal, onEdgesChange]
  );

  const onConnect = useCallback(
    (params: Connection) => {
      setEdges((eds) => addEdge({ ...params, animated: true }, eds));
      // Update parent
      setTimeout(() => {
        setEdges((eds) => {
          onEdgesChange(eds);
          return eds;
        });
      }, 0);
    },
    [setEdges, onEdgesChange]
  );

  const onNodeClick = useCallback(
    (_event: React.MouseEvent, node: Node) => {
      onNodeSelect(node);
    },
    [onNodeSelect]
  );

  const onPaneClick = useCallback(() => {
    onNodeSelect(null);
  }, [onNodeSelect]);

  const addNode = useCallback(
    (type: string) => {
      const newNode: Node = {
        id: `${type}-${Date.now()}`,
        type,
        position: {
          x: Math.random() * 400 + 100,
          y: Math.random() * 300 + 100,
        },
        data: {
          label:
            type === 'entryPoint'
              ? 'Entry Point'
              : type === 'process'
                ? 'New Process'
                : type === 'decision'
                  ? 'Decision'
                  : type === 'toolCall'
                    ? 'Tool Call'
                    : type === 'router'
                      ? 'Router'
                      : type === 'parallelGateway'
                        ? 'Parallel Gateway'
                        : type === 'human'
                          ? 'Human Input'
                          : type === 'reactAgent'
                            ? 'ReAct Agent'
                            : type === 'deepPlanner'
                              ? 'Task Planner'
                              : type === 'deepExecutor'
                                ? 'Task Executor'
                                : type === 'deepCritic'
                                  ? 'Quality Critic'
                                  : type === 'subAgent'
                                    ? 'Sub-Agent'
                                    : type === 'contextManager'
                                      ? 'Context Manager'
                                      : 'End',
          description: '',
          ...(type === 'process' && {
            model: 'gpt-5-mini',
            temperature: 0.7,
            maxTokens: 1000,
          }),
          ...(type === 'toolCall' && {
            tool: '',
            parameters: {},
          }),
          ...(type === 'decision' && {
            conditions: [],
          }),
          ...(type === 'router' && {
            routing_logic: 'conditional',
            routes: [],
          }),
          ...(type === 'parallelGateway' && {
            branches: [],
            strategy: 'fan_out',
          }),
          ...(type === 'human' && {
            prompt: 'Please provide input...',
            timeout: 3600,
          }),
          ...(type === 'reactAgent' && {
            model: 'gpt-5-mini',
            tools: [],
            max_iterations: 10,
            early_stopping: 'force',
          }),
          ...(type === 'deepPlanner' && {
            strategy: 'hierarchical',
            max_subtasks: 10,
          }),
          ...(type === 'deepExecutor' && {
            model: 'claude-sonnet-4-5-20250929',
            enable_todos: true,
            enable_filesystem: true,
            enable_subagents: false,
            enable_summarization: true,
            max_iterations: 5,
          }),
          ...(type === 'deepCritic' && {
            validation_criteria: ['completeness', 'accuracy', 'clarity'],
            quality_threshold: 0.8,
            auto_replan: true,
          }),
          ...(type === 'subAgent' && {
            specialization: 'Research',
            tools: [],
            max_depth: 3,
          }),
          ...(type === 'contextManager' && {
            size_threshold: 170000,
            offload_strategy: 'auto',
            auto_summarize: true,
          }),
        },
      };

      setNodes((nds) => [...nds, newNode]);
      onNodesChange([...nodes, newNode]);
    },
    [setNodes, nodes, onNodesChange]
  );

  const handleExportMermaid = useCallback(() => {
    const agentName = 'agent-graph'; // TODO: Get from context/props
    const mermaidMarkdown = exportMermaidDiagram(nodes, edges, agentName, false);

    // Download as .md file
    const blob = new Blob([mermaidMarkdown], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${agentName}-mermaid.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [nodes, edges]);

  return (
    <div className="w-full h-full relative bg-bg-0">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={handleNodesChange}
        onEdgesChange={handleEdgesChange}
        onConnect={onConnect}
        onNodeClick={onNodeClick}
        onPaneClick={onPaneClick}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.4, maxZoom: 0.8 }}
        defaultViewport={{ x: 0, y: 0, zoom: 0.6 }}
        minZoom={0.2}
        maxZoom={2}
        className="bg-bg-0"
      >
        <Background
          variant={BackgroundVariant.Dots}
          gap={20}
          size={1}
          color="#8690A5"
          className="bg-bg-0"
        />
        <Controls className="bg-bg-1 border border-white/10 rounded-lg" />
        <MiniMap
          className="bg-bg-1 border border-white/10 rounded-lg"
          nodeColor={(node) => {
            switch (node.type) {
              case 'entryPoint':
                return '#10b981';
              case 'process':
                return '#1E67FF';
              case 'decision':
                return '#f59e0b';
              case 'toolCall':
                return '#8b5cf6';
              case 'end':
                return '#ef4444';
              default:
                return '#8690A5';
            }
          }}
        />

        {/* Add Node Panel */}
        <Panel
          position="top-left"
          className="bg-bg-1 border border-white/10 rounded-lg p-2 shadow-lg"
        >
          <div className="flex flex-col gap-1.5">
            <div className="text-xs font-semibold text-fg-1 px-2 mb-1">
              Add Node
            </div>

            {/* Core Nodes - Only showing working node types */}
            <Button
              size="sm"
              variant="outline"
              onClick={() => addNode('entryPoint')}
              className="justify-start border-white/10 hover:bg-green-600/10"
            >
              <Circle className="w-4 h-4 mr-2 text-green-500" />
              <span className="text-fg-1">Entry Point</span>
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => addNode('process')}
              className="justify-start border-white/10 hover:bg-blue-600/10"
            >
              <Square className="w-4 h-4 mr-2 text-blue-500" />
              <span className="text-fg-1">Process (LLM)</span>
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => addNode('human')}
              className="justify-start border-white/10 hover:bg-cyan-600/10"
            >
              <User className="w-4 h-4 mr-2 text-cyan-500" />
              <span className="text-fg-1">Interrupt</span>
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => addNode('end')}
              className="justify-start border-white/10 hover:bg-red-600/10"
            >
              <Circle className="w-4 h-4 mr-2 text-red-500" />
              <span className="text-fg-1">End</span>
            </Button>
          </div>
        </Panel>

        {/* Export Panel */}
        <Panel
          position="top-right"
          className="bg-bg-1 border border-white/10 rounded-lg p-2 shadow-lg"
        >
          <div className="flex flex-col gap-1.5">
            <div className="text-xs font-semibold text-fg-1 px-2 mb-1">Export</div>

            <Button
              size="sm"
              variant="outline"
              onClick={handleExportMermaid}
              className="justify-start border-white/10 hover:bg-blue-600/10"
              title="Export graph as Mermaid flowchart diagram"
            >
              <GitGraph className="w-4 h-4 mr-2 text-blue-500" />
              <span className="text-fg-1">Mermaid</span>
            </Button>
          </div>
        </Panel>
      </ReactFlow>
    </div>
  );
}
