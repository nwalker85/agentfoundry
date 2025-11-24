'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function ForgePage() {
  const router = useRouter();

  useEffect(() => {
    // Redirect to the CIBC agent graph as default
    // TODO: Make this configurable or show a graph selection page
    router.push('/app/graphs/cibc-card-activation');
  }, [router]);

  return (
    <div className="flex items-center justify-center h-screen bg-bg-0">
      <div className="text-fg-2">Redirecting to Forge...</div>
    </div>
  );
}
