'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import {
  Save,
  Undo,
  Redo,
  Maximize2,
  Minimize2,
  Database,
  Zap,
  Settings,
  ChevronLeft,
  Rocket,
} from 'lucide-react';
import { toast } from 'sonner';
import GraphTypeSelector, { GraphType } from './components/GraphTypeSelector';
import GraphGallery from './components/GraphGallery';
import { GraphEditor } from '@/app/forge/components/GraphEditor';
import { NodeEditor } from '@/app/forge/components/NodeEditor';
import { StateSchemaModal } from './components/StateSchemaModal';
import { useGraphCodeStore } from '@/lib/stores/graphCode.store';
import { graphToPython, validatePython } from '@/app/forge/lib/graph-to-python';
import { TriggerModal } from './components/TriggerModal';
import { ConfirmDialog } from '@/components/ui/confirm-dialog';
import {
  convertLangGraphToReactFlow,
  isLangGraphFormat,
  isReactFlowFormat,
} from './utils/format-converter';
import { useGraphTabs } from './context/GraphTabsContext';

interface Graph {
  id: string;
  name: string;
  display_name: string;
  description?: string;
  graph_type: GraphType;
  channel?: string;
  organization_id?: string;
  domain_id?: string;
  version: string;
  status: string;
  updated_at: string;
  yaml_content?: string;
}

interface Node {
  id: string;
  type: string;
  position: { x: number; y: number };
  data: any;
}

interface Edge {
  id: string;
  source: string;
  target: string;
  sourceHandle?: string;
  targetHandle?: string;
}

export default function UnifiedGraphsPage() {
  const router = useRouter();
  const { openTab } = useGraphTabs();
  const { setGraphData, setCode, clear: clearGraphCode } = useGraphCodeStore();

  // View state
  const [viewMode, setViewMode] = useState<'gallery' | 'editor'>('gallery');
  const [graphType, setGraphType] = useState<GraphType>('user');
  const [selectedChannel, setSelectedChannel] = useState<string>('chat');

  // Gallery state
  const [graphs, setGraphs] = useState<Graph[]>([]);
  const [graphCounts, setGraphCounts] = useState({ user: 0, channel: 0, system: 0 });
  const [loading, setLoading] = useState(true);

  // Editor state
  const [currentGraph, setCurrentGraph] = useState<Graph | null>(null);
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  // History state
  const [history, setHistory] = useState<Array<{ nodes: Node[]; edges: Edge[] }>>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);

  // UI state
  const [isMaximized, setIsMaximized] = useState(false);
  const [showStateModal, setShowStateModal] = useState(false);
  const [showTriggerModal, setShowTriggerModal] = useState(false);
  const [selectedStateSchema, setSelectedStateSchema] = useState<string | null>(null);
  const [selectedTriggers, setSelectedTriggers] = useState<string[]>([]);

  // State schemas and triggers data
  const [stateSchemas, setStateSchemas] = useState<any[]>([]);
  const [triggers, setTriggers] = useState<any[]>([]);

  // Confirmation dialog state
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [graphToDelete, setGraphToDelete] = useState<Graph | null>(null);
  const [unsavedChangesDialogOpen, setUnsavedChangesDialogOpen] = useState(false);

  // Load graphs on mount and when type changes
  useEffect(() => {
    loadGraphs();
    loadStateSchemas();
    loadTriggers();
  }, [graphType, selectedChannel]);

  // Update the graph code store when nodes/edges change (for the Code tab in BottomPanel)
  useEffect(() => {
    if (viewMode === 'editor' && currentGraph) {
      const agentName = currentGraph.name || 'agent-preview';
      setGraphData(nodes, edges, agentName);

      // Generate Python code and validate
      const pythonCode = graphToPython(nodes, edges, agentName, {
        stateSchema: null,
        triggers: [],
      });
      const validation = validatePython(pythonCode);
      setCode(pythonCode, validation.valid, validation.errors);
    } else {
      clearGraphCode();
    }
  }, [nodes, edges, currentGraph, viewMode, setGraphData, setCode, clearGraphCode]);

  // Clear graph code when leaving the page
  useEffect(() => {
    return () => {
      clearGraphCode();
    };
  }, [clearGraphCode]);

  const loadGraphs = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        environment: 'dev',
      });

      if (graphType) {
        params.append('graph_type', graphType);
      }
      if (graphType === 'channel' && selectedChannel) {
        params.append('channel', selectedChannel);
      }

      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/graphs?${params}`);
      const data = await res.json();

      setGraphs(data.graphs || []);

      // Update counts
      const userCount = data.graphs.filter((g: Graph) => g.graph_type === 'user').length;
      const channelCount = data.graphs.filter((g: Graph) => g.graph_type === 'channel').length;
      const systemCount = data.graphs.filter((g: Graph) => g.graph_type === 'system').length;
      setGraphCounts({ user: userCount, channel: channelCount, system: systemCount });
    } catch (error) {
      console.error('Failed to load graphs:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadStateSchemas = async () => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/forge/state-schemas`);
      const data = await res.json();
      setStateSchemas(data.schemas || []);
    } catch (error) {
      console.error('Failed to load state schemas:', error);
    }
  };

  const loadTriggers = async () => {
    try {
      const params = new URLSearchParams();
      if (graphType === 'channel' && selectedChannel) {
        params.append('channel', selectedChannel);
      }
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/forge/triggers?${params}`);
      const data = await res.json();
      setTriggers(data.triggers || []);
    } catch (error) {
      console.error('Failed to load triggers:', error);
    }
  };

  // State schema handlers
  const handleSaveSchema = async (schema: any) => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/forge/state-schemas`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(schema),
      });

      if (!res.ok) {
        const errorText = await res.text();
        console.error('Failed to save state schema:', errorText);
        throw new Error(`Failed to save state schema: ${res.statusText}`);
      }

      await loadStateSchemas();
    } catch (error) {
      console.error('Failed to save state schema:', error);
      throw error;
    }
  };

  const handleDeleteSchema = async (schemaId: string) => {
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/forge/state-schemas/${schemaId}`,
        { method: 'DELETE' }
      );

      if (!res.ok) {
        throw new Error('Failed to delete state schema');
      }

      await loadStateSchemas();
      if (selectedStateSchema === schemaId) {
        setSelectedStateSchema(null);
      }
    } catch (error) {
      console.error('Failed to delete state schema:', error);
      throw error;
    }
  };

  // Trigger handlers
  const handleSaveTrigger = async (trigger: any) => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/forge/triggers`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(trigger),
      });

      if (!res.ok) {
        const errorText = await res.text();
        console.error('Failed to save trigger:', errorText);
        throw new Error(`Failed to save trigger: ${res.statusText}`);
      }

      await loadTriggers();
    } catch (error) {
      console.error('Failed to save trigger:', error);
      throw error;
    }
  };

  const handleDeleteTrigger = async (triggerId: string) => {
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/forge/triggers/${triggerId}`,
        { method: 'DELETE' }
      );

      if (!res.ok) {
        throw new Error('Failed to delete trigger');
      }

      await loadTriggers();
      setSelectedTriggers((prev) => prev.filter((id) => id !== triggerId));
    } catch (error) {
      console.error('Failed to delete trigger:', error);
      throw error;
    }
  };

  // History management
  const addToHistory = useCallback(
    (newNodes: Node[], newEdges: Edge[]) => {
      setHistory((prev) => {
        const newHistory = prev.slice(0, historyIndex + 1);
        newHistory.push({ nodes: newNodes, edges: newEdges });
        return newHistory.slice(-50); // Keep last 50 states
      });
      setHistoryIndex((prev) => Math.min(prev + 1, 49));
      setHasUnsavedChanges(true);
    },
    [historyIndex]
  );

  const handleUndo = () => {
    if (historyIndex > 0) {
      const prevState = history[historyIndex - 1];
      setNodes(prevState.nodes);
      setEdges(prevState.edges);
      setHistoryIndex(historyIndex - 1);
      setHasUnsavedChanges(true);
    }
  };

  const handleRedo = () => {
    if (historyIndex < history.length - 1) {
      const nextState = history[historyIndex + 1];
      setNodes(nextState.nodes);
      setEdges(nextState.edges);
      setHistoryIndex(historyIndex + 1);
      setHasUnsavedChanges(true);
    }
  };

  // Graph actions
  const handleNewGraph = () => {
    // Navigate to graph editor with a new draft ID
    const draftId = `draft_${Date.now()}`;
    const draftName = `New Graph`;

    // Register the new tab before navigating
    openTab({
      id: draftId,
      name: draftName,
      displayName: draftName,
      description: 'New agent created in visual designer',
      nodes: [],
      edges: [],
      isDraft: true,
      canonicalId: null,
      stateSchemaId: null,
      triggerIds: [],
    });

    router.push(
      `/app/graphs/${draftId}?type=${graphType}${graphType === 'channel' ? `&channel=${selectedChannel}` : ''}`
    );
  };

  const handleOpenGraph = async (graph: Graph) => {
    // Register the tab before navigating
    openTab({
      id: graph.id,
      name: graph.name,
      displayName: graph.display_name || graph.name,
      description: graph.description,
      nodes: [], // Will be loaded by the graph page
      edges: [], // Will be loaded by the graph page
      isDraft: false,
      canonicalId: graph.id,
      stateSchemaId: null,
      triggerIds: [],
    });

    // Navigate to the dedicated graph editor page using the graph UUID
    router.push(`/app/graphs/${graph.id}`);
  };

  const handleSaveGraph = async () => {
    if (!currentGraph) return;

    try {
      const graphData = {
        metadata: {
          id: currentGraph.id.startsWith('draft_') ? undefined : currentGraph.id,
          name: currentGraph.name,
          display_name: currentGraph.display_name,
          description: currentGraph.description,
          type: currentGraph.graph_type,
          channel: currentGraph.channel,
          organization_id: currentGraph.organization_id || 'cibc',
          domain_id: currentGraph.domain_id || 'card-services',
          version: currentGraph.version,
          status: currentGraph.status,
        },
        spec: {
          state_schema_id: selectedStateSchema,
          triggers: selectedTriggers,
          graph: {
            nodes,
            edges,
          },
        },
      };

      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/graphs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(graphData),
      });

      if (!res.ok) {
        throw new Error('Failed to save graph');
      }

      const savedGraph = await res.json();
      setCurrentGraph(savedGraph);
      setHasUnsavedChanges(false);
      toast.success('Graph saved successfully');
      await loadGraphs();
    } catch (error) {
      console.error('Failed to save graph:', error);
      toast.error('Failed to save graph');
    }
  };

  const handleDeployGraph = async () => {
    if (!currentGraph) return;

    // Check if graph is saved
    if (currentGraph.id.startsWith('draft_') || hasUnsavedChanges) {
      toast.warning('Please save the graph before deploying');
      return;
    }

    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/graphs/${currentGraph.id}/deploy`,
        { method: 'POST' }
      );

      if (!res.ok) {
        throw new Error('Failed to deploy graph');
      }

      const result = await res.json();
      toast.success(`Agent "${currentGraph.name}" deployed successfully`);
      console.log('Deployment result:', result);
    } catch (error) {
      console.error('Failed to deploy graph:', error);
      toast.error('Failed to deploy graph');
    }
  };

  const handleDuplicateGraph = async (graph: Graph) => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/graphs/${graph.id}`);
      const fullGraph = await res.json();

      const duplicateData = {
        ...JSON.parse(fullGraph.yaml_content || '{}'),
        metadata: {
          ...JSON.parse(fullGraph.yaml_content || '{}').metadata,
          id: undefined,
          name: `${graph.name} (Copy)`,
          display_name: `${graph.display_name} (Copy)`,
        },
      };

      const saveRes = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/graphs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(duplicateData),
      });

      if (!saveRes.ok) {
        throw new Error('Failed to duplicate graph');
      }

      toast.success('Graph duplicated successfully');
      await loadGraphs();
    } catch (error) {
      console.error('Failed to duplicate graph:', error);
      toast.error('Failed to duplicate graph');
    }
  };

  const handleDeleteGraph = (graph: Graph) => {
    setGraphToDelete(graph);
    setDeleteDialogOpen(true);
  };

  const confirmDeleteGraph = async () => {
    if (!graphToDelete) return;

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/graphs/${graphToDelete.id}`, {
        method: 'DELETE',
      });

      if (!res.ok) {
        throw new Error('Failed to delete graph');
      }

      toast.success('Graph deleted successfully');
      await loadGraphs();
    } catch (error) {
      console.error('Failed to delete graph:', error);
      toast.error('Failed to delete graph');
    } finally {
      setGraphToDelete(null);
    }
  };

  const handleBackToGallery = () => {
    if (hasUnsavedChanges) {
      setUnsavedChangesDialogOpen(true);
      return;
    }
    navigateToGallery();
  };

  const navigateToGallery = () => {
    setViewMode('gallery');
    setCurrentGraph(null);
    setNodes([]);
    setEdges([]);
    setHasUnsavedChanges(false);
  };

  // Node selection
  const handleNodeClick = (node: Node) => {
    setSelectedNode(node);
  };

  const handleNodeUpdate = (updatedNode: Node) => {
    const newNodes = nodes.map((n) => (n.id === updatedNode.id ? updatedNode : n));
    setNodes(newNodes);
    addToHistory(newNodes, edges);
  };

  const handleNodesChange = (newNodes: Node[]) => {
    setNodes(newNodes);
    addToHistory(newNodes, edges);
  };

  const handleEdgesChange = (newEdges: Edge[]) => {
    setEdges(newEdges);
    addToHistory(nodes, newEdges);
  };

  return (
    <div className="flex flex-col h-full bg-gray-50 dark:bg-gray-900">
      {/* Top bar - Sticky */}
      <div className="sticky top-0 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-6 py-4 z-20">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Agent Graphs</h1>
        </div>

        {viewMode === 'gallery' ? (
          <GraphTypeSelector
            selectedType={graphType}
            onTypeChange={(type) => setGraphType(type)}
            counts={graphCounts}
          />
        ) : (
          <div className="flex flex-col gap-3">
            {/* Top row - Back button and graph info */}
            <div className="flex items-center gap-4">
              <button
                onClick={handleBackToGallery}
                className="flex items-center gap-2 px-3 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
              >
                <ChevronLeft className="w-4 h-4" />
                Back
              </button>

              {/* Graph Name & Description */}
              <div className="flex-1 flex flex-col gap-1">
                <input
                  type="text"
                  value={currentGraph?.name || ''}
                  onChange={(e) => {
                    if (currentGraph) {
                      setCurrentGraph({
                        ...currentGraph,
                        name: e.target.value,
                        display_name: e.target.value,
                      });
                      setHasUnsavedChanges(true);
                    }
                  }}
                  placeholder="Enter graph name..."
                  className="px-3 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-base font-semibold text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <input
                  type="text"
                  value={currentGraph?.description || ''}
                  onChange={(e) => {
                    if (currentGraph) {
                      setCurrentGraph({
                        ...currentGraph,
                        description: e.target.value,
                      });
                      setHasUnsavedChanges(true);
                    }
                  }}
                  placeholder="Description (optional)"
                  className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-sm text-gray-600 dark:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* Bottom row - Toolbar */}
            <div className="flex items-center justify-end gap-2">
              {graphType === 'channel' && (
                <select
                  value={selectedChannel}
                  onChange={(e) => setSelectedChannel(e.target.value)}
                  className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-sm"
                >
                  <option value="chat">Chat</option>
                  <option value="voice">Voice</option>
                  <option value="api">API</option>
                </select>
              )}

              <button
                onClick={handleUndo}
                disabled={historyIndex <= 0}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded disabled:opacity-50"
                title="Undo"
              >
                <Undo className="w-4 h-4" />
              </button>

              <button
                onClick={handleRedo}
                disabled={historyIndex >= history.length - 1}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded disabled:opacity-50"
                title="Redo"
              >
                <Redo className="w-4 h-4" />
              </button>

              <button
                onClick={() => setShowStateModal(true)}
                className="flex items-center gap-2 px-3 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded text-sm"
                title="State Schema"
              >
                <Database className="w-4 h-4" />
                State
              </button>

              <button
                onClick={() => setShowTriggerModal(true)}
                className="flex items-center gap-2 px-3 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded text-sm"
                title="Triggers"
              >
                <Zap className="w-4 h-4" />
                Triggers
              </button>

              <button
                onClick={handleSaveGraph}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium"
              >
                <Save className="w-4 h-4" />
                Save
              </button>

              <button
                onClick={handleDeployGraph}
                disabled={
                  !currentGraph || currentGraph.id.startsWith('draft_') || hasUnsavedChanges
                }
                className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                title={hasUnsavedChanges ? 'Save before deploying' : 'Deploy agent'}
              >
                <Rocket className="w-4 h-4" />
                Deploy
              </button>

              <button
                onClick={() => setIsMaximized(!isMaximized)}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                title={isMaximized ? 'Minimize' : 'Maximize'}
              >
                {isMaximized ? (
                  <Minimize2 className="w-4 h-4" />
                ) : (
                  <Maximize2 className="w-4 h-4" />
                )}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Main content */}
      <div className="flex-1 overflow-hidden">
        {viewMode === 'gallery' ? (
          <div className="p-6 h-full overflow-auto">
            {loading ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-gray-500">Loading graphs...</div>
              </div>
            ) : (
              <GraphGallery
                graphs={graphs}
                selectedType={graphType}
                onOpenGraph={handleOpenGraph}
                onNewGraph={handleNewGraph}
                onDuplicateGraph={handleDuplicateGraph}
                onDeleteGraph={handleDeleteGraph}
              />
            )}
          </div>
        ) : (
          <div className="flex h-full">
            {/* Graph editor */}
            <div className={`flex-1 ${selectedNode ? 'mr-80' : ''} relative`}>
              <GraphEditor
                nodes={nodes}
                edges={edges}
                onNodesChange={handleNodesChange}
                onEdgesChange={handleEdgesChange}
                onNodeSelect={handleNodeClick}
              />
            </div>

            {/* Node editor sidebar */}
            {selectedNode && (
              <div className="w-80 border-l border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 overflow-auto">
                <NodeEditor
                  node={selectedNode}
                  triggers={triggers}
                  onNodeUpdate={handleNodeUpdate}
                  onClose={() => setSelectedNode(null)}
                  onNodeDelete={(nodeId) => {
                    const newNodes = nodes.filter((n) => n.id !== nodeId);
                    const newEdges = edges.filter(
                      (e) => e.source !== nodeId && e.target !== nodeId
                    );
                    setNodes(newNodes);
                    setEdges(newEdges);
                    addToHistory(newNodes, newEdges);
                    setSelectedNode(null);
                  }}
                />
              </div>
            )}
          </div>
        )}
      </div>

      {/* State Schema Modal */}
      <StateSchemaModal
        open={showStateModal}
        onOpenChange={setShowStateModal}
        schemas={stateSchemas}
        activeSchemaId={selectedStateSchema}
        onSelectSchema={(id) => {
          setSelectedStateSchema(id);
          setHasUnsavedChanges(true);
        }}
        onSaveSchema={handleSaveSchema}
        onDeleteSchema={handleDeleteSchema}
      />

      {/* Trigger Modal */}
      <TriggerModal
        open={showTriggerModal}
        onOpenChange={setShowTriggerModal}
        triggers={triggers}
        selectedTriggerIds={selectedTriggers}
        onToggleTrigger={(triggerId, selected) => {
          setSelectedTriggers((prev) =>
            selected ? [...prev, triggerId] : prev.filter((id) => id !== triggerId)
          );
          setHasUnsavedChanges(true);
        }}
        onSaveTrigger={handleSaveTrigger}
        onDeleteTrigger={handleDeleteTrigger}
      />

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        open={deleteDialogOpen}
        onOpenChange={setDeleteDialogOpen}
        title="Delete Graph"
        description={`Are you sure you want to delete "${graphToDelete?.display_name}"? This action cannot be undone.`}
        confirmLabel="Delete"
        cancelLabel="Cancel"
        variant="destructive"
        onConfirm={confirmDeleteGraph}
        onCancel={() => setGraphToDelete(null)}
      />

      {/* Unsaved Changes Confirmation Dialog */}
      <ConfirmDialog
        open={unsavedChangesDialogOpen}
        onOpenChange={setUnsavedChangesDialogOpen}
        title="Unsaved Changes"
        description="You have unsaved changes. Are you sure you want to leave? Your changes will be lost."
        confirmLabel="Leave"
        cancelLabel="Stay"
        variant="destructive"
        onConfirm={navigateToGallery}
      />
    </div>
  );
}
