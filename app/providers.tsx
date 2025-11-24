'use client';

import { ReactNode, useEffect, Suspense } from 'react';
import { SessionProvider } from '@/components/providers/SessionProvider';
import { ThemeProvider } from '@/components/providers/ThemeProvider';
import { Toaster } from '@/components/ui/sonner';
import { NavigationProgress } from '@/components/layout/NavigationProgress';

const UI_VERSION = '0.8.0';

export function Providers({ children }: { children: ReactNode }) {
  useEffect(() => {
    // Log UI version on initialization
    console.log(
      `%c🚀 Agent Foundry UI v${UI_VERSION}`,
      'color: #3b82f6; font-size: 16px; font-weight: bold; padding: 4px 8px; background: #1e293b; border-radius: 4px;'
    );
    console.log(`%cBuild: ${new Date().toISOString()}`, 'color: #6b7280; font-size: 12px;');
  }, []);

  return (
    <SessionProvider>
      <ThemeProvider
        attribute="class"
        defaultTheme="dark"
        enableSystem={false}
        disableTransitionOnChange={false}
      >
        <Suspense fallback={null}>
          <NavigationProgress />
        </Suspense>
        {children}
        <Toaster richColors position="top-right" />
      </ThemeProvider>
    </SessionProvider>
  );
}
