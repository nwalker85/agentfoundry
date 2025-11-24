'use client';

import { useEffect } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { GraphTabsProvider, useGraphTabs } from './context/GraphTabsContext';
import { GraphTabBar } from './components/GraphTabBar';

// Global key for storing unsaved changes state
const UNSAVED_CHANGES_KEY = 'graphsHasUnsavedChanges';

function GraphsLayoutInner({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { hasAnyUnsavedChanges, tabs } = useGraphTabs();

  // Sync unsaved changes state to sessionStorage for global access
  useEffect(() => {
    if (hasAnyUnsavedChanges) {
      sessionStorage.setItem(UNSAVED_CHANGES_KEY, 'true');
    } else {
      sessionStorage.removeItem(UNSAVED_CHANGES_KEY);
    }
  }, [hasAnyUnsavedChanges]);

  // Clean up on unmount (leaving graphs section)
  useEffect(() => {
    return () => {
      sessionStorage.removeItem(UNSAVED_CHANGES_KEY);
    };
  }, []);

  // Navigation guard - warn before leaving /app/graphs if there are unsaved changes
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (hasAnyUnsavedChanges) {
        e.preventDefault();
        e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
        return e.returnValue;
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [hasAnyUnsavedChanges]);

  // Check if we're on the main graphs page (gallery view)
  const isGalleryView = pathname === '/app/graphs';

  return (
    <div className="flex flex-col h-full">
      {/* Tab bar - only show when there are tabs and not on gallery */}
      {!isGalleryView && tabs.length > 0 && (
        <GraphTabBar />
      )}

      {/* Page content */}
      <div className="flex-1 overflow-hidden">
        {children}
      </div>
    </div>
  );
}

export default function GraphsLayout({ children }: { children: React.ReactNode }) {
  return (
    <GraphTabsProvider>
      <GraphsLayoutInner>{children}</GraphsLayoutInner>
    </GraphTabsProvider>
  );
}
