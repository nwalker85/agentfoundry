'use client';

import { useState, useEffect, useRef, useCallback, use } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Save, Trash2 } from 'lucide-react';
import { NodeEditor } from '../../../../forge/components/NodeEditor';
import { useGraphTabs } from '../../../context/GraphTabsContext';
import type { Node } from 'reactflow';

export default function NodeEditorPage({
  params,
}: {
  params: Promise<{ graphId: string; nodeId: string }>;
}) {
  const { graphId, nodeId } = use(params);
  const router = useRouter();
  const { updateTabNodes } = useGraphTabs();
  const [node, setNode] = useState<Node | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  // Debounce timer ref
  const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Load node data from localStorage or API
  useEffect(() => {
    const loadNode = async () => {
      try {
        // TODO: Load from API or state management
        // For now, we'll need to pass node data via query params or global state
        // This is a temporary solution until we implement proper state management
        const savedNodes = localStorage.getItem(`forge-nodes-${graphId}`);
        if (savedNodes) {
          const nodes = JSON.parse(savedNodes);
          const foundNode = nodes.find((n: Node) => n.id === nodeId);
          if (foundNode) {
            setNode(foundNode);
          }
        }
      } catch (error) {
        console.error('Failed to load node:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadNode();
  }, [graphId, nodeId]);

  // Debounced save to localStorage
  const debouncedSave = useCallback(
    (updatedNode: Node) => {
      // Clear any pending save
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }

      // Schedule save after 500ms of no changes
      saveTimeoutRef.current = setTimeout(() => {
        try {
          const savedNodes = localStorage.getItem(`forge-nodes-${graphId}`);
          if (savedNodes) {
            const nodes = JSON.parse(savedNodes);
            const updatedNodes = nodes.map((n: Node) => (n.id === nodeId ? updatedNode : n));

            // Save to localStorage (source of truth)
            localStorage.setItem(`forge-nodes-${graphId}`, JSON.stringify(updatedNodes));

            // Also sync to tab context so it stays in sync
            updateTabNodes(graphId, updatedNodes);
            setHasUnsavedChanges(false);
          }
        } catch (error) {
          console.error('Failed to save node:', error);
        }
      }, 500);
    },
    [graphId, nodeId, updateTabNodes]
  );

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
    };
  }, []);

  const handleNodeUpdate = (updatedNode: Node) => {
    // Update local state immediately for responsive UI
    setNode(updatedNode);
    setHasUnsavedChanges(true);

    // Debounce the actual save
    debouncedSave(updatedNode);
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      // Flush any pending debounced save immediately
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }

      // Save current node state
      if (node) {
        const savedNodes = localStorage.getItem(`forge-nodes-${graphId}`);
        if (savedNodes) {
          const nodes = JSON.parse(savedNodes);
          const updatedNodes = nodes.map((n: Node) => (n.id === nodeId ? node : n));
          localStorage.setItem(`forge-nodes-${graphId}`, JSON.stringify(updatedNodes));
          updateTabNodes(graphId, updatedNodes);
        }
      }

      setHasUnsavedChanges(false);
      router.push(`/app/graphs/${graphId}`);
    } catch (error) {
      console.error('Failed to save:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm(`Delete node "${node?.data.label || nodeId}"?`)) {
      return;
    }

    try {
      // TODO: Implement actual delete
      const savedNodes = localStorage.getItem(`forge-nodes-${graphId}`);
      if (savedNodes) {
        const nodes = JSON.parse(savedNodes);
        const filteredNodes = nodes.filter((n: Node) => n.id !== nodeId);
        localStorage.setItem(`forge-nodes-${graphId}`, JSON.stringify(filteredNodes));
      }

      router.push(`/app/graphs/${graphId}`);
    } catch (error) {
      console.error('Failed to delete:', error);
    }
  };

  const handleBack = () => {
    router.push(`/app/graphs/${graphId}`);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-fg-2">Loading node...</div>
      </div>
    );
  }

  if (!node) {
    return (
      <div className="flex flex-col items-center justify-center h-screen gap-4">
        <div className="text-fg-1">Node not found</div>
        <Button onClick={handleBack} variant="outline">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Graph
        </Button>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-bg-0">
      {/* Header */}
      <div className="h-14 border-b border-white/10 bg-bg-1 flex items-center px-6 gap-4">
        <Button variant="ghost" size="sm" onClick={handleBack} className="gap-2">
          <ArrowLeft className="w-4 h-4" />
          Back to Graph
        </Button>

        {/* Breadcrumb */}
        <div className="flex items-center gap-2 text-sm text-fg-3">
          <span>Forge</span>
          <span>/</span>
          <span>{graphId}</span>
          <span>/</span>
          <span className="text-fg-1 font-medium">{node.data.label || nodeId}</span>
        </div>

        {/* Spacer */}
        <div className="flex-1" />

        {/* Actions */}
        <Button
          variant="outline"
          size="sm"
          onClick={handleDelete}
          className="gap-2 border-red-600/30 text-red-400 hover:bg-red-600/10"
        >
          <Trash2 className="w-4 h-4" />
          Delete
        </Button>
        <Button size="sm" onClick={handleSave} disabled={isSaving} className="gap-2">
          <Save className="w-4 h-4" />
          {isSaving ? 'Saving...' : hasUnsavedChanges ? 'Save & Close' : 'Close'}
        </Button>
        {hasUnsavedChanges && (
          <span className="text-xs text-amber-400 ml-2">Unsaved</span>
        )}
      </div>

      {/* Main Content - Full Page Node Editor */}
      <div className="flex-1 overflow-hidden">
        <div className="h-full overflow-y-auto">
          <div className="max-w-7xl mx-auto p-6">
            <NodeEditor
              node={node}
              triggers={[]} // TODO: Load triggers from context
              onNodeUpdate={handleNodeUpdate}
              onNodeDelete={handleDelete}
              onClose={handleBack}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
