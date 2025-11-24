'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { X, Circle, FileCode } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useGraphTabs, type GraphTab } from '../context/GraphTabsContext';
import { ConfirmDialog } from '@/components/ui/confirm-dialog';

interface GraphTabBarProps {
  className?: string;
}

export function GraphTabBar({ className }: GraphTabBarProps) {
  const router = useRouter();
  const { tabs, activeTabId, setActiveTab, closeTab, getTabById } = useGraphTabs();
  const [confirmCloseTabId, setConfirmCloseTabId] = useState<string | null>(null);

  if (tabs.length === 0) {
    return null;
  }

  const tabToClose = confirmCloseTabId ? getTabById(confirmCloseTabId) : null;

  const handleSelectTab = (tabId: string) => {
    setActiveTab(tabId);
    // Navigate to the selected graph
    router.push(`/app/graphs/${tabId}`);
  };

  const handleCloseTab = (tabId: string) => {
    const closed = closeTab(tabId);
    if (closed) {
      // Tab was closed (no unsaved changes)
      navigateAfterClose(tabId);
    } else {
      // Tab has unsaved changes, show confirmation dialog
      setConfirmCloseTabId(tabId);
    }
  };

  const navigateAfterClose = (closedTabId: string) => {
    // If we closed the active tab, navigate to another tab or gallery
    if (closedTabId === activeTabId) {
      const remainingTabs = tabs.filter(t => t.id !== closedTabId);
      if (remainingTabs.length > 0) {
        router.push(`/app/graphs/${remainingTabs[0].id}`);
      } else {
        router.push('/app/graphs');
      }
    }
  };

  const handleConfirmClose = () => {
    if (confirmCloseTabId) {
      // Force close the tab
      closeTab(confirmCloseTabId, true);
      navigateAfterClose(confirmCloseTabId);
      setConfirmCloseTabId(null);
    }
  };

  return (
    <>
      <div className={cn(
        'flex items-center gap-1 bg-bg-1 border-b border-white/10 px-2 py-1 overflow-x-auto',
        className
      )}>
        {tabs.map((tab) => (
          <GraphTabItem
            key={tab.id}
            tab={tab}
            isActive={tab.id === activeTabId}
            onSelect={() => handleSelectTab(tab.id)}
            onClose={() => handleCloseTab(tab.id)}
          />
        ))}
      </div>

      {/* Unsaved changes confirmation dialog */}
      <ConfirmDialog
        open={!!confirmCloseTabId}
        onOpenChange={(open) => !open && setConfirmCloseTabId(null)}
        title="Unsaved Changes"
        description={`"${tabToClose?.displayName || tabToClose?.name || 'This tab'}" has unsaved changes. Are you sure you want to close it?`}
        confirmLabel="Close Without Saving"
        cancelLabel="Cancel"
        variant="destructive"
        onConfirm={handleConfirmClose}
        onCancel={() => setConfirmCloseTabId(null)}
      />
    </>
  );
}

interface GraphTabItemProps {
  tab: GraphTab;
  isActive: boolean;
  onSelect: () => void;
  onClose: () => void;
}

function GraphTabItem({ tab, isActive, onSelect, onClose }: GraphTabItemProps) {
  const handleClose = (e: React.MouseEvent) => {
    e.stopPropagation();
    onClose();
  };

  return (
    <div
      onClick={onSelect}
      className={cn(
        'group flex items-center gap-2 px-3 py-1.5 rounded-t-lg cursor-pointer transition-colors',
        'border border-b-0 border-transparent',
        isActive
          ? 'bg-bg-0 border-white/10 text-fg-0'
          : 'text-fg-2 hover:text-fg-1 hover:bg-white/5'
      )}
    >
      <FileCode className="w-4 h-4 flex-shrink-0 text-blue-400" />

      <span className="text-sm font-medium truncate max-w-[150px]">
        {tab.displayName || tab.name}
      </span>

      {/* Unsaved indicator */}
      {tab.hasUnsavedChanges && (
        <Circle className="w-2 h-2 fill-amber-400 text-amber-400 flex-shrink-0" />
      )}

      {/* Loading indicator */}
      {tab.isLoading && (
        <div className="w-3 h-3 border border-blue-400 border-t-transparent rounded-full animate-spin flex-shrink-0" />
      )}

      {/* Close button */}
      <button
        onClick={handleClose}
        className={cn(
          'p-0.5 rounded hover:bg-white/10 transition-colors flex-shrink-0',
          'opacity-0 group-hover:opacity-100',
          isActive && 'opacity-60'
        )}
        title="Close tab"
      >
        <X className="w-3.5 h-3.5" />
      </button>
    </div>
  );
}

export default GraphTabBar;
