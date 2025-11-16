/**
 * Environment Selector Component
 * Dropdown for selecting environment (dev/staging/prod)
 */

'use client';

import { useState, useRef, useEffect } from 'react';
import { ChevronDown, Circle } from 'lucide-react';
import { cn } from '@/lib/utils';

export type Environment = 'dev' | 'staging' | 'prod';

interface EnvironmentConfig {
  label: string;
  color: string;
  dotColor: string;
}

const environmentConfig: Record<Environment, EnvironmentConfig> = {
  dev: {
    label: 'Development',
    color: 'text-blue-400',
    dotColor: 'fill-blue-500',
  },
  staging: {
    label: 'Staging',
    color: 'text-yellow-400',
    dotColor: 'fill-yellow-500',
  },
  prod: {
    label: 'Production',
    color: 'text-green-400',
    dotColor: 'fill-green-500',
  },
};

interface EnvironmentSelectorProps {
  current: Environment;
  onChange: (env: Environment) => void;
}

export function EnvironmentSelector({ current, onChange }: EnvironmentSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const currentConfig = environmentConfig[current];

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen]);

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          "flex items-center gap-2 px-3 py-1.5 rounded-md",
          "hover:bg-gray-800 transition-colors",
          isOpen && "bg-gray-800"
        )}
      >
        <Circle className={cn("w-2 h-2", currentConfig.dotColor)} />
        <span className={cn("text-sm font-medium", currentConfig.color)}>
          {currentConfig.label}
        </span>
        <ChevronDown
          className={cn(
            "w-4 h-4 text-gray-400 transition-transform",
            isOpen && "rotate-180"
          )}
        />
      </button>

      {isOpen && (
        <div className="absolute top-full mt-1 left-0 w-48 bg-gray-900 border border-gray-700 rounded-lg shadow-xl z-50">
          {(Object.keys(environmentConfig) as Environment[]).map((env) => {
            const config = environmentConfig[env];
            return (
              <button
                key={env}
                onClick={() => {
                  onChange(env);
                  setIsOpen(false);
                }}
                className={cn(
                  "w-full px-3 py-2.5 flex items-center gap-3",
                  "hover:bg-gray-800 transition-colors",
                  current === env && "bg-gray-800"
                )}
              >
                <Circle className={cn("w-2 h-2", config.dotColor)} />
                <span className={cn("text-sm font-medium", config.color)}>
                  {config.label}
                </span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
