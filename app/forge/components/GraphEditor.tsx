'use client';

import { useCallback, useMemo } from 'react';
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
import { Button } from '@/components/ui/button';
import { Plus, Circle, GitBranch, Wrench, Square } from 'lucide-react';

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

  // Sync internal state with props
  const handleNodesChange = useCallback((changes: any) => {
    onNodesChangeInternal(changes);
    // Update parent
    setTimeout(() => {
      setNodes((nds) => {
        onNodesChange(nds);
        return nds;
      });
    }, 0);
  }, [onNodesChangeInternal, onNodesChange]);

  const handleEdgesChange = useCallback((changes: any) => {
    onEdgesChangeInternal(changes);
    // Update parent
    setTimeout(() => {
      setEdges((eds) => {
        onEdgesChange(eds);
        return eds;
      });
    }, 0);
  }, [onEdgesChangeInternal, onEdgesChange]);

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
          label: type === 'entryPoint' ? 'Entry Point' :
                 type === 'process' ? 'New Process' :
                 type === 'decision' ? 'Decision' :
                 type === 'toolCall' ? 'Tool Call' :
                 'End',
          description: '',
          ...(type === 'process' && {
            model: 'gpt-4o-mini',
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
        },
      };

      setNodes((nds) => [...nds, newNode]);
      onNodesChange([...nodes, newNode]);
    },
    [setNodes, nodes, onNodesChange]
  );

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
              case 'entryPoint': return '#10b981';
              case 'process': return '#1E67FF';
              case 'decision': return '#f59e0b';
              case 'toolCall': return '#8b5cf6';
              case 'end': return '#ef4444';
              default: return '#8690A5';
            }
          }}
        />

        {/* Add Node Panel */}
        <Panel position="top-left" className="bg-bg-1 border border-white/10 rounded-lg p-2">
          <div className="flex flex-col gap-2">
            <div className="text-xs font-medium text-fg-2 px-2 mb-1">Add Node</div>
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
              <span className="text-fg-1">Process</span>
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => addNode('decision')}
              className="justify-start border-white/10 hover:bg-yellow-600/10"
            >
              <GitBranch className="w-4 h-4 mr-2 text-yellow-500" />
              <span className="text-fg-1">Decision</span>
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => addNode('toolCall')}
              className="justify-start border-white/10 hover:bg-purple-600/10"
            >
              <Wrench className="w-4 h-4 mr-2 text-purple-500" />
              <span className="text-fg-1">Tool Call</span>
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
      </ReactFlow>
    </div>
  );
}
