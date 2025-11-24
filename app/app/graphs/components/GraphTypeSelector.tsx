'use client';

import React from 'react';
import { GitBranch, Workflow, Shield } from 'lucide-react';

export type GraphType = 'user' | 'channel' | 'system';

interface GraphTypeSelectorProps {
  selectedType: GraphType;
  onTypeChange: (type: GraphType) => void;
  counts?: {
    user: number;
    channel: number;
    system: number;
  };
}

export default function GraphTypeSelector({
  selectedType,
  onTypeChange,
  counts,
}: GraphTypeSelectorProps) {
  const types: Array<{
    key: GraphType;
    label: string;
    description: string;
    icon: React.ReactNode;
  }> = [
    {
      key: 'user',
      label: 'User Agent',
      description: 'Custom agents for your organization',
      icon: <GitBranch className="w-5 h-5" />,
    },
    {
      key: 'channel',
      label: 'Channel Workflow',
      description: 'Multi-agent workflows for chat, voice, and API',
      icon: <Workflow className="w-5 h-5" />,
    },
    {
      key: 'system',
      label: 'System Agent',
      description: 'Core platform agents (Supervisor, IO, Context)',
      icon: <Shield className="w-5 h-5" />,
    },
  ];

  return (
    <div className="flex gap-3">
      {types.map((type) => {
        const isSelected = selectedType === type.key;
        const count = counts?.[type.key] || 0;

        return (
          <button
            key={type.key}
            onClick={() => onTypeChange(type.key)}
            className={`
              flex items-center gap-3 px-4 py-3 rounded-lg border-2 transition-all
              ${
                isSelected
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                  : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
              }
            `}
          >
            <div
              className={`
              ${
                isSelected ? 'text-blue-600 dark:text-blue-400' : 'text-gray-500 dark:text-gray-400'
              }
            `}
            >
              {type.icon}
            </div>
            <div className="flex flex-col items-start">
              <div className="flex items-center gap-2">
                <span
                  className={`
                  font-medium text-sm
                  ${
                    isSelected
                      ? 'text-blue-900 dark:text-blue-100'
                      : 'text-gray-900 dark:text-gray-100'
                  }
                `}
                >
                  {type.label}
                </span>
                {counts && (
                  <span
                    className={`
                    text-xs px-2 py-0.5 rounded-full
                    ${
                      isSelected
                        ? 'bg-blue-100 text-blue-700 dark:bg-blue-800 dark:text-blue-200'
                        : 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400'
                    }
                  `}
                  >
                    {count}
                  </span>
                )}
              </div>
              <span className="text-xs text-gray-500 dark:text-gray-400">{type.description}</span>
            </div>
          </button>
        );
      })}
    </div>
  );
}
