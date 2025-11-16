'use client';

import { useState, useEffect, useMemo, useCallback } from 'react';
import { GraphEditor } from './components/GraphEditor';
import { NodeEditor } from './components/NodeEditor';
import { YAMLPreview } from './components/YAMLPreview';
import { AgentOpenDialog } from './components/AgentOpenDialog';
import { AgentPropertiesDialog, type AgentMetadata } from './components/AgentPropertiesDialog';
import { VersionSelector, type DeploymentVersion } from './components/VersionSelector';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import {
  Save,
  FolderOpen,
  AlertCircle,
  Rocket,
  FilePlus,
  Undo2,
  Redo2,
} from 'lucide-react';
import { LoadingState, EmptyState } from '@/components/shared';
import { Toolbar, type ToolbarAction } from '@/components/layout/Toolbar';
import { mockAgents } from '@/lib/mocks/agents.mock';
import type { Agent } from '@/types';
import type { Node, Edge } from 'reactflow';

interface HistoryState {
  nodes: Node[]
  edges: Edge[]
}

export default function ForgePage() {
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [agentName, setAgentName] = useState('untitled-agent');
  const [isSaving, setIsSaving] = useState(false);
  const [isDeploying, setIsDeploying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [openDialogOpen, setOpenDialogOpen] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [currentVersion, setCurrentVersion] = useState('v1.0.0');

  // Agent metadata and properties
  const [agentMetadata, setAgentMetadata] = useState<AgentMetadata>({
    name: 'untitled-agent',
    description: '',
    version: '1.0.0',
    tags: [],
  });
  const [propertiesDialogOpen, setPropertiesDialogOpen] = useState(false);
  const [propertiesDialogMode, setPropertiesDialogMode] = useState<'new' | 'edit'>('new');
  const [isAgentInitialized, setIsAgentInitialized] = useState(false);

  // Undo/Redo state
  const [history, setHistory] = useState<HistoryState[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const [isUndoRedoing, setIsUndoRedoing] = useState(false);

  // Mock deployment versions - in a real app, this would come from an API
  const deploymentVersions: DeploymentVersion[] = [
    {
      version: 'v1.0.0',
      deployedBy: 'John Doe',
      deployedAt: new Date().toISOString(),
      environment: 'prod',
      commitHash: 'a1b2c3d',
      isCurrent: true,
    },
    {
      version: 'v0.9.5',
      deployedBy: 'Jane Smith',
      deployedAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      environment: 'prod',
      commitHash: 'e4f5g6h',
    },
    {
      version: 'v0.9.4',
      deployedBy: 'John Doe',
      deployedAt: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
      environment: 'staging',
      commitHash: 'i7j8k9l',
    },
    {
      version: 'v0.9.3',
      deployedBy: 'Alice Johnson',
      deployedAt: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
      environment: 'dev',
      commitHash: 'm0n1o2p',
    },
  ];

  // Add to history when nodes or edges change
  const addToHistory = useCallback(() => {
    if (isUndoRedoing) return;

    const newState: HistoryState = { nodes, edges };
    const newHistory = history.slice(0, historyIndex + 1);
    newHistory.push(newState);

    // Limit history to 50 states
    if (newHistory.length > 50) {
      newHistory.shift();
    } else {
      setHistoryIndex(historyIndex + 1);
    }

    setHistory(newHistory);
  }, [nodes, edges, history, historyIndex, isUndoRedoing]);

  // Track changes to nodes/edges for unsaved changes
  useEffect(() => {
    if (nodes.length > 0 || edges.length > 0) {
      setHasUnsavedChanges(true);
    }
  }, [nodes, edges]);

  const handleNew = () => {
    if (hasUnsavedChanges) {
      if (!confirm('You have unsaved changes. Are you sure you want to create a new agent?')) {
        return;
      }
    }
    // Open properties dialog for new agent
    setPropertiesDialogMode('new');
    setAgentMetadata({
      name: 'untitled-agent',
      description: '',
      version: '1.0.0',
      tags: [],
    });
    setPropertiesDialogOpen(true);
  };

  const handleSaveMetadata = (metadata: AgentMetadata) => {
    setAgentMetadata(metadata);
    setAgentName(metadata.name);
    setNodes([]);
    setEdges([]);
    setSelectedAgent(null);
    setHistory([]);
    setHistoryIndex(-1);
    setHasUnsavedChanges(false);
    setIsAgentInitialized(true);
    setSuccessMessage(`Ready to build "${metadata.name}"`);
  };

  const handleOpen = () => {
    setOpenDialogOpen(true);
  };

  const handleSave = async () => {
    setIsSaving(true);
    setError(null);
    setSuccessMessage(null);
    try {
      const { registerAgentInManifest } = await import('./lib/manifest-api');

      const environment = (localStorage.getItem('selectedInstance') || 'dev') as 'dev' | 'staging' | 'prod';

      // TODO: make org/domain/instance dynamic – for now, we target CIBC / Card Services / dev
      await registerAgentInManifest({
        agentId: agentName,
        nodes,
        edges,
        organizationId: 'cibc',
        organizationName: 'CIBC',
        domainId: 'card-services',
        domainName: 'Card Services',
        environment,
        instanceId: 'dev',
        author: 'foundry-user',
        tags: [],
        isSystemAgent: false,
      });

      setSuccessMessage('Agent saved successfully');
      setHasUnsavedChanges(false);
    } catch (error) {
      console.error('Failed to save:', error);
      setError(`Failed to save agent: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsSaving(false);
    }
  };

  const handleSaveAs = async () => {
    const newName = prompt('Enter a name for the new agent:', `${agentName}-copy`);
    if (!newName) return;

    setIsSaving(true);
    setError(null);
    setSuccessMessage(null);
    try {
      const { registerAgentInManifest } = await import('./lib/manifest-api');
      const environment = (localStorage.getItem('selectedInstance') || 'dev') as 'dev' | 'staging' | 'prod';

      await registerAgentInManifest({
        agentId: newName,
        nodes,
        edges,
        organizationId: 'cibc',
        organizationName: 'CIBC',
        domainId: 'card-services',
        domainName: 'Card Services',
        environment,
        instanceId: 'dev',
        author: 'foundry-user',
        tags: [],
        isSystemAgent: false,
      });

      setAgentName(newName);
      setSuccessMessage(`Agent saved as "${newName}"`);
      setHasUnsavedChanges(false);
    } catch (error) {
      console.error('Failed to save as:', error);
      setError(`Failed to save agent: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsSaving(false);
    }
  };

  const handleUndo = () => {
    if (historyIndex > 0) {
      setIsUndoRedoing(true);
      const newIndex = historyIndex - 1;
      const state = history[newIndex];
      setNodes(state.nodes);
      setEdges(state.edges);
      setHistoryIndex(newIndex);
      setTimeout(() => setIsUndoRedoing(false), 100);
    }
  };

  const handleRedo = () => {
    if (historyIndex < history.length - 1) {
      setIsUndoRedoing(true);
      const newIndex = historyIndex + 1;
      const state = history[newIndex];
      setNodes(state.nodes);
      setEdges(state.edges);
      setHistoryIndex(newIndex);
      setTimeout(() => setIsUndoRedoing(false), 100);
    }
  };

  const handleDeploy = async () => {
    // Save first if there are unsaved changes
    if (hasUnsavedChanges) {
      await handleSave();
    }

    setIsDeploying(true);
    setError(null);
    setSuccessMessage(null);
    try {
      const { forgeAPI } = await import('./lib/forge-api');

      // Get environment from localStorage or use 'dev' as default
      const environment = (localStorage.getItem('selectedInstance') || 'dev') as 'dev' | 'staging' | 'prod';

      const deployment = await forgeAPI.deployAgent(agentName, {
        environment,
        git_commit: false, // TODO: Add UI option for Git commit
      });

      setSuccessMessage(`Agent deployed to ${environment} successfully!`);
    } catch (error) {
      console.error('Failed to deploy:', error);
      setError(`Failed to deploy agent: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsDeploying(false);
    }
  };

  const handleLoadAgent = async (agent: Agent) => {
    setIsLoading(true);
    setError(null);
    setSuccessMessage(null);
    try {
      const { forgeAPI } = await import('./lib/forge-api');
      const { yamlToGraph, autoLayoutNodes } = await import('./lib/yaml-to-graph');

      const agentData = await forgeAPI.getAgent(agent.name);

      // Convert YAML to graph
      const yaml = await import('js-yaml');
      const yamlString = yaml.dump(agentData);
      const result = yamlToGraph(yamlString);

      if (result.error) {
        setError(`Failed to load agent: ${result.error}`);
        return;
      }

      // Auto-layout nodes
      const layoutedNodes = autoLayoutNodes(result.nodes, result.edges);

      setNodes(layoutedNodes);
      setEdges(result.edges);
      setAgentName(result.agentName);
      setSelectedAgent(agent);
      setHasUnsavedChanges(false);
      setIsAgentInitialized(true);
      setHistory([{ nodes: layoutedNodes, edges: result.edges }]);
      setHistoryIndex(0);

      setSuccessMessage(`Loaded agent: ${result.agentName}`);
    } catch (error) {
      console.error('Failed to load agent:', error);
      setError(`Failed to load agent: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectVersion = (version: DeploymentVersion) => {
    // TODO: Load the selected version
    console.log('Loading version:', version);
    setCurrentVersion(version.version);
  };

  // Define toolbar actions - left side
  const forgeActions: ToolbarAction[] = useMemo(() => [
    {
      icon: FilePlus,
      label: 'New',
      onClick: handleNew,
      variant: 'ghost',
      tooltip: 'Create a new agent',
    },
    {
      icon: FolderOpen,
      label: 'Open',
      onClick: handleOpen,
      variant: 'ghost',
      tooltip: 'Open an existing agent',
    },
    {
      icon: Save,
      label: 'Save',
      onClick: handleSave,
      disabled: isSaving || !hasUnsavedChanges,
      variant: 'ghost',
      tooltip: isSaving ? 'Saving...' : hasUnsavedChanges ? 'Save agent' : 'No changes to save',
    },
    {
      icon: Save,
      label: 'Save As',
      onClick: handleSaveAs,
      disabled: isSaving || nodes.length === 0,
      variant: 'ghost',
      tooltip: 'Save agent with a new name',
    },
    {
      icon: Undo2,
      label: 'Undo',
      onClick: handleUndo,
      disabled: historyIndex <= 0,
      variant: 'ghost',
      tooltip: 'Undo last change',
    },
    {
      icon: Redo2,
      label: 'Redo',
      onClick: handleRedo,
      disabled: historyIndex >= history.length - 1,
      variant: 'ghost',
      tooltip: 'Redo last change',
    },
  ], [isSaving, nodes.length, hasUnsavedChanges, historyIndex, history.length]);

  // Define toolbar actions - right side (Deploy)
  const forgeRightActions: ToolbarAction[] = useMemo(() => [
    {
      icon: Rocket,
      label: 'Deploy',
      onClick: handleDeploy,
      disabled: isDeploying || nodes.length === 0,
      variant: 'default',
      tooltip: isDeploying ? 'Deploying...' : 'Deploy agent to environment',
    },
  ], [isDeploying, nodes.length]);

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar with custom Deploy section */}
      <div className="h-12 bg-bg-0 border-b border-white/10 flex items-center px-6 gap-4">
        {/* Left Actions */}
        <Toolbar actions={forgeActions} className="border-0 h-auto bg-transparent px-0" />

        {/* Spacer */}
        <div className="flex-1" />

        {/* Right Actions: Version Selector + Deploy */}
        <div className="flex items-center gap-2">
          <div className="h-6 w-px bg-white/20" />
          <VersionSelector
            currentVersion={currentVersion}
            versions={deploymentVersions}
            onSelectVersion={handleSelectVersion}
            disabled={nodes.length === 0}
          />
          <Toolbar rightActions={forgeRightActions} className="border-0 h-auto bg-transparent px-0" />
        </div>
      </div>

      {/* Agent Open Dialog */}
      <AgentOpenDialog
        open={openDialogOpen}
        onOpenChange={setOpenDialogOpen}
        agents={mockAgents}
        onSelectAgent={handleLoadAgent}
        currentAgentId={selectedAgent?.id}
      />

      {/* Agent Properties Dialog */}
      <AgentPropertiesDialog
        open={propertiesDialogOpen}
        onOpenChange={setPropertiesDialogOpen}
        metadata={agentMetadata}
        onSave={handleSaveMetadata}
        mode={propertiesDialogMode}
      />

      {/* Status Messages */}
      {error && (
        <div className="bg-red-500/10 border-b border-red-500/20 px-8 py-3">
          <div className="flex items-center gap-2 text-sm text-red-500">
            <AlertCircle className="w-4 h-4" />
            {error}
          </div>
        </div>
      )}
      {successMessage && (
        <div className="bg-green-500/10 border-b border-green-500/20 px-8 py-3">
          <div className="flex items-center gap-2 text-sm text-green-500">
            <AlertCircle className="w-4 h-4" />
            {successMessage}
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden relative min-h-0">
        {/* Loading Overlay */}
        {isLoading && (
          <div className="absolute inset-0 z-50 bg-bg-0/80 backdrop-blur-sm">
            <LoadingState message="Loading agent..." />
          </div>
        )}

        {/* Empty State */}
        {!isLoading && nodes.length === 0 && !isAgentInitialized && (
          <div className="flex-1 flex items-center justify-center">
            <EmptyState
              title="No workflow nodes"
              description="Open an agent or create a new one to start building."
            />
          </div>
        )}

        {/* Graph Editor - Main Canvas with built-in Add Node panel */}
        {!isLoading && (nodes.length > 0 || isAgentInitialized) && (
          <>
            <div className="flex-1 relative">
              <GraphEditor
                nodes={nodes}
                edges={edges}
                onNodesChange={setNodes}
                onEdgesChange={setEdges}
                onNodeSelect={setSelectedNode}
              />
            </div>

            {/* Right Panel - Node Editor */}
            {selectedNode && (
              <div className="w-80 border-l border-white/10 bg-bg-1 overflow-y-auto">
                <NodeEditor
                  node={selectedNode}
                  onNodeUpdate={(updatedNode) => {
                    setNodes(nodes.map(n => n.id === updatedNode.id ? updatedNode : n));
                    setSelectedNode(updatedNode);
                  }}
                  onClose={() => setSelectedNode(null)}
                />
              </div>
            )}
          </>
        )}
      </div>

      {/* Bottom Panel - YAML Preview */}
      <div className="h-64 border-t border-white/10 bg-bg-1">
        <YAMLPreview nodes={nodes} edges={edges} agentName={agentName} />
      </div>
    </div>
  );
}
