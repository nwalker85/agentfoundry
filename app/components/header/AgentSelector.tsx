/**
 * Agent Selector Component
 * Dropdown with search for selecting agents
 */

'use client';

import { useState, useRef, useEffect } from 'react';
import { ChevronDown, Check, Plus, Search } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { Agent } from '@/types';

interface AgentSelectorProps {
  agents: Agent[];
  selectedAgent?: Agent | null;
  onSelect: (agent: Agent) => void;
  onCreateNew?: () => void;
}

export function AgentSelector({
  agents,
  selectedAgent,
  onSelect,
  onCreateNew,
}: AgentSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const dropdownRef = useRef<HTMLDivElement>(null);

  const filteredAgents = agents.filter(
    (agent) =>
      agent.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      agent.display_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

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
          'flex items-center gap-2 px-3 py-1.5 rounded-md',
          'hover:bg-gray-800 transition-colors min-w-[200px]',
          isOpen && 'bg-gray-800'
        )}
      >
        <div className="flex items-center flex-1 min-w-0">
          <div
            className={cn(
              'w-2 h-2 rounded-full mr-2 flex-shrink-0',
              selectedAgent?.status === 'active' ? 'bg-green-500' : 'bg-gray-500'
            )}
          />
          <span className="text-sm text-white truncate">
            {selectedAgent?.display_name || selectedAgent?.name || 'Select Agent'}
          </span>
        </div>
        <ChevronDown
          className={cn(
            'w-4 h-4 text-gray-400 transition-transform flex-shrink-0',
            isOpen && 'rotate-180'
          )}
        />
      </button>

      {isOpen && (
        <div className="absolute top-full mt-1 left-0 w-80 bg-gray-900 border border-gray-700 rounded-lg shadow-xl z-50">
          {/* Search */}
          <div className="p-3 border-b border-gray-700">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search agents..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-3 py-2 bg-gray-800 text-white rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 border border-gray-700"
                autoFocus
              />
            </div>
          </div>

          {/* Agent List */}
          <div className="max-h-64 overflow-y-auto">
            {filteredAgents.length === 0 ? (
              <div className="px-3 py-8 text-gray-500 text-sm text-center">No agents found</div>
            ) : (
              filteredAgents.map((agent) => (
                <button
                  key={agent.id}
                  onClick={() => {
                    onSelect(agent);
                    setIsOpen(false);
                    setSearchTerm('');
                  }}
                  className="w-full px-3 py-2.5 flex items-center gap-3 hover:bg-gray-800 transition-colors"
                >
                  <div
                    className={cn(
                      'w-2 h-2 rounded-full flex-shrink-0',
                      agent.status === 'active' ? 'bg-green-500' : 'bg-gray-500'
                    )}
                  />
                  <div className="flex-1 text-left min-w-0">
                    <div className="text-sm text-white truncate">{agent.display_name}</div>
                    <div className="text-xs text-gray-500 truncate">{agent.name}</div>
                  </div>
                  {selectedAgent?.id === agent.id && (
                    <Check className="w-4 h-4 text-blue-500 flex-shrink-0" />
                  )}
                </button>
              ))
            )}
          </div>

          {/* Create New */}
          {onCreateNew && (
            <div className="p-3 border-t border-gray-700">
              <button
                onClick={() => {
                  onCreateNew();
                  setIsOpen(false);
                  setSearchTerm('');
                }}
                className="w-full px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-sm transition-colors flex items-center justify-center gap-2"
              >
                <Plus className="w-4 h-4" />
                Create New Agent
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
