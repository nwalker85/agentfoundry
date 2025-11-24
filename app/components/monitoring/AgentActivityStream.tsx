/**
 * Enhanced Agent Activity Stream
 * Displays real-time agent activity with filtering, sorting, and better presentation
 */

import React, { useRef, useEffect, useState, useMemo } from 'react';
import { Activity, Filter, Trash2, ChevronDown, ChevronRight, Search, X } from 'lucide-react';
import { AgentActivity } from '@/lib/hooks/useAgentActivity';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';

type EventFilter = 'all' | 'messages' | 'tool_calls' | 'errors' | 'lifecycle';

interface AgentActivityStreamProps {
  activities: AgentActivity[];
  connected: boolean;
  onClear?: () => void;
  activeAgent?: string | null;
}

const EVENT_FILTERS: { value: EventFilter; label: string; color: string }[] = [
  { value: 'all', label: 'All', color: 'bg-fg-2' },
  { value: 'messages', label: 'Messages', color: 'bg-blue-500' },
  { value: 'tool_calls', label: 'Tools', color: 'bg-purple-500' },
  { value: 'errors', label: 'Errors', color: 'bg-red-500' },
  { value: 'lifecycle', label: 'Lifecycle', color: 'bg-green-500' },
];

export function AgentActivityStream({
  activities,
  connected,
  onClear,
  activeAgent,
}: AgentActivityStreamProps) {
  const streamRef = useRef<HTMLDivElement>(null);
  const [filter, setFilter] = useState<EventFilter>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [autoScroll, setAutoScroll] = useState(true);

  // Filter activities based on selected filter and search
  const filteredActivities = useMemo(() => {
    let filtered = activities;

    // Apply type filter
    if (filter !== 'all') {
      filtered = filtered.filter((activity) => {
        switch (filter) {
          case 'messages':
            return (
              activity.event_type === 'user_message' || activity.event_type === 'agent_message'
            );
          case 'tool_calls':
            return activity.event_type === 'tool_call';
          case 'errors':
            return activity.event_type === 'error';
          case 'lifecycle':
            return ['started', 'completed', 'interrupted', 'resumed'].includes(activity.event_type);
          default:
            return true;
        }
      });
    }

    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (activity) =>
          activity.message.toLowerCase().includes(query) ||
          activity.agent_name.toLowerCase().includes(query) ||
          activity.event_type.toLowerCase().includes(query)
      );
    }

    return filtered;
  }, [activities, filter, searchQuery]);

  // Auto-scroll to bottom when new activity arrives (if enabled)
  useEffect(() => {
    if (autoScroll && streamRef.current) {
      streamRef.current.scrollTop = streamRef.current.scrollHeight;
    }
  }, [filteredActivities, autoScroll]);

  // Detect manual scroll to disable auto-scroll
  const handleScroll = () => {
    if (streamRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = streamRef.current;
      const isAtBottom = scrollHeight - scrollTop - clientHeight < 50;
      setAutoScroll(isAtBottom);
    }
  };

  // Count events by type for badges
  const eventCounts = useMemo(() => {
    const counts = { messages: 0, tool_calls: 0, errors: 0, lifecycle: 0 };
    activities.forEach((activity) => {
      if (activity.event_type === 'user_message' || activity.event_type === 'agent_message') {
        counts.messages++;
      } else if (activity.event_type === 'tool_call') {
        counts.tool_calls++;
      } else if (activity.event_type === 'error') {
        counts.errors++;
      } else if (['started', 'completed', 'interrupted', 'resumed'].includes(activity.event_type)) {
        counts.lifecycle++;
      }
    });
    return counts;
  }, [activities]);

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-white/10">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-purple-500" />
            <h2 className="text-lg font-semibold text-fg-0">Activity Feed</h2>
          </div>
          <div className="flex items-center gap-2">
            {/* Connection Status */}
            <div
              className={cn(
                'flex items-center gap-1.5 text-xs px-2 py-1 rounded-full',
                connected ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'
              )}
            >
              <div
                className={cn(
                  'w-1.5 h-1.5 rounded-full',
                  connected ? 'bg-green-500 animate-pulse' : 'bg-red-500'
                )}
              />
              {connected ? 'Live' : 'Disconnected'}
            </div>
            {/* Clear Button */}
            {onClear && activities.length > 0 && (
              <button
                onClick={onClear}
                className="p-1.5 rounded-md hover:bg-bg-2 text-fg-2 hover:text-fg-0 transition-colors"
                title="Clear activities"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        {/* Active Agent Banner */}
        {activeAgent && (
          <div className="mb-3 px-3 py-2 bg-blue-500/10 border border-blue-500/20 rounded-lg">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
              <span className="text-xs text-fg-2">Active:</span>
              <span className="text-sm font-medium text-blue-400">{activeAgent}</span>
            </div>
          </div>
        )}

        {/* Search */}
        <div className="relative mb-3">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-fg-3" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search activities..."
            className="w-full pl-9 pr-8 py-2 bg-bg-2 border border-white/10 rounded-lg text-sm text-fg-0 placeholder:text-fg-3 focus:outline-none focus:border-blue-500/50"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-fg-3 hover:text-fg-0"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Filter Chips */}
        <div className="flex flex-wrap gap-2">
          {EVENT_FILTERS.map((f) => {
            const count =
              f.value === 'all'
                ? activities.length
                : eventCounts[f.value as keyof typeof eventCounts];
            return (
              <button
                key={f.value}
                onClick={() => setFilter(f.value)}
                className={cn(
                  'flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium transition-all',
                  filter === f.value
                    ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                    : 'bg-bg-2 text-fg-2 border border-white/10 hover:border-white/20'
                )}
              >
                <div className={cn('w-2 h-2 rounded-full', f.color)} />
                {f.label}
                {count > 0 && (
                  <span className="ml-1 px-1.5 py-0.5 bg-white/10 rounded-full text-[10px]">
                    {count}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Column Headers */}
      <div className="grid grid-cols-[60px_1fr_80px] gap-2 px-4 py-2 bg-bg-1/50 border-b border-white/5 text-xs font-medium text-fg-2">
        <div>Time</div>
        <div>Event</div>
        <div className="text-right">Agent</div>
      </div>

      {/* Activity Stream */}
      <div ref={streamRef} onScroll={handleScroll} className="flex-1 overflow-y-auto">
        {filteredActivities.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-fg-3 text-sm p-8">
            <Activity className="w-12 h-12 mb-3 opacity-20" />
            {activities.length === 0 ? (
              <>
                <p>Waiting for agent activity...</p>
                <p className="text-xs mt-1">Start a conversation to see live updates</p>
              </>
            ) : (
              <>
                <p>No matching activities</p>
                <p className="text-xs mt-1">Try adjusting your filters</p>
              </>
            )}
          </div>
        ) : (
          <div className="divide-y divide-white/5">
            {filteredActivities.map((activity, idx) => (
              <ActivityLogEntry key={idx} activity={activity} />
            ))}
          </div>
        )}
      </div>

      {/* Auto-scroll indicator */}
      {!autoScroll && filteredActivities.length > 0 && (
        <button
          onClick={() => {
            setAutoScroll(true);
            if (streamRef.current) {
              streamRef.current.scrollTop = streamRef.current.scrollHeight;
            }
          }}
          className="absolute bottom-4 right-8 px-3 py-1.5 bg-blue-500 text-white text-xs rounded-full shadow-lg hover:bg-blue-600 transition-colors"
        >
          Jump to latest
        </button>
      )}
    </div>
  );
}

interface ActivityLogEntryProps {
  activity: AgentActivity;
}

function ActivityLogEntry({ activity }: ActivityLogEntryProps) {
  const [expanded, setExpanded] = useState(false);

  const getEventIcon = (eventType: string) => {
    switch (eventType) {
      case 'started':
        return '▶';
      case 'processing':
        return '⚙';
      case 'tool_call':
        return '🔧';
      case 'completed':
        return '✓';
      case 'error':
        return '✕';
      case 'interrupted':
        return '⏸';
      case 'resumed':
        return '▶';
      case 'user_message':
        return '→';
      case 'agent_message':
        return '←';
      default:
        return '•';
    }
  };

  const getEventStyle = (eventType: string) => {
    switch (eventType) {
      case 'started':
        return 'text-blue-400 bg-blue-500/10';
      case 'processing':
        return 'text-yellow-400 bg-yellow-500/10';
      case 'tool_call':
        return 'text-purple-400 bg-purple-500/10';
      case 'completed':
        return 'text-green-400 bg-green-500/10';
      case 'error':
        return 'text-red-400 bg-red-500/10';
      case 'interrupted':
        return 'text-orange-400 bg-orange-500/10';
      case 'resumed':
        return 'text-cyan-400 bg-cyan-500/10';
      case 'user_message':
        return 'text-white bg-blue-600/20';
      case 'agent_message':
        return 'text-emerald-300 bg-emerald-500/10';
      default:
        return 'text-fg-2 bg-bg-2';
    }
  };

  const timestamp = new Date(activity.timestamp * 1000).toLocaleTimeString('en-US', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });

  const isMessage =
    activity.event_type === 'user_message' || activity.event_type === 'agent_message';
  const isToolCall = activity.event_type === 'tool_call';
  const hasDetails =
    activity.metadata &&
    (activity.metadata.input || activity.metadata.output || activity.metadata.duration);

  // Message events - special rendering
  if (isMessage) {
    return (
      <div className={cn('px-4 py-3', getEventStyle(activity.event_type))}>
        <div className="grid grid-cols-[60px_1fr_80px] gap-2 items-start">
          <span className="text-xs font-mono text-fg-3">{timestamp}</span>
          <div className="min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-sm">{getEventIcon(activity.event_type)}</span>
              <Badge variant="outline" className="text-[10px]">
                {activity.event_type === 'user_message' ? 'User' : 'Agent'}
              </Badge>
            </div>
            <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">
              {activity.message}
            </p>
          </div>
          <span className="text-xs text-fg-2 text-right truncate" title={activity.agent_name}>
            {activity.agent_name}
          </span>
        </div>
      </div>
    );
  }

  // Tool call events - expandable
  if (isToolCall && hasDetails) {
    const toolName = activity.metadata?.tool || 'Unknown Tool';
    const status = activity.metadata?.status || 'unknown';
    const duration = activity.metadata?.duration;

    return (
      <div className={cn('border-l-2 border-purple-500/50', getEventStyle(activity.event_type))}>
        <button
          onClick={() => setExpanded(!expanded)}
          className="w-full px-4 py-2 hover:bg-white/5 transition-colors"
        >
          <div className="grid grid-cols-[60px_1fr_80px] gap-2 items-center text-left">
            <span className="text-xs font-mono text-fg-3">{timestamp}</span>
            <div className="flex items-center gap-2 min-w-0">
              {expanded ? (
                <ChevronDown className="w-3 h-3 flex-shrink-0" />
              ) : (
                <ChevronRight className="w-3 h-3 flex-shrink-0" />
              )}
              <span className="text-sm">{getEventIcon(activity.event_type)}</span>
              <span className="font-medium text-sm truncate">{toolName}</span>
              {duration && <span className="text-xs text-fg-3">{duration.toFixed(2)}s</span>}
            </div>
            <span className="text-xs text-fg-2 text-right truncate">{activity.agent_name}</span>
          </div>
        </button>

        {expanded && (
          <div className="px-4 pb-3 pt-1 space-y-2 text-xs bg-bg-2/50">
            <div className="flex items-center gap-2 text-fg-2">
              <span>Status:</span>
              <Badge
                variant={
                  status === 'completed'
                    ? 'default'
                    : status === 'failed'
                      ? 'destructive'
                      : 'secondary'
                }
                className="text-[10px]"
              >
                {status}
              </Badge>
            </div>
            {activity.metadata?.input && (
              <div>
                <div className="text-purple-300 font-medium mb-1">Input:</div>
                <pre className="bg-bg-3 rounded p-2 text-fg-1 font-mono text-xs whitespace-pre-wrap break-all max-h-32 overflow-y-auto">
                  {typeof activity.metadata.input === 'string'
                    ? activity.metadata.input
                    : JSON.stringify(activity.metadata.input, null, 2)}
                </pre>
              </div>
            )}
            {activity.metadata?.output && (
              <div>
                <div className="text-purple-300 font-medium mb-1">Output:</div>
                <pre className="bg-bg-3 rounded p-2 text-fg-1 font-mono text-xs whitespace-pre-wrap break-all max-h-32 overflow-y-auto">
                  {activity.metadata.output}
                </pre>
              </div>
            )}
          </div>
        )}
      </div>
    );
  }

  // Standard events - compact row
  return (
    <div
      className={cn(
        'px-4 py-2 hover:bg-white/5 transition-colors',
        getEventStyle(activity.event_type)
      )}
    >
      <div className="grid grid-cols-[60px_1fr_80px] gap-2 items-center">
        <span className="text-xs font-mono text-fg-3">{timestamp}</span>
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-sm flex-shrink-0">{getEventIcon(activity.event_type)}</span>
          <span className="text-sm truncate">{activity.message}</span>
        </div>
        <span className="text-xs text-fg-2 text-right truncate" title={activity.agent_name}>
          {activity.agent_name}
        </span>
      </div>
    </div>
  );
}
