'use client';

import { useEffect, useState, useRef } from 'react';
import {
  FileText,
  Search,
  Download,
  Trash2,
  AlertCircle,
  Info,
  AlertTriangle,
  XCircle,
} from 'lucide-react';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

type LogLevel = 'INFO' | 'WARN' | 'ERROR' | 'DEBUG' | 'ALL';

interface LogEntry {
  timestamp: string;
  level: LogLevel;
  message: string;
  module?: string;
}

export function LogsTab() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [filter, setFilter] = useState<LogLevel>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [autoScroll, setAutoScroll] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Poll logs from backend
  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const res = await fetch(`${apiBase}/api/system/logs?limit=100`);
        if (res.ok) {
          const data = await res.json();
          setLogs(data.logs || []);
        }
      } catch (e) {
        console.error('Failed to fetch logs:', e);
      }
    };

    fetchLogs();
    const interval = setInterval(fetchLogs, 3000); // Poll every 3s
    return () => clearInterval(interval);
  }, []);

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs, autoScroll]);

  const clearLogs = () => {
    setLogs([]);
  };

  const exportLogs = () => {
    const text = logs
      .map(
        (log) =>
          `[${log.timestamp}] [${log.level}] ${log.module ? `[${log.module}] ` : ''}${log.message}`
      )
      .join('\n');
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `logs-${new Date().toISOString()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const filteredLogs = logs.filter((log) => {
    // Filter by level
    if (filter !== 'ALL' && log.level !== filter) return false;

    // Filter by search query
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      return (
        log.message.toLowerCase().includes(query) ||
        log.module?.toLowerCase().includes(query) ||
        log.level.toLowerCase().includes(query)
      );
    }

    return true;
  });

  const getLevelIcon = (level: LogLevel) => {
    switch (level) {
      case 'INFO':
        return <Info className="h-3.5 w-3.5 text-blue-400" />;
      case 'WARN':
        return <AlertTriangle className="h-3.5 w-3.5 text-yellow-400" />;
      case 'ERROR':
        return <XCircle className="h-3.5 w-3.5 text-red-400" />;
      case 'DEBUG':
        return <AlertCircle className="h-3.5 w-3.5 text-fg-3" />;
      default:
        return <Info className="h-3.5 w-3.5 text-fg-3" />;
    }
  };

  const getLevelColor = (level: LogLevel) => {
    switch (level) {
      case 'INFO':
        return 'text-blue-400';
      case 'WARN':
        return 'text-yellow-400';
      case 'ERROR':
        return 'text-red-400';
      case 'DEBUG':
        return 'text-fg-3';
      default:
        return 'text-fg-2';
    }
  };

  const getLevelBg = (level: LogLevel) => {
    switch (level) {
      case 'ERROR':
        return 'bg-red-500/10 border-red-500/30';
      case 'WARN':
        return 'bg-yellow-500/10 border-yellow-500/30';
      default:
        return 'bg-bg-2/60 border-white/10';
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* Controls */}
      <div className="border-b border-white/10 px-3 py-2 bg-bg-1/50 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 flex-1">
          <div className="relative flex-1 max-w-xs">
            <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-fg-3" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search logs..."
              className="w-full h-7 pl-7 pr-2 text-xs bg-bg-2/80 border border-white/10 rounded text-fg-0 placeholder:text-fg-3 focus:outline-none focus:ring-1 focus:ring-blue-500/70"
            />
          </div>

          <Select value={filter} onValueChange={(v) => setFilter(v as LogLevel)}>
            <SelectTrigger className="h-7 text-xs w-24">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">All</SelectItem>
              <SelectItem value="DEBUG">Debug</SelectItem>
              <SelectItem value="INFO">Info</SelectItem>
              <SelectItem value="WARN">Warn</SelectItem>
              <SelectItem value="ERROR">Error</SelectItem>
            </SelectContent>
          </Select>

          <span className="text-xs text-fg-2">{filteredLogs.length} logs</span>
        </div>

        <div className="flex items-center gap-2">
          <label className="flex items-center gap-1.5 text-xs text-fg-2 cursor-pointer">
            <input
              type="checkbox"
              checked={autoScroll}
              onChange={(e) => setAutoScroll(e.target.checked)}
              className="rounded"
            />
            Auto-scroll
          </label>

          <button
            onClick={exportLogs}
            disabled={logs.length === 0}
            className="p-1.5 rounded hover:bg-bg-2 text-fg-2 hover:text-fg-0 transition-colors disabled:opacity-50"
            title="Export logs"
          >
            <Download className="h-3.5 w-3.5" />
          </button>

          <button
            onClick={clearLogs}
            disabled={logs.length === 0}
            className="p-1.5 rounded hover:bg-bg-2 text-fg-2 hover:text-fg-0 transition-colors disabled:opacity-50"
            title="Clear logs"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      {/* Logs Stream */}
      <ScrollArea className="flex-1">
        <div ref={scrollRef} className="px-3 py-2 space-y-0.5 font-mono">
          {filteredLogs.length === 0 && (
            <div className="text-center py-8 text-xs text-fg-3">
              {logs.length === 0 ? 'No logs available' : 'No logs match your filter'}
            </div>
          )}

          {filteredLogs.map((log, idx) => (
            <div
              key={`${log.timestamp}-${idx}`}
              className={`rounded px-2 py-1.5 border ${getLevelBg(log.level)} hover:bg-bg-2 transition-colors`}
            >
              <div className="flex items-start gap-2 text-xs">
                <span className="text-[10px] text-fg-3 whitespace-nowrap">
                  {new Date(log.timestamp).toLocaleTimeString()}
                </span>
                <div className="flex items-center gap-1.5 min-w-[60px]">
                  {getLevelIcon(log.level)}
                  <span className={`text-[10px] font-semibold ${getLevelColor(log.level)}`}>
                    {log.level}
                  </span>
                </div>
                {log.module && (
                  <span className="text-[10px] text-fg-3 min-w-[80px] truncate">
                    [{log.module}]
                  </span>
                )}
                <span className="text-xs text-fg-0 flex-1 break-all">{log.message}</span>
              </div>
            </div>
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}
