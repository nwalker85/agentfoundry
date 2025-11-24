'use client';

import { useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';

interface UseNavigationGuardOptions {
  when: boolean;
  message?: string;
  onBeforeUnload?: () => void;
}

/**
 * Hook to warn users about unsaved changes when navigating away
 *
 * @param when - Condition to enable the guard (e.g., hasUnsavedChanges)
 * @param message - Custom message for confirmation dialog
 * @param onBeforeUnload - Callback before page unload
 */
export function useNavigationGuard({
  when,
  message = 'You have unsaved changes. Are you sure you want to leave?',
  onBeforeUnload,
}: UseNavigationGuardOptions) {
  // Handle browser navigation (back/forward, close tab, refresh)
  useEffect(() => {
    if (!when) return;

    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      e.preventDefault();
      // Modern browsers ignore custom message but still show dialog
      e.returnValue = message;
      onBeforeUnload?.();
      return message;
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [when, message, onBeforeUnload]);

  // Return a function to check before programmatic navigation
  const confirmNavigation = useCallback(() => {
    if (!when) return true;
    return confirm(message);
  }, [when, message]);

  return { confirmNavigation };
}
