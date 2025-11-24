import type { Metadata } from 'next';
import './globals.css';
import { ReactNode } from 'react';
import { Providers } from './providers';

export const metadata: Metadata = {
  title: 'Agent Foundry | Modern AI Agent Development Platform',
  description: 'Professional AI agent development and management platform',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="bg-bg-0 text-fg-0 antialiased">
        <Providers>
          <div id="root-content" className="min-h-screen">
            {/* Skip to main content link for keyboard navigation - WCAG 2.4.1 */}
            <a
              href="#main-content"
              className="sr-only sr-only-focusable fixed top-4 left-4 z-50 bg-blue-600 text-white px-4 py-2 rounded-lg font-semibold shadow-lg"
            >
              Skip to content
            </a>
            {children}
          </div>
        </Providers>
      </body>
    </html>
  );
}
