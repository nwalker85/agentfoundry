'use client';

import { useEffect, useState, useRef } from 'react';
import { Zap, Filter, Download, Trash2 } from 'lucide-react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useEventSubscription, Event } from '@/lib/hooks/useEventSubscription';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

export function EventsTab() {
  const { subscribe, isConnected } = useEventSubscription();
  const [events, setEvents] = useState<Event[]>([]);
  const [filter, setFilter] = useState<string>('all');
  const [autoScroll, setAutoScroll] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Subscribe to all events
  useEffect(() => {
    const unsubscribe = subscribe({ type: '*' }, (event) => {
      setEvents((prev) => [event, ...prev].slice(0, 100)); // Keep last 100 events
    });

    return unsubscribe;
  }, [subscribe]);

  // Auto-scroll to top when new events arrive
  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = 0;
    }
  }, [events, autoScroll]);

  const clearEvents = () => {
    setEvents([]);
  };

  const exportEvents = () => {
    const json = JSON.stringify(events, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `events-${new Date().toISOString()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const filteredEvents = events.filter((event) => {
    if (filter === 'all') return true;
    if (filter === 'agent') return event.type.startsWith('agent.');
    if (filter === 'domain') return event.type.startsWith('domain.');
    if (filter === 'organization') return event.type.startsWith('organization.');
    if (filter === 'deployment') return event.type.startsWith('deployment.');
    return true;
  });

  const getEventIcon = (type: string) => {
    if (type.includes('created')) return '➕';
    if (type.includes('updated')) return '✏️';
    if (type.includes('deleted')) return '🗑️';
    if (type.includes('completed')) return '✅';
    if (type.includes('failed')) return '❌';
    if (type.includes('started')) return '🚀';
    return '📌';
  };

  const getEventColor = (type: string) => {
    if (type.includes('created')) return 'text-green-400';
    if (type.includes('updated')) return 'text-blue-400';
    if (type.includes('deleted')) return 'text-red-400';
    if (type.includes('completed')) return 'text-green-400';
    if (type.includes('failed')) return 'text-red-400';
    if (type.includes('started')) return 'text-yellow-400';
    return 'text-fg-1';
  };

  return (
    <div className="h-full flex flex-col">
      {/* Controls */}
      <div className="border-b border-white/10 px-3 py-2 bg-bg-1/50 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 text-xs">
            <div
              className={`h-2 w-2 rounded-full ${isConnected ? 'bg-green-400' : 'bg-red-400'}`}
            />
            <span className="text-fg-2">{isConnected ? 'Connected' : 'Disconnected'}</span>
          </div>
          <span className="text-fg-3 text-xs">•</span>
          <span className="text-xs text-fg-2">{filteredEvents.length} events</span>
        </div>

        <div className="flex items-center gap-2">
          <Select value={filter} onValueChange={setFilter}>
            <SelectTrigger className="h-7 text-xs w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Events</SelectItem>
              <SelectItem value="agent">Agent Events</SelectItem>
              <SelectItem value="domain">Domain Events</SelectItem>
              <SelectItem value="organization">Org Events</SelectItem>
              <SelectItem value="deployment">Deployments</SelectItem>
            </SelectContent>
          </Select>

          <button
            onClick={exportEvents}
            disabled={events.length === 0}
            className="p-1.5 rounded hover:bg-bg-2 text-fg-2 hover:text-fg-0 transition-colors disabled:opacity-50"
            title="Export events"
          >
            <Download className="h-3.5 w-3.5" />
          </button>

          <button
            onClick={clearEvents}
            disabled={events.length === 0}
            className="p-1.5 rounded hover:bg-bg-2 text-fg-2 hover:text-fg-0 transition-colors disabled:opacity-50"
            title="Clear events"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      {/* Events Stream */}
      <ScrollArea className="flex-1">
        <div ref={scrollRef} className="px-3 py-2 space-y-1">
          {filteredEvents.length === 0 && (
            <div className="text-center py-8 text-xs text-fg-3">
              {isConnected ? 'Waiting for events...' : 'Connecting to event stream...'}
            </div>
          )}

          {filteredEvents.map((event, idx) => (
            <div
              key={`${event.timestamp}-${idx}`}
              className="bg-bg-2/60 rounded-md px-3 py-2 border border-white/10 hover:bg-bg-2 transition-colors"
            >
              <div className="flex items-start justify-between gap-2 mb-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm">{getEventIcon(event.type)}</span>
                  <span className={`text-xs font-medium ${getEventColor(event.type)}`}>
                    {event.type}
                  </span>
                </div>
                <span className="text-[10px] text-fg-3">
                  {new Date(event.timestamp).toLocaleTimeString()}
                </span>
              </div>

              <div className="text-xs text-fg-2 space-y-0.5 ml-6">
                {event.organization_id && (
                  <div>
                    <span className="text-fg-3">Org:</span> {event.organization_id}
                  </div>
                )}
                {event.domain_id && (
                  <div>
                    <span className="text-fg-3">Domain:</span> {event.domain_id}
                  </div>
                )}
                {event.data?.id && (
                  <div>
                    <span className="text-fg-3">ID:</span> {event.data.id}
                  </div>
                )}
                {event.data?.name && (
                  <div>
                    <span className="text-fg-3">Name:</span> {event.data.name}
                  </div>
                )}
                {event.data?.status && (
                  <div>
                    <span className="text-fg-3">Status:</span> {event.data.status}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}
