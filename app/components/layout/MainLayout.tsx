'use client';

import { ReactNode, useState, useCallback, useRef, useEffect } from 'react';
import { Panel, PanelGroup, PanelResizeHandle, ImperativePanelHandle } from 'react-resizable-panels';
import { BottomPanel } from './BottomPanel';
import { StatusFooter } from './StatusFooter';

export function MainLayout({ children }: { children: ReactNode }) {
  const [isPanelCollapsed, setIsPanelCollapsed] = useState(true);
  const [activeTab, setActiveTab] = useState<string>('admin');
  const bottomPanelRef = useRef<ImperativePanelHandle>(null);

  const handlePanelCollapse = useCallback((collapsed: boolean) => {
    setIsPanelCollapsed(collapsed);
    // Resize panel when collapse state changes
    if (bottomPanelRef.current) {
      if (collapsed) {
        bottomPanelRef.current.resize(4);
      } else {
        bottomPanelRef.current.resize(30);
      }
    }
  }, []);

  const handleOpenPanel = useCallback((tab: string) => {
    setActiveTab(tab);
    setIsPanelCollapsed(false);
    // Expand the panel
    if (bottomPanelRef.current) {
      bottomPanelRef.current.resize(30);
    }
  }, []);

  return (
    <div className="flex-1 flex flex-col">
      {/* Main content area with resizable bottom panel */}
      <PanelGroup direction="vertical" className="flex-1 overflow-hidden">
        {/* Main Content */}
        <Panel defaultSize={98} minSize={30}>
          <main id="main-content" className="h-full overflow-auto">
            {children}
          </main>
        </Panel>

        {/* Resize Handle - only visible when panel is expanded */}
        {!isPanelCollapsed && (
          <PanelResizeHandle className="h-1 bg-blue-500/20 hover:bg-blue-500/40 transition-colors" />
        )}

        {/* Bottom Panel */}
        <Panel
          ref={bottomPanelRef}
          defaultSize={4}
          minSize={4}
          maxSize={60}
          collapsible={false}
        >
          <BottomPanel defaultTab={activeTab as any} onCollapseChange={handlePanelCollapse} />
        </Panel>
      </PanelGroup>

      {/* Status Footer - always at the bottom, outside the resizable panel */}
      <StatusFooter onOpenPanel={handleOpenPanel} />
    </div>
  );
}
