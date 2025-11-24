'use client';

import { useState, useEffect, useMemo, useCallback, use } from 'react';
import { useRouter } from 'next/navigation';
import { GraphEditor } from '../../forge/components/GraphEditor';
import { NodePreviewPanel } from '../../forge/components/NodePreviewPanel';
import { useGraphCodeStore } from '@/lib/stores/graphCode.store';
import { graphToPython, validatePython } from '../../forge/lib/graph-to-python';
import { AgentOpenDialog } from '../../forge/components/AgentOpenDialog';
import {
  AgentPropertiesDialog,
  type AgentMetadata,
} from '../../forge/components/AgentPropertiesDialog';
import { VersionSelector, type DeploymentVersion } from '../../forge/components/VersionSelector';
import {
  StateDesignerPanel,
  type StateSchemaDraft,
} from '../../forge/components/StateDesignerPanel';
import { TriggerRegistryDrawer } from '../../forge/components/TriggerRegistryDrawer';
import { useNavigationGuard } from '@/lib/hooks/useNavigationGuard';
import { useGraphTabs } from '../context/GraphTabsContext';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Save,
  FolderOpen,
  AlertCircle,
  Rocket,
  FilePlus,
  Undo2,
  Redo2,
  Maximize2,
  Minimize2,
  Database,
  Plug,
} from 'lucide-react';
import { ConfirmDialog } from '@/components/ui/confirm-dialog';
import { LoadingState, EmptyState } from '@/components/shared';
import { Toolbar, type ToolbarAction } from '@/components/layout/Toolbar';
import type { Agent } from '@/types';
import type { Node, Edge } from 'reactflow';
import type { StateSchema, TriggerDefinition } from '@/types';
import {
  listStateSchemas,
  saveStateSchema as apiSaveStateSchema,
  deleteStateSchema as apiDeleteStateSchema,
  listTriggers,
  saveTrigger,
  deleteTrigger,
  saveGraphTriggers,
  listGraphTriggers,
} from '../../forge/lib/designer-api';

interface HistoryState {
  nodes: Node[];
  edges: Edge[];
}

export default function GraphPage({ params }: { params: Promise<{ graphId: string }> }) {
  const { graphId } = use(params);
  const router = useRouter();
  const {
    activeTab,
    openTab,
    updateTabNodes,
    updateTabEdges,
    updateTabName,
    markTabSaved,
    markTabLoading,
    updateTabStateSchema,
    updateTabTriggers,
    getTabById,
  } = useGraphTabs();
  const { setGraphData, setCode, clear: clearGraphCode } = useGraphCodeStore();

  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [agentName, setAgentName] = useState(graphId || 'untitled-agent');
  // Track the canonical graph ID separately from the editable name
  // This ensures saves always update the same agent record
  const [canonicalGraphId, setCanonicalGraphId] = useState<string | null>(
    graphId && !graphId.startsWith('draft_') ? graphId : null
  );
  const [isSaving, setIsSaving] = useState(false);
  const [isDeploying, setIsDeploying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [openDialogOpen, setOpenDialogOpen] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [currentVersion, setCurrentVersion] = useState('v1.0.0');

  // Navigation guard - warn before leaving with unsaved changes
  useNavigationGuard({
    when: hasUnsavedChanges,
    message: 'You have unsaved changes in your agent. Are you sure you want to leave?',
  });

  // Agent metadata and properties
  const [agentMetadata, setAgentMetadata] = useState<AgentMetadata>({
    name: 'untitled-agent',
    description: '',
    version: '0.0.1',
    tags: [],
  });
  const [propertiesDialogOpen, setPropertiesDialogOpen] = useState(false);
  const [propertiesDialogMode, setPropertiesDialogMode] = useState<'new' | 'edit'>('new');
  const [isAgentInitialized, setIsAgentInitialized] = useState(false);

  // Deploy confirmation dialog state
  const [showDeployConfirm, setShowDeployConfirm] = useState(false);

  // Full-screen mode state
  const [isMaximized, setIsMaximized] = useState(false);

  // Undo/Redo state
  const [history, setHistory] = useState<HistoryState[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const [isUndoRedoing, setIsUndoRedoing] = useState(false);

  // State schema management
  const [stateSchemas, setStateSchemas] = useState<StateSchema[]>([]);
  const [activeStateSchemaId, setActiveStateSchemaId] = useState<string | null>(null);
  const [isStatePanelOpen, setIsStatePanelOpen] = useState(false);

  // Trigger management
  const [triggers, setTriggers] = useState<TriggerDefinition[]>([]);
  const [selectedTriggerIds, setSelectedTriggerIds] = useState<string[]>([]);
  const [isTriggerDrawerOpen, setIsTriggerDrawerOpen] = useState(false);
  const [isGraphTriggerSyncing, setIsGraphTriggerSyncing] = useState(false);
  const [isDesignerDataLoading, setIsDesignerDataLoading] = useState(false);

  // Available agents for Open dialog
  const [availableAgents, setAvailableAgents] = useState<Agent[]>([]);

  // Selected node for the preview panel
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);

  // Deployment versions (fetched from API)
  const [deploymentVersions, setDeploymentVersions] = useState<DeploymentVersion[]>([]);

  const activeStateSchema = useMemo(
    () => stateSchemas.find((schema) => schema.id === activeStateSchemaId) ?? null,
    [stateSchemas, activeStateSchemaId]
  );

  const selectedTriggersList = useMemo(
    () => triggers.filter((trigger) => trigger.id && selectedTriggerIds.includes(trigger.id)),
    [triggers, selectedTriggerIds]
  );

  const entryNodeId = useMemo(
    () => nodes.find((node) => node.type === 'entryPoint')?.id ?? null,
    [nodes]
  );

  // State for deployed version ID
  const [deployedVersionId, setDeployedVersionId] = useState<string | null>(null);

  // Fetch deployment versions from API
  useEffect(() => {
    const fetchVersions = async () => {
      // Only fetch if we have a canonical graph ID (not a draft)
      const fetchId = canonicalGraphId || (graphId && !graphId.startsWith('draft_') ? graphId : null);
      if (!fetchId) {
        setDeploymentVersions([]);
        return;
      }

      try {
        // Fetch both versions and agent data (to get deployed_version_id)
        const [versionsRes, agentRes] = await Promise.all([
          fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/graphs/${fetchId}/versions`),
          fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/graphs/${fetchId}`),
        ]);

        if (!versionsRes.ok) {
          console.warn('Failed to fetch versions:', versionsRes.statusText);
          setDeploymentVersions([]);
          return;
        }

        const versionsData = await versionsRes.json();
        const agentData = agentRes.ok ? await agentRes.json() : null;
        const currentDeployedVersionId = agentData?.deployed_version_id || null;
        setDeployedVersionId(currentDeployedVersionId);

        // Transform API response to DeploymentVersion format
        const versions: DeploymentVersion[] = (versionsData.versions || []).map((v: any, index: number) => ({
          version: `v${v.version_label || v.version_number || '1.0.0'}`,
          deployedBy: v.created_by || 'Unknown',
          deployedAt: v.created_at || new Date().toISOString(),
          environment: 'dev' as const,
          commitHash: v.id?.substring(0, 7),
          versionId: v.id, // Full version ID for API calls
          isCurrent: index === 0, // First version is the current one
          isDeployed: v.id === currentDeployedVersionId, // Mark if this is the deployed version
        }));

        setDeploymentVersions(versions);

        // Update current version display and metadata
        if (versions.length > 0) {
          const latestVersionLabel = versionsData.versions[0]?.version_label || '0.0.1';
          setCurrentVersion(versions[0].version);
          // Update metadata with the latest version so auto-increment works correctly
          setAgentMetadata((prev) => ({
            ...prev,
            version: latestVersionLabel,
          }));
        }
      } catch (err) {
        console.error('Error fetching versions:', err);
        setDeploymentVersions([]);
      }
    };

    fetchVersions();
  }, [canonicalGraphId, graphId]);

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

  // Track changes to nodes/edges for unsaved changes and sync with tab context
  useEffect(() => {
    if (nodes.length > 0 || edges.length > 0) {
      setHasUnsavedChanges(true);
      // Sync with tab context
      if (graphId) {
        updateTabNodes(graphId, nodes);
      }
    }
  }, [nodes, graphId, updateTabNodes]);

  useEffect(() => {
    if (edges.length > 0 && graphId) {
      updateTabEdges(graphId, edges);
    }
  }, [edges, graphId, updateTabEdges]);

  // Sync graph data to the Code tab in BottomPanel
  useEffect(() => {
    const name = agentMetadata.name || 'agent-preview';
    setGraphData(nodes, edges, name);

    // Generate Python code and validate
    if (nodes.length > 0) {
      const pythonCode = graphToPython(nodes, edges, name, {
        stateSchema: activeStateSchema,
        triggers: selectedTriggersList,
      });
      const validation = validatePython(pythonCode);
      setCode(pythonCode, validation.valid, validation.errors);
    } else {
      setCode('', true, []);
    }
  }, [nodes, edges, agentMetadata.name, activeStateSchema, selectedTriggersList, setGraphData, setCode]);

  // Clear graph code store when unmounting
  useEffect(() => {
    return () => {
      clearGraphCode();
    };
  }, [clearGraphCode]);

  useEffect(() => {
    const loadDesignerData = async () => {
      setIsDesignerDataLoading(true);
      try {
        const [schemasResponse, triggersResponse] = await Promise.all([
          listStateSchemas(),
          listTriggers(),
        ]);
        setStateSchemas(schemasResponse);
        if (!activeStateSchemaId && schemasResponse.length > 0) {
          setActiveStateSchemaId(schemasResponse[0].id);
        }
        setTriggers(triggersResponse);
      } catch (err) {
        console.error('Failed to load designer data', err);
        setError('Failed to load state schemas or triggers');
      } finally {
        setIsDesignerDataLoading(false);
      }
    };
    loadDesignerData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Auto-initialize for draft graphs (new agent)
  useEffect(() => {
    if (graphId && graphId.startsWith('draft_') && !isAgentInitialized) {
      // Check if we have existing data in localStorage (returning from node editor)
      let existingNodes: Node[] = [];
      let existingEdges: Edge[] = [];
      let hasExistingData = false;

      try {
        const savedNodes = localStorage.getItem(`forge-nodes-${graphId}`);
        const savedEdges = localStorage.getItem(`forge-edges-${graphId}`);
        if (savedNodes) {
          existingNodes = JSON.parse(savedNodes);
          hasExistingData = existingNodes.length > 0;
        }
        if (savedEdges) {
          existingEdges = JSON.parse(savedEdges);
        }
      } catch (e) {
        console.warn('Failed to read from localStorage:', e);
      }

      // Check tab context only if localStorage was empty
      // localStorage is the source of truth (updated by Node Editor page)
      const existingTab = getTabById(graphId);
      if (!hasExistingData && existingTab && existingTab.nodes.length > 0) {
        existingNodes = existingTab.nodes;
        existingEdges = existingTab.edges;
        hasExistingData = true;
      }

      const draftName = hasExistingData
        ? (existingTab?.name || `draft-${Date.now()}`)
        : `draft-${Date.now()}`;

      setAgentMetadata({
        name: draftName,
        description: hasExistingData
          ? (existingTab?.description || 'Draft agent')
          : 'New agent created in visual designer',
        version: '0.0.1',
        tags: ['draft', 'forge'],
      });
      setAgentName(draftName);
      setCanonicalGraphId(null);
      setNodes(existingNodes);
      setEdges(existingEdges);
      setSelectedAgent(null);
      setHistory(hasExistingData ? [{ nodes: existingNodes, edges: existingEdges }] : []);
      setHistoryIndex(hasExistingData ? 0 : -1);
      setHasUnsavedChanges(hasExistingData);
      setIsAgentInitialized(true);
      setSelectedTriggerIds([]);

      // Ensure tab is registered (for direct URL navigation)
      if (!existingTab) {
        openTab({
          id: graphId,
          name: draftName,
          displayName: 'New Graph',
          description: 'New agent created in visual designer',
          nodes: existingNodes,
          edges: existingEdges,
          isDraft: true,
          canonicalId: null,
          stateSchemaId: null,
          triggerIds: [],
        });
      }
    }
  }, [graphId, isAgentInitialized, getTabById, openTab]);

  // Auto-load graph when navigating to a specific graphId (not a draft)
  useEffect(() => {
    const loadGraphFromUrl = async () => {
      // Skip if it's a new draft or already initialized
      if (!graphId || graphId.startsWith('draft_') || isAgentInitialized) {
        return;
      }

      setIsLoading(true);
      setError(null);
      try {
        const { yamlToGraph, autoLayoutNodes } = await import('../../forge/lib/yaml-to-graph');

        // First check localStorage for cached nodes (may have local edits)
        let localNodes: Node[] = [];
        let useLocalStorage = false;
        try {
          const savedNodes = localStorage.getItem(`forge-nodes-${graphId}`);
          if (savedNodes) {
            localNodes = JSON.parse(savedNodes);
            if (localNodes.length > 0) {
              useLocalStorage = true;
            }
          }
        } catch (e) {
          console.warn('Failed to read from localStorage:', e);
        }

        // Fetch the graph metadata from the API (for name, description, etc.)
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/graphs/${graphId}`);
        if (!res.ok) {
          throw new Error(`Graph not found: ${res.statusText}`);
        }
        const graphData = await res.json();

        let nodes: Node[] = [];
        let edges: Edge[] = [];

        // If we have local nodes, use them (preserves local edits)
        if (useLocalStorage) {
          nodes = localNodes;
          // Try to get edges from localStorage too
          try {
            const savedEdges = localStorage.getItem(`forge-edges-${graphId}`);
            if (savedEdges) {
              edges = JSON.parse(savedEdges);
            }
          } catch (e) {
            // Fall back to API edges
          }
        }

        // If no local nodes, parse from API
        if (nodes.length === 0) {
          if (graphData.yaml_content) {
            try {
              // yaml_content is JSON string containing the graph spec
              const content = JSON.parse(graphData.yaml_content);
              if (content.spec?.graph) {
                nodes = content.spec.graph.nodes || [];
                edges = content.spec.graph.edges || [];
              } else if (content.graph) {
                nodes = content.graph.nodes || [];
                edges = content.graph.edges || [];
              }
            } catch (parseError) {
              // If JSON parse fails, try YAML
              const result = yamlToGraph(graphData.yaml_content);
              if (!result.error) {
                nodes = result.nodes;
                edges = result.edges;
              }
            }
          } else if (graphData.spec?.graph) {
            nodes = graphData.spec.graph.nodes || [];
            edges = graphData.spec.graph.edges || [];
          }
        }

        if (nodes.length === 0) {
          console.warn('No nodes found in graph data');
        }

        // Auto-layout nodes if they don't have positions
        const needsLayout = nodes.some(
          (n: Node) => !n.position || (n.position.x === 0 && n.position.y === 0)
        );
        const layoutedNodes = needsLayout ? autoLayoutNodes(nodes, edges) : nodes;

        setNodes(layoutedNodes);
        setEdges(edges);
        setAgentName(graphData.name || graphId);
        setAgentMetadata((prev) => ({
          ...prev,
          name: graphData.display_name || graphData.name || graphId,
          description: graphData.description || prev.description,
        }));
        setHasUnsavedChanges(useLocalStorage); // Mark as unsaved if using local changes
        setIsAgentInitialized(true);
        setHistory([{ nodes: layoutedNodes, edges }]);
        setHistoryIndex(0);

        // Ensure tab is registered (for direct URL navigation)
        const existingTab = getTabById(graphId);
        if (!existingTab) {
          openTab({
            id: graphId,
            name: graphData.name || graphId,
            displayName: graphData.display_name || graphData.name || graphId,
            description: graphData.description || '',
            nodes: layoutedNodes,
            edges,
            isDraft: false,
            canonicalId: graphId,
            stateSchemaId: null,
            triggerIds: [],
          });
        } else {
          // Update existing tab with loaded data
          updateTabNodes(graphId, layoutedNodes);
          updateTabEdges(graphId, edges);
        }

        const message = useLocalStorage
          ? `Loaded: ${graphData.display_name || graphData.name} (with local changes)`
          : `Loaded: ${graphData.display_name || graphData.name}`;
        setSuccessMessage(message);
        setTimeout(() => setSuccessMessage(null), 3000);
      } catch (error) {
        console.error('Failed to load graph from URL:', error);
        setError(`Failed to load graph. It may not exist or there was a network error.`);
      } finally {
        setIsLoading(false);
      }
    };

    loadGraphFromUrl();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [graphId, getTabById, openTab, updateTabNodes, updateTabEdges]);

  // Fetch available agents for the Open dialog
  useEffect(() => {
    const loadAvailableAgents = async () => {
      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/api/graphs?environment=dev&graph_type=user`
        );
        const data = await res.json();
        // Convert graph data to Agent format for the dialog
        const agents: Agent[] = (data.graphs || []).map((g: any) => ({
          id: g.id,
          name: g.name,
          display_name: g.display_name || g.name,
          description: g.description || '',
          version: g.version || '1.0.0',
          status: g.status || 'active',
          environment: 'dev',
          organization_id: g.organization_id,
          organization_name: g.organization_name || '',
          domain_id: g.domain_id,
          domain_name: g.domain_name || '',
          created_at: g.created_at || new Date().toISOString(),
          updated_at: g.updated_at || new Date().toISOString(),
          created_by: g.created_by || 'unknown',
          tags: Array.isArray(g.tags)
            ? g.tags
            : typeof g.tags === 'string'
              ? (() => {
                  try {
                    return JSON.parse(g.tags || '[]');
                  } catch {
                    return [];
                  }
                })()
              : [],
          graph_yaml: g.yaml_content || '',
          graph_json: {},
          tools_used: [],
          models_used: [],
          channels: [],
          metrics: {
            executions_24h: 0,
            success_rate: 0,
            error_count: 0,
            avg_latency_ms: 0,
            p95_latency_ms: 0,
            p99_latency_ms: 0,
          },
          cost_p95: 0,
          total_cost_24h: 0,
        }));
        setAvailableAgents(agents);
      } catch (err) {
        console.error('Failed to load available agents:', err);
      }
    };
    loadAvailableAgents();
  }, []);

  // Save nodes and edges to localStorage whenever they change (for node editor page)
  useEffect(() => {
    if (nodes.length > 0 && graphId) {
      try {
        localStorage.setItem(`forge-nodes-${graphId}`, JSON.stringify(nodes));
        localStorage.setItem(`forge-edges-${graphId}`, JSON.stringify(edges));
      } catch (error) {
        console.warn('Failed to save to localStorage:', error);
      }
    }
  }, [nodes, edges, graphId]);

  // Handle Configure button click - navigate to node detail page
  const handleConfigureNode = useCallback(
    (node: Node) => {
      router.push(`/app/graphs/${graphId}/node/${node.id}`);
    },
    [router, graphId]
  );

  useEffect(() => {
    setSelectedTriggerIds((prev) =>
      prev.filter((id) => triggers.some((trigger) => trigger.id === id))
    );
  }, [triggers]);

  useEffect(() => {
    if (!agentName) return;
    const loadAssignedTriggers = async () => {
      try {
        const assignments = await listGraphTriggers('agent', agentName);
        setSelectedTriggerIds(assignments.map((assignment) => assignment.triggerId));
      } catch (error) {
        console.warn('Failed to load graph triggers', error);
      }
    };
    loadAssignedTriggers();
  }, [agentName]);

  const persistGraphTriggers = useCallback(
    async (triggerIds: string[]) => {
      if (!agentName) {
        return;
      }

      setIsGraphTriggerSyncing(true);
      try {
        await saveGraphTriggers({
          targetType: 'agent',
          targetId: agentName,
          triggerIds,
          startNodeId: entryNodeId ?? undefined,
        });
      } catch (error) {
        console.error('Failed to persist graph triggers', error);
        setError('Failed to attach trigger to agent graph');
      } finally {
        setIsGraphTriggerSyncing(false);
      }
    },
    [agentName, entryNodeId]
  );

  const handleStateSchemaSave = useCallback(async (schemaDraft: StateSchemaDraft) => {
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
        const existingIndex = prev.findIndex((schema) => schema.id === saved.id);
        if (existingIndex >= 0) {
          const copy = [...prev];
          copy[existingIndex] = saved;
          return copy;
        }
        return [...prev, saved];
      });
      setActiveStateSchemaId(saved.id);
      setSuccessMessage(`State schema "${saved.name}" saved`);
    } catch (error) {
      console.error('Failed to save state schema', error);
      setError('Unable to save state schema');
    }
  }, []);

  const handleStateSchemaDelete = useCallback(
    async (schemaId: string) => {
      try {
        await apiDeleteStateSchema(schemaId);
        setStateSchemas((prev) => {
          const filtered = prev.filter((schema) => schema.id !== schemaId);
          if (activeStateSchemaId === schemaId) {
            setActiveStateSchemaId(filtered[0]?.id ?? null);
          }
          return filtered;
        });
      } catch (error) {
        console.error('Failed to delete state schema', error);
        setError('Unable to delete state schema');
      }
    },
    [activeStateSchemaId]
  );

  const handleTriggerSave = useCallback(
    async (triggerDraft: {
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
          const existingIndex = prev.findIndex((trigger) => trigger.id === saved.id);
          if (existingIndex >= 0) {
            const copy = [...prev];
            copy[existingIndex] = saved;
            return copy;
          }
          return [...prev, saved];
        });
        setSuccessMessage(`Trigger "${saved.name}" saved`);
      } catch (error) {
        console.error('Failed to save trigger', error);
        setError('Unable to save trigger');
      }
    },
    []
  );

  const handleTriggerDelete = useCallback(async (triggerId: string) => {
    try {
      await deleteTrigger(triggerId);
      setTriggers((prev) => prev.filter((trigger) => trigger.id !== triggerId));
      setSelectedTriggerIds((prev) => prev.filter((id) => id !== triggerId));
    } catch (error) {
      console.error('Failed to delete trigger', error);
      setError('Unable to delete trigger');
    }
  }, []);

  const handleTriggerSelection = useCallback(
    async (triggerId: string, selected: boolean) => {
      setSelectedTriggerIds((prev) => {
        const exists = prev.includes(triggerId);
        let next = prev;
        if (selected && !exists) {
          next = [...prev, triggerId];
        } else if (!selected && exists) {
          next = prev.filter((id) => id !== triggerId);
        }
        persistGraphTriggers(next);
        return next;
      });
    },
    [persistGraphTriggers]
  );

  // Keyboard shortcut: Escape to exit full-screen mode
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isMaximized) {
        setIsMaximized(false);
      }
      // F11 or Cmd/Ctrl + Shift + F to toggle maximize
      if (
        (e.key === 'F11' || ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === 'f')) &&
        !e.repeat
      ) {
        e.preventDefault();
        setIsMaximized(!isMaximized);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isMaximized]);

  const handleNew = () => {
    if (hasUnsavedChanges) {
      if (!confirm('You have unsaved changes. Are you sure you want to create a new agent?')) {
        return;
      }
    }

    // Create draft agent immediately (no dialog)
    const timestamp = Date.now();
    const draftName = `draft-${timestamp}`;

    setAgentMetadata({
      name: draftName,
      description: 'Draft agent created in visual designer',
      version: '0.0.1',
      tags: ['draft', 'forge'],
    });
    setAgentName(draftName);
    setCanonicalGraphId(null); // Reset canonical ID for new agent
    setNodes([]);
    setEdges([]);
    setSelectedAgent(null);
    setHistory([]);
    setHistoryIndex(-1);
    setHasUnsavedChanges(false);
    setIsAgentInitialized(true);
    setSuccessMessage(
      `Draft agent "${draftName}" created. Start adding nodes to build your workflow.`
    );
    setSelectedTriggerIds([]);

    // Auto-dismiss success message after 3 seconds
    setTimeout(() => setSuccessMessage(null), 3000);
  };

  const handleSaveMetadata = async (metadata: AgentMetadata) => {
    // This is called when the user saves from the properties dialog
    // Actually perform the save with the provided metadata
    await performSave(metadata);
  };

  const handleOpen = () => {
    setOpenDialogOpen(true);
  };

  // Check if this is an unsaved draft (needs naming before save)
  const isUnsavedDraft = graphId?.startsWith('draft_') && !canonicalGraphId;

  const handleSave = async () => {
    // If this is an unsaved draft, show the properties dialog to name it first
    if (isUnsavedDraft) {
      setPropertiesDialogMode('new');
      setPropertiesDialogOpen(true);
      return;
    }

    // Otherwise, save directly
    await performSave();
  };

  // Helper to increment patch version (0.0.1 -> 0.0.2)
  const incrementVersion = (version: string): string => {
    const parts = version.split('.');
    if (parts.length !== 3) return version;
    const patch = parseInt(parts[2], 10);
    if (isNaN(patch)) return version;
    return `${parts[0]}.${parts[1]}.${patch + 1}`;
  };

  // Actual save logic (called directly or after naming a draft)
  const performSave = async (metadata?: AgentMetadata) => {
    setIsSaving(true);
    setError(null);
    setSuccessMessage(null);
    try {
      const { registerAgentInManifest } = await import('../../forge/lib/manifest-api');

      const environment = (localStorage.getItem('selectedInstance') || 'dev') as
        | 'dev'
        | 'staging'
        | 'prod';

      // Use metadata if provided (from dialog), otherwise use current state
      const saveMetadata = metadata || agentMetadata;

      // Use canonicalGraphId if available (existing agent), otherwise use the new name
      const saveId = canonicalGraphId || saveMetadata.name;

      // Auto-increment version when saving an existing agent (not from dialog)
      // If metadata is provided (from dialog), use that version as-is
      let versionToSave = saveMetadata.version || '0.0.1';
      if (!metadata && canonicalGraphId) {
        // This is a save of an existing agent - increment the version
        versionToSave = incrementVersion(agentMetadata.version || '0.0.1');
      }

      const result = await registerAgentInManifest({
        agentId: saveId,
        nodes,
        edges,
        stateSchema: activeStateSchema,
        triggers: selectedTriggersList,
        organizationId: 'cibc',
        organizationName: 'CIBC',
        domainId: 'card-services',
        domainName: 'Card Services',
        environment,
        instanceId: 'dev',
        author: 'foundry-user',
        tags: saveMetadata.tags,
        isSystemAgent: false,
        displayName: saveMetadata.name,
        description: saveMetadata.description,
        version: versionToSave,
      });

      // If this was a new agent, capture the canonical ID from the response
      if (!canonicalGraphId && result?.id) {
        setCanonicalGraphId(result.id);
      }

      // Update local metadata state with new version
      setAgentMetadata((prev) => ({
        ...prev,
        ...(metadata || {}),
        version: versionToSave,
      }));
      if (metadata) {
        setAgentName(metadata.name);
      }

      // Update current version display
      setCurrentVersion(`v${versionToSave}`);

      // Mark the tab as saved in the context
      markTabSaved(graphId, result?.id || canonicalGraphId || undefined);

      setSuccessMessage(`Agent "${saveMetadata.name}" saved as v${versionToSave}`);
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
      const { registerAgentInManifest } = await import('../../forge/lib/manifest-api');
      const environment = (localStorage.getItem('selectedInstance') || 'dev') as
        | 'dev'
        | 'staging'
        | 'prod';

      await registerAgentInManifest({
        agentId: newName,
        nodes,
        edges,
        stateSchema: activeStateSchema,
        triggers: selectedTriggersList,
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
      setAgentMetadata((prev) => ({ ...prev, name: newName }));
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

  const handleDeploy = () => {
    // If there are unsaved changes or it's an unsaved draft, require save first
    if (hasUnsavedChanges || isUnsavedDraft) {
      setError('Please save your agent before deploying.');
      return;
    }

    // Show confirmation dialog
    setShowDeployConfirm(true);
  };

  const performDeploy = async () => {
    setShowDeployConfirm(false);
    setIsDeploying(true);
    setError(null);
    setSuccessMessage(null);
    try {
      const { forgeAPI } = await import('../../forge/lib/forge-api');

      // Get environment from localStorage or use 'dev' as default
      const environment = (localStorage.getItem('selectedInstance') || 'dev') as
        | 'dev'
        | 'staging'
        | 'prod';

      // Use canonicalGraphId for the deploy API call (the actual saved ID)
      const deployId = canonicalGraphId || agentName;
      await forgeAPI.deployGraph(deployId, {
        environment,
        git_commit: false, // TODO: Add UI option for Git commit
      });

      setSuccessMessage(`Agent "${agentMetadata.name}" v${agentMetadata.version} deployed to ${environment} successfully!`);
    } catch (error) {
      console.error('Failed to deploy:', error);
      setError(
        `Failed to deploy agent: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    } finally {
      setIsDeploying(false);
    }
  };

  const handleNodeDelete = useCallback(
    (nodeId: string) => {
      setNodes((nds) => nds.filter((node) => node.id !== nodeId));
      setEdges((eds) => eds.filter((edge) => edge.source !== nodeId && edge.target !== nodeId));
      addToHistory();
      setHasUnsavedChanges(true);
    },
    [addToHistory]
  );

  const handleLoadAgent = async (agent: Agent) => {
    setIsLoading(true);
    setError(null);
    setSuccessMessage(null);
    try {
      const { forgeAPI } = await import('../../forge/lib/forge-api');
      const { yamlToGraph, autoLayoutNodes } = await import('../../forge/lib/yaml-to-graph');

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
      setAgentMetadata((prev) => ({
        ...prev,
        name: result.agentName,
        description: agent.description ?? prev.description,
      }));
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

  const handleSelectVersion = async (version: DeploymentVersion) => {
    // Load the selected version from the API
    const fetchId = canonicalGraphId || graphId;
    if (!fetchId || !version.commitHash) {
      setCurrentVersion(version.version);
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      // The commitHash is the first 7 chars of the version ID - we need to find the full ID
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/graphs/${fetchId}/versions`);
      if (!res.ok) throw new Error('Failed to fetch versions');
      const data = await res.json();

      // Find the version with matching commitHash (first 7 chars of ID)
      const fullVersion = (data.versions || []).find(
        (v: any) => v.id?.substring(0, 7) === version.commitHash
      );

      if (!fullVersion) {
        throw new Error('Version not found');
      }

      // Load the reactflow data from the version
      if (fullVersion.reactflow_data) {
        const rfData = fullVersion.reactflow_data;
        setNodes(rfData.nodes || []);
        setEdges(rfData.edges || []);
        setCurrentVersion(version.version);
        setHasUnsavedChanges(true); // Mark as unsaved since we're loading an older version
        setSuccessMessage(`Loaded version ${version.version}`);
        setTimeout(() => setSuccessMessage(null), 3000);
      }
    } catch (err) {
      console.error('Error loading version:', err);
      setError(`Failed to load version: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle deploying a specific version
  const handleDeployVersion = async (version: DeploymentVersion) => {
    const fetchId = canonicalGraphId || graphId;
    if (!fetchId || !version.versionId) {
      setError('Cannot deploy: missing agent or version ID');
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/graphs/${fetchId}/versions/${version.versionId}/deploy`,
        { method: 'POST' }
      );

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Failed to deploy version');
      }

      // Update local state to reflect the deployed version
      setDeployedVersionId(version.versionId);
      setDeploymentVersions((prev) =>
        prev.map((v) => ({
          ...v,
          isDeployed: v.versionId === version.versionId,
        }))
      );

      setSuccessMessage(`Deployed ${version.version} successfully`);
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      console.error('Error deploying version:', err);
      setError(`Failed to deploy: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggleMaximize = () => {
    setIsMaximized(!isMaximized);
  };

  // Define toolbar actions - left side
  const forgeActions: ToolbarAction[] = useMemo(
    () => [
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
        tooltip: isSaving
          ? 'Saving...'
          : isUnsavedDraft
            ? 'Name and save your agent'
            : hasUnsavedChanges
              ? 'Save agent'
              : 'No changes to save',
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
    ],
    [isSaving, nodes.length, hasUnsavedChanges, historyIndex, history.length, isUnsavedDraft]
  );

  // Define toolbar actions - right side (Deploy + Maximize)
  const forgeRightActions: ToolbarAction[] = useMemo(
    () => [
      {
        icon: isMaximized ? Minimize2 : Maximize2,
        label: isMaximized ? 'Restore' : 'Maximize',
        onClick: handleToggleMaximize,
        variant: 'ghost',
        tooltip: isMaximized ? 'Restore to normal view' : 'Maximize canvas to full screen',
      },
      {
        icon: Rocket,
        label: 'Deploy',
        onClick: handleDeploy,
        disabled: isDeploying || nodes.length === 0 || hasUnsavedChanges || isUnsavedDraft,
        variant: 'default',
        tooltip: isDeploying
          ? 'Deploying...'
          : hasUnsavedChanges || isUnsavedDraft
            ? 'Save your agent before deploying'
            : 'Deploy agent to environment',
      },
    ],
    [isDeploying, nodes.length, isMaximized, hasUnsavedChanges, isUnsavedDraft]
  );

  return (
    <div
      className={`flex flex-col h-full transition-all duration-300 ${
        isMaximized ? 'fixed inset-0 z-50 bg-bg-0' : ''
      }`}
    >
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
            onDeployVersion={handleDeployVersion}
            disabled={nodes.length === 0}
          />
          <Toolbar
            rightActions={forgeRightActions}
            className="border-0 h-auto bg-transparent px-0"
          />
        </div>
      </div>

      {/* Designer configuration strip */}
      <div className="border-b border-white/10 bg-bg-1 px-6 py-3 flex flex-wrap items-center gap-8">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-emerald-500/10">
            <Database className="w-4 h-4 text-emerald-400" />
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
                      {schema.name} ({schema.version})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button size="sm" variant="ghost" onClick={() => setIsStatePanelOpen(true)}>
                Manage
              </Button>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          <div className="p-2 rounded-lg bg-indigo-500/10">
            <Plug className="w-4 h-4 text-indigo-400" />
          </div>
          <div>
            <div className="text-xs text-fg-3 uppercase tracking-wide">Entry Triggers</div>
            <div className="flex items-center gap-2 flex-wrap">
              {selectedTriggersList.length === 0 && (
                <Badge variant="outline" className="text-amber-300 border-amber-500/40">
                  No triggers configured
                </Badge>
              )}
              {selectedTriggersList.map((trigger) => (
                <Badge
                  key={trigger.id}
                  variant="outline"
                  className="bg-indigo-500/10 border-indigo-400/40"
                >
                  {trigger.name}
                </Badge>
              ))}
              <Button size="sm" variant="ghost" onClick={() => setIsTriggerDrawerOpen(true)}>
                Configure
              </Button>
            </div>
          </div>
          {isGraphTriggerSyncing && (
            <span className="text-xs text-amber-400">Syncing triggers...</span>
          )}
        </div>
      </div>

      {/* Agent Open Dialog */}
      <AgentOpenDialog
        open={openDialogOpen}
        onOpenChange={setOpenDialogOpen}
        agents={availableAgents}
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

      {/* Deploy Confirmation Dialog */}
      <ConfirmDialog
        open={showDeployConfirm}
        onOpenChange={setShowDeployConfirm}
        title="Deploy Agent"
        description={`Are you sure you want to deploy "${agentMetadata.name}" v${agentMetadata.version}? This will make the agent available in the selected environment.`}
        confirmLabel={`Deploy v${agentMetadata.version}`}
        cancelLabel="Cancel"
        onConfirm={performDeploy}
        onCancel={() => setShowDeployConfirm(false)}
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
          <div className="flex-1 relative">
            <GraphEditor
              nodes={nodes}
              edges={edges}
              onNodesChange={setNodes}
              onEdgesChange={setEdges}
              onNodeSelect={setSelectedNode}
            />
          </div>
        )}

        {/* Node Preview Panel - Right side */}
        {selectedNode && (
          <NodePreviewPanel
            node={selectedNode}
            onClose={() => setSelectedNode(null)}
            onConfigure={handleConfigureNode}
          />
        )}
      </div>

      {/* Drawers */}
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
        onToggleTriggerSelection={handleTriggerSelection}
        onSaveTrigger={handleTriggerSave}
        onDeleteTrigger={handleTriggerDelete}
      />
    </div>
  );
}
