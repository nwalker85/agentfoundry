'use client';

import { X, Plus, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

export interface AgentTab {
  id: string;
  name: string;
  isDraft: boolean;
  hasUnsavedChanges: boolean;
}

interface AgentTabsProps {
  tabs: AgentTab[];
  activeTabId: string;
  onTabSelect: (tabId: string) => void;
  onTabClose: (tabId: string) => void;
  onNewTab: () => void;
  maxTabs?: number;
}

export function AgentTabs({
  tabs,
  activeTabId,
  onTabSelect,
  onTabClose,
  onNewTab,
  maxTabs = 10,
}: AgentTabsProps) {
  const handleCloseTab = (e: React.MouseEvent, tabId: string) => {
    e.stopPropagation();
    onTabClose(tabId);
  };

  return (
    <div className="flex items-center gap-1 bg-bg-0 border-b border-white/10 px-4 overflow-x-auto">
      {/* Tabs */}
      <div className="flex items-center gap-1 flex-1 min-w-0">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onTabSelect(tab.id)}
            className={cn(
              'group relative flex items-center gap-2 px-3 py-2 text-sm font-medium transition-colors min-w-[120px] max-w-[200px] border-b-2',
              activeTabId === tab.id
                ? 'text-fg-0 border-blue-500 bg-bg-1'
                : 'text-fg-2 border-transparent hover:text-fg-0 hover:bg-bg-1'
            )}
          >
            {/* Tab Name */}
            <span className="truncate flex-1">
              {tab.name}
              {tab.isDraft && ' (Draft)'}
            </span>

            {/* Unsaved Indicator */}
            {tab.hasUnsavedChanges && (
              <div
                className="w-2 h-2 rounded-full bg-amber-400 flex-shrink-0"
                title="Unsaved changes"
              />
            )}

            {/* Close Button */}
            <button
              onClick={(e) => handleCloseTab(e, tab.id)}
              className="flex-shrink-0 p-0.5 rounded hover:bg-bg-2 text-fg-3 hover:text-fg-0 transition-colors"
              title="Close tab"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </button>
        ))}
      </div>

      {/* New Tab Button */}
      <Button
        onClick={onNewTab}
        disabled={tabs.length >= maxTabs}
        size="sm"
        variant="ghost"
        className="flex-shrink-0 h-8 px-2"
        title={tabs.length >= maxTabs ? `Maximum ${maxTabs} tabs reached` : 'New agent (Cmd+T)'}
      >
        <Plus className="w-4 h-4" />
      </Button>

      {/* Max tabs warning */}
      {tabs.length >= maxTabs && (
        <div className="flex items-center gap-1 text-xs text-amber-400 flex-shrink-0 ml-2">
          <AlertCircle className="w-3 h-3" />
          <span>Max tabs</span>
        </div>
      )}
    </div>
  );
}
