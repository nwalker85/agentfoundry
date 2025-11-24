import { ReactNode } from 'react';
import { LeftNav } from '@/components/layout/LeftNav';
import { TopNav } from '@/components/layout/TopNav';
import { MainLayout } from '@/components/layout/MainLayout';

export default function AppShellLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex h-screen overflow-hidden">
      <LeftNav />
      <div className="flex-1 flex flex-col min-h-0">
        <TopNav />
        <MainLayout>{children}</MainLayout>
      </div>
    </div>
  );
}
