import type { Metadata } from "next";
import "./globals.css";
import { ReactNode } from "react";
import { ThemeProvider } from "./components/providers/ThemeProvider";
import { TopNav } from "./components/layout/TopNav";
import { LeftNav } from "./components/layout/LeftNav";

export const metadata: Metadata = {
  title: "Agent Foundry | Modern AI Agent Development Platform",
  description: "Professional AI agent development and management platform",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="bg-bg-0 text-fg-0 antialiased">
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          enableSystem={false}
          disableTransitionOnChange={false}
        >
          <div className="flex h-screen overflow-hidden">
            <LeftNav />
            <div className="flex-1 flex flex-col overflow-hidden">
              <TopNav />
              <main className="flex-1 overflow-auto">
                {children}
              </main>
            </div>
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
}
