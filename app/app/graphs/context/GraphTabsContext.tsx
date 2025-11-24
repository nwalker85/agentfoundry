'use client';

import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import type { Node, Edge } from 'reactflow';

export interface GraphTab {
  id: string;
  name: string;
  displayName: string;
  description?: string;
  nodes: Node[];
  edges: Edge[];
  hasUnsavedChanges: boolean;
  isLoading: boolean;
  isDraft: boolean;
  canonicalId: string | null;
  stateSchemaId: string | null;
  triggerIds: string[];
}

interface GraphTabsContextType {
  tabs: GraphTab[];
  activeTabId: string | null;
  activeTab: GraphTab | null;

  // Tab management
  openTab: (tab: Omit<GraphTab, 'hasUnsavedChanges' | 'isLoading'>) => void;
  closeTab: (tabId: string, force?: boolean) => boolean; // Returns false if blocked by unsaved changes (unless force=true)
  setActiveTab: (tabId: string) => void;

  // Tab state updates
  updateTabNodes: (tabId: string, nodes: Node[]) => void;
  updateTabEdges: (tabId: string, edges: Edge[]) => void;
  updateTabName: (tabId: string, name: string, displayName?: string) => void;
  updateTabDescription: (tabId: string, description: string) => void;
  markTabSaved: (tabId: string, canonicalId?: string) => void;
  markTabLoading: (tabId: string, isLoading: boolean) => void;
  updateTabStateSchema: (tabId: string, schemaId: string | null) => void;
  updateTabTriggers: (tabId: string, triggerIds: string[]) => void;

  // Utility
  hasAnyUnsavedChanges: boolean;
  getTabById: (tabId: string) => GraphTab | undefined;
}

const GraphTabsContext = createContext<GraphTabsContextType | null>(null);

export function GraphTabsProvider({ children }: { children: React.ReactNode }) {
  const [tabs, setTabs] = useState<GraphTab[]>([]);
  const [activeTabId, setActiveTabId] = useState<string | null>(null);

  // Persist tabs to sessionStorage
  useEffect(() => {
    const saved = sessionStorage.getItem('graphTabs');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setTabs(parsed.tabs || []);
        setActiveTabId(parsed.activeTabId || null);
      } catch (e) {
        console.warn('Failed to restore graph tabs:', e);
      }
    }
  }, []);

  useEffect(() => {
    if (tabs.length > 0) {
      sessionStorage.setItem('graphTabs', JSON.stringify({ tabs, activeTabId }));
    } else {
      // Clear sessionStorage when all tabs are closed
      sessionStorage.removeItem('graphTabs');
    }
  }, [tabs, activeTabId]);

  const activeTab = tabs.find(t => t.id === activeTabId) || null;
  const hasAnyUnsavedChanges = tabs.some(t => t.hasUnsavedChanges);

  const openTab = useCallback((newTab: Omit<GraphTab, 'hasUnsavedChanges' | 'isLoading'>) => {
    setTabs(prev => {
      // Check if tab already exists
      const existing = prev.find(t => t.id === newTab.id);
      if (existing) {
        setActiveTabId(newTab.id);
        return prev;
      }

      const tab: GraphTab = {
        ...newTab,
        hasUnsavedChanges: false,
        isLoading: false,
      };

      return [...prev, tab];
    });
    setActiveTabId(newTab.id);
  }, []);

  const closeTab = useCallback((tabId: string, force: boolean = false): boolean => {
    const tab = tabs.find(t => t.id === tabId);
    // If not forcing and tab has unsaved changes, return false to let caller handle confirmation
    if (!force && tab?.hasUnsavedChanges) {
      return false;
    }

    // Clean up localStorage for draft tabs when closing
    if (tabId.startsWith('draft_')) {
      try {
        localStorage.removeItem(`forge-nodes-${tabId}`);
        localStorage.removeItem(`forge-edges-${tabId}`);
      } catch (e) {
        console.warn('Failed to clean up localStorage for closed tab:', e);
      }
    }

    setTabs(prev => {
      const newTabs = prev.filter(t => t.id !== tabId);

      // If closing active tab, switch to another
      if (activeTabId === tabId && newTabs.length > 0) {
        const closedIndex = prev.findIndex(t => t.id === tabId);
        const newActiveIndex = Math.min(closedIndex, newTabs.length - 1);
        setActiveTabId(newTabs[newActiveIndex]?.id || null);
      } else if (newTabs.length === 0) {
        setActiveTabId(null);
      }

      return newTabs;
    });

    return true;
  }, [tabs, activeTabId]);

  const setActiveTab = useCallback((tabId: string) => {
    if (tabs.some(t => t.id === tabId)) {
      setActiveTabId(tabId);
    }
  }, [tabs]);

  const updateTabNodes = useCallback((tabId: string, nodes: Node[]) => {
    setTabs(prev => prev.map(t =>
      t.id === tabId
        ? { ...t, nodes, hasUnsavedChanges: true }
        : t
    ));
  }, []);

  const updateTabEdges = useCallback((tabId: string, edges: Edge[]) => {
    setTabs(prev => prev.map(t =>
      t.id === tabId
        ? { ...t, edges, hasUnsavedChanges: true }
        : t
    ));
  }, []);

  const updateTabName = useCallback((tabId: string, name: string, displayName?: string) => {
    setTabs(prev => prev.map(t =>
      t.id === tabId
        ? { ...t, name, displayName: displayName || name, hasUnsavedChanges: true }
        : t
    ));
  }, []);

  const updateTabDescription = useCallback((tabId: string, description: string) => {
    setTabs(prev => prev.map(t =>
      t.id === tabId
        ? { ...t, description, hasUnsavedChanges: true }
        : t
    ));
  }, []);

  const markTabSaved = useCallback((tabId: string, canonicalId?: string) => {
    setTabs(prev => prev.map(t =>
      t.id === tabId
        ? {
            ...t,
            hasUnsavedChanges: false,
            isDraft: false,
            canonicalId: canonicalId || t.canonicalId,
            // Update id if we got a canonical ID for a draft
            id: canonicalId && t.isDraft ? canonicalId : t.id,
          }
        : t
    ));
    // Update activeTabId if the tab id changed
    if (canonicalId) {
      setActiveTabId(prev => prev === tabId ? canonicalId : prev);
    }
  }, []);

  const markTabLoading = useCallback((tabId: string, isLoading: boolean) => {
    setTabs(prev => prev.map(t =>
      t.id === tabId ? { ...t, isLoading } : t
    ));
  }, []);

  const updateTabStateSchema = useCallback((tabId: string, schemaId: string | null) => {
    setTabs(prev => prev.map(t =>
      t.id === tabId
        ? { ...t, stateSchemaId: schemaId, hasUnsavedChanges: true }
        : t
    ));
  }, []);

  const updateTabTriggers = useCallback((tabId: string, triggerIds: string[]) => {
    setTabs(prev => prev.map(t =>
      t.id === tabId
        ? { ...t, triggerIds, hasUnsavedChanges: true }
        : t
    ));
  }, []);

  const getTabById = useCallback((tabId: string) => {
    return tabs.find(t => t.id === tabId);
  }, [tabs]);

  return (
    <GraphTabsContext.Provider value={{
      tabs,
      activeTabId,
      activeTab,
      openTab,
      closeTab,
      setActiveTab,
      updateTabNodes,
      updateTabEdges,
      updateTabName,
      updateTabDescription,
      markTabSaved,
      markTabLoading,
      updateTabStateSchema,
      updateTabTriggers,
      hasAnyUnsavedChanges,
      getTabById,
    }}>
      {children}
    </GraphTabsContext.Provider>
  );
}

export function useGraphTabs() {
  const context = useContext(GraphTabsContext);
  if (!context) {
    throw new Error('useGraphTabs must be used within a GraphTabsProvider');
  }
  return context;
}
