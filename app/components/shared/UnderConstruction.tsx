'use client';

import { Construction } from 'lucide-react';
import { cn } from '@/lib/utils';

interface UnderConstructionProps {
  className?: string;
  message?: string;
}

export function UnderConstruction({
  className,
  message = 'This page is under construction and may have limited functionality.',
}: UnderConstructionProps) {
  return (
    <div
      className={cn(
        'flex items-center gap-3 px-4 py-3 bg-amber-500/10 border border-amber-500/30 rounded-lg text-amber-200 text-sm',
        className
      )}
    >
      <Construction className="w-5 h-5 flex-shrink-0 text-amber-400" />
      <span>{message}</span>
    </div>
  );
}
