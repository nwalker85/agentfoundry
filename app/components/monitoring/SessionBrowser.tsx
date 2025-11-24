/**
 * Session Browser Component
 * Displays a list of recent sessions with summary information
 */

import React from 'react';
import { Clock, Activity, AlertCircle, Users } from 'lucide-react';
import { useRecentSessions } from '@/lib/hooks/useActivityHistory';

interface SessionBrowserProps {
  onSelectSession: (sessionId: string) => void;
  selectedSessionId?: string | null;
}

export function SessionBrowser({ onSelectSession, selectedSessionId }: SessionBrowserProps) {
  const { sessions, isLoading, error, refresh } = useRecentSessions(20);

  if (isLoading && sessions.length === 0) {
    return (
      <div className="p-4 text-center text-fg-3">
        <div className="animate-spin w-6 h-6 border-2 border-purple-500 border-t-transparent rounded-full mx-auto mb-2"></div>
        Loading sessions...
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 text-center text-red-400">
        <AlertCircle className="w-6 h-6 mx-auto mb-2" />
        {error}
        <button
          onClick={refresh}
          className="block mx-auto mt-2 text-sm text-purple-400 hover:text-purple-300"
        >
          Retry
        </button>
      </div>
    );
  }

  if (sessions.length === 0) {
    return (
      <div className="p-4 text-center text-fg-3">
        <Activity className="w-8 h-8 mx-auto mb-2 opacity-30" />
        <p>No sessions found</p>
        <p className="text-xs mt-1">Sessions will appear here after agent activity</p>
      </div>
    );
  }

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
    return `${Math.round(seconds / 3600)}h`;
  };

  const formatTime = (isoString: string) => {
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.round(diffMs / 60000);

    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.round(diffMins / 60)}h ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between px-2 py-1">
        <h3 className="text-sm font-semibold text-fg-1">Recent Sessions</h3>
        <button
          onClick={refresh}
          className="text-xs text-purple-400 hover:text-purple-300"
          disabled={isLoading}
        >
          {isLoading ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      <div className="space-y-1 max-h-96 overflow-y-auto">
        {sessions.map((session) => (
          <button
            key={session.session_id}
            onClick={() => onSelectSession(session.session_id)}
            className={`w-full text-left p-3 rounded-lg transition-colors ${
              selectedSessionId === session.session_id
                ? 'bg-purple-900/30 border border-purple-500/50'
                : 'bg-bg-2 hover:bg-bg-1 border border-transparent'
            }`}
          >
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1 min-w-0">
                <div className="text-xs font-mono text-fg-2 truncate">{session.session_id}</div>
                <div className="flex items-center gap-3 mt-1 text-xs text-fg-3">
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {formatDuration(session.duration_seconds)}
                  </span>
                  <span className="flex items-center gap-1">
                    <Activity className="w-3 h-3" />
                    {session.activity_count}
                  </span>
                  {session.error_count > 0 && (
                    <span className="flex items-center gap-1 text-red-400">
                      <AlertCircle className="w-3 h-3" />
                      {session.error_count}
                    </span>
                  )}
                </div>
              </div>
              <div className="text-xs text-fg-3 whitespace-nowrap">
                {formatTime(session.ended_at)}
              </div>
            </div>

            {session.agents.length > 0 && (
              <div className="flex items-center gap-1 mt-2 flex-wrap">
                <Users className="w-3 h-3 text-fg-3" />
                {session.agents.slice(0, 3).map((agent, i) => (
                  <span key={i} className="text-xs px-1.5 py-0.5 bg-bg-3 rounded text-fg-2">
                    {agent}
                  </span>
                ))}
                {session.agents.length > 3 && (
                  <span className="text-xs text-fg-3">+{session.agents.length - 3} more</span>
                )}
              </div>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}

export default SessionBrowser;
