'use client';

import { useEffect, useState, useRef } from 'react';
import { usePathname, useSearchParams } from 'next/navigation';
import { cn } from '@/lib/utils';

/**
 * Global navigation progress indicator.
 * Shows a thin progress bar at the top of the viewport during page transitions.
 */
export function NavigationProgress() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [isNavigating, setIsNavigating] = useState(false);
  const [progress, setProgress] = useState(0);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    // When pathname or search params change, the navigation is complete
    // Reset the progress bar
    if (isNavigating) {
      // Complete the progress bar
      setProgress(100);

      // Hide after animation completes
      timeoutRef.current = setTimeout(() => {
        setIsNavigating(false);
        setProgress(0);
      }, 200);
    }

    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [pathname, searchParams]);

  // Listen for click events on links to start the progress bar
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      const link = target.closest('a');

      if (!link) return;

      const href = link.getAttribute('href');
      if (!href) return;

      // Skip external links, hash links, and same-page links
      if (
        href.startsWith('http') ||
        href.startsWith('#') ||
        href === pathname ||
        link.target === '_blank'
      ) {
        return;
      }

      // Start the progress bar
      setIsNavigating(true);
      setProgress(0);

      // Animate progress from 0 to ~80% over time
      let currentProgress = 0;
      intervalRef.current = setInterval(() => {
        currentProgress += Math.random() * 15;
        if (currentProgress >= 80) {
          currentProgress = 80 + Math.random() * 5; // Slow down near 80%
          if (intervalRef.current) clearInterval(intervalRef.current);
        }
        setProgress(Math.min(currentProgress, 85));
      }, 100);
    };

    document.addEventListener('click', handleClick);
    return () => {
      document.removeEventListener('click', handleClick);
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [pathname]);

  if (!isNavigating && progress === 0) return null;

  return (
    <div
      className="fixed top-0 left-0 right-0 z-[9999] h-[3px] bg-transparent pointer-events-none"
      role="progressbar"
      aria-valuenow={progress}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label="Page loading"
    >
      <div
        className={cn(
          'h-full bg-gradient-to-r from-blue-500 via-blue-400 to-cyan-400 transition-all duration-200 ease-out',
          progress === 100 && 'opacity-0'
        )}
        style={{ width: `${progress}%` }}
      />
      {/* Glow effect */}
      <div
        className={cn(
          'absolute right-0 top-0 h-full w-24 bg-gradient-to-l from-cyan-400/50 to-transparent blur-sm transition-opacity duration-200',
          progress === 100 && 'opacity-0'
        )}
        style={{
          transform: `translateX(${progress < 100 ? '0' : '100%'})`,
        }}
      />
    </div>
  );
}
