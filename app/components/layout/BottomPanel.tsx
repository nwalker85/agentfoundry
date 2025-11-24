'use client';

import { useEffect, useState, useCallback } from 'react';
import { usePathname } from 'next/navigation';
import { MessageCircle, Activity, Zap, FileText, ChevronDown, ChevronUp, X, Code } from 'lucide-react';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { AdminTab } from './BottomPanel/AdminTab';
import { SystemStatusTab } from './BottomPanel/SystemStatusTab';
import { EventsTab } from './BottomPanel/EventsTab';
import { LogsTab } from './BottomPanel/LogsTab';
import { CodeTab } from './BottomPanel/CodeTab';

type PanelTab = 'admin' | 'system' | 'events' | 'logs' | 'code';

interface BottomPanelProps {
  defaultTab?: PanelTab;
  onTabChange?: (tab: PanelTab) => void;
  onCollapseChange?: (collapsed: boolean) => void;
}

export function BottomPanel({
  defaultTab = 'admin',
  onTabChange,
  onCollapseChange,
}: BottomPanelProps) {
  const pathname = usePathname();
  const [activeTab, setActiveTab] = useState<PanelTab>(defaultTab);
  const [isCollapsed, setIsCollapsed] = useState(true); // Always start minimized
  const [hasAdminBeenClicked, setHasAdminBeenClicked] = useState(false);

  // Code tab is always available now (useful for reviewing agent code from anywhere)
  const isOnGraphsPage = true; // pathname?.startsWith('/app/graphs') || pathname?.startsWith('/app/forge');

  // Initialize admin click state from localStorage
  useEffect(() => {
    try {
      const clicked = localStorage.getItem('bottomPanelAdminClicked');
      if (clicked) {
        setHasAdminBeenClicked(JSON.parse(clicked));
      }
    } catch {
      // ignore
    }
  }, []);

  // Handle admin tab click - mark as clicked and stop pulse
  const handleAdminClick = useCallback(() => {
    if (!hasAdminBeenClicked) {
      setHasAdminBeenClicked(true);
      try {
        localStorage.setItem('bottomPanelAdminClicked', JSON.stringify(true));
      } catch {
        // ignore
      }
    }
  }, [hasAdminBeenClicked]);

  // Notify parent of collapse state changes
  useEffect(() => {
    onCollapseChange?.(isCollapsed);
  }, [isCollapsed, onCollapseChange]);

  // Handle tab changes from external sources (e.g., footer clicks)
  useEffect(() => {
    if (defaultTab !== activeTab) {
      if (defaultTab === 'admin') {
        handleAdminClick();
      }
      setActiveTab(defaultTab);
      setIsCollapsed(false);
    }
  }, [defaultTab, activeTab, handleAdminClick]);

  const handleTabChange = useCallback(
    (value: string) => {
      const tab = value as PanelTab;
      setActiveTab(tab);
      onTabChange?.(tab);
    },
    [onTabChange]
  );

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Cmd/Ctrl + K to open admin assistant
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        handleAdminClick();
        setActiveTab('admin');
        setIsCollapsed(false);
      }
      // Cmd/Ctrl + Shift + L to open logs
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === 'l') {
        e.preventDefault();
        setActiveTab('logs');
        setIsCollapsed(false);
      }
      // Cmd/Ctrl + Shift + E to open events
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === 'e') {
        e.preventDefault();
        setActiveTab('events');
        setIsCollapsed(false);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleAdminClick]);

  if (isCollapsed) {
    return (
      <div className="h-8 border-t border-white/10 bg-bg-0/95 backdrop-blur-sm flex items-center justify-between px-3">
        <div className="flex items-center gap-2 text-xs text-fg-2">
          <button
            onClick={() => {
              handleAdminClick();
              setActiveTab('admin');
              setIsCollapsed(false);
            }}
            className={`flex items-center gap-1.5 px-2 py-1 rounded hover:bg-bg-2 hover:text-fg-0 transition-colors ${!hasAdminBeenClicked ? 'motion-safe:animate-soft-pulse-blue' : ''}`}
          >
            <MessageCircle className="h-3 w-3" />
            <span>Admin</span>
          </button>
          <button
            onClick={() => {
              setActiveTab('system');
              setIsCollapsed(false);
            }}
            className="flex items-center gap-1.5 px-2 py-1 rounded hover:bg-bg-2 hover:text-fg-0 transition-colors"
          >
            <Activity className="h-3 w-3" />
            <span>System</span>
          </button>
          <button
            onClick={() => {
              setActiveTab('events');
              setIsCollapsed(false);
            }}
            className="flex items-center gap-1.5 px-2 py-1 rounded hover:bg-bg-2 hover:text-fg-0 transition-colors"
          >
            <Zap className="h-3 w-3" />
            <span>Events</span>
          </button>
          <button
            onClick={() => {
              setActiveTab('logs');
              setIsCollapsed(false);
            }}
            className="flex items-center gap-1.5 px-2 py-1 rounded hover:bg-bg-2 hover:text-fg-0 transition-colors"
          >
            <FileText className="h-3 w-3" />
            <span>Logs</span>
          </button>
          {isOnGraphsPage && (
            <button
              onClick={() => {
                setActiveTab('code');
                setIsCollapsed(false);
              }}
              className="flex items-center gap-1.5 px-2 py-1 rounded hover:bg-bg-2 hover:text-fg-0 transition-colors text-purple-400"
            >
              <Code className="h-3 w-3" />
              <span>Code</span>
            </button>
          )}
        </div>
        <button
          onClick={() => setIsCollapsed(false)}
          className="p-1 rounded hover:bg-bg-2 text-fg-2 hover:text-fg-0 transition-colors"
          aria-label="Expand panel"
        >
          <ChevronUp className="h-4 w-4" />
        </button>
      </div>
    );
  }

  return (
    <div className="border-t border-white/10 bg-bg-1/95 backdrop-blur-sm flex flex-col h-full">
      <Tabs value={activeTab} onValueChange={handleTabChange} className="flex flex-col h-full">
        <div className="flex items-center justify-between border-b border-white/10 px-3 py-1.5">
          <TabsList className="bg-transparent border-none h-auto p-0 gap-1">
            <TabsTrigger
              value="admin"
              onClick={handleAdminClick}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-xs data-[state=active]:bg-bg-2 data-[state=active]:text-fg-0 rounded-md ${!hasAdminBeenClicked ? 'motion-safe:animate-soft-pulse-blue' : ''}`}
            >
              <MessageCircle className="h-3.5 w-3.5" />
              <span>Admin</span>
            </TabsTrigger>
            <TabsTrigger
              value="system"
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs data-[state=active]:bg-bg-2 data-[state=active]:text-fg-0 rounded-md"
            >
              <Activity className="h-3.5 w-3.5" />
              <span>System</span>
            </TabsTrigger>
            <TabsTrigger
              value="events"
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs data-[state=active]:bg-bg-2 data-[state=active]:text-fg-0 rounded-md"
            >
              <Zap className="h-3.5 w-3.5" />
              <span>Events</span>
            </TabsTrigger>
            <TabsTrigger
              value="logs"
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs data-[state=active]:bg-bg-2 data-[state=active]:text-fg-0 rounded-md"
            >
              <FileText className="h-3.5 w-3.5" />
              <span>Logs</span>
            </TabsTrigger>
            {isOnGraphsPage && (
              <TabsTrigger
                value="code"
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs data-[state=active]:bg-bg-2 data-[state=active]:text-fg-0 data-[state=active]:text-purple-400 rounded-md text-purple-400"
              >
                <Code className="h-3.5 w-3.5" />
                <span>Code</span>
              </TabsTrigger>
            )}
          </TabsList>

          <div className="flex items-center gap-1">
            <button
              onClick={() => setIsCollapsed(true)}
              className="p-1 rounded hover:bg-bg-2 text-fg-2 hover:text-fg-0 transition-colors"
              aria-label="Collapse panel"
            >
              <ChevronDown className="h-4 w-4" />
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-hidden">
          <TabsContent value="admin" className="h-full m-0">
            <AdminTab />
          </TabsContent>
          <TabsContent value="system" className="h-full m-0">
            <SystemStatusTab />
          </TabsContent>
          <TabsContent value="events" className="h-full m-0">
            <EventsTab />
          </TabsContent>
          <TabsContent value="logs" className="h-full m-0">
            <LogsTab />
          </TabsContent>
          {isOnGraphsPage && (
            <TabsContent value="code" className="h-full m-0">
              <CodeTab />
            </TabsContent>
          )}
        </div>
      </Tabs>
    </div>
  );
}
