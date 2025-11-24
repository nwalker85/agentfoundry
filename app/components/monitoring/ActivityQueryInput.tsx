/**
 * Activity Query Input Component
 * Natural language query input for the Observability Agent
 */

import React, { useState, FormEvent } from 'react';
import { Search, Send, Loader2, MessageSquare } from 'lucide-react';
import { useObservabilityQuery } from '@/lib/hooks/useActivityHistory';

interface ActivityQueryInputProps {
  sessionId?: string;
  agentId?: string;
  className?: string;
}

export function ActivityQueryInput({
  sessionId,
  agentId,
  className = '',
}: ActivityQueryInputProps) {
  const [queryText, setQueryText] = useState('');
  const { response, data, isLoading, error, query } = useObservabilityQuery();
  const [showResponse, setShowResponse] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!queryText.trim() || isLoading) return;

    await query(queryText, sessionId, agentId);
    setShowResponse(true);
  };

  const exampleQueries = [
    'Show me recent errors',
    'What happened in the last session?',
    'How long did sessions take today?',
    'Search for tool calls',
  ];

  return (
    <div className={`space-y-3 ${className}`}>
      <form onSubmit={handleSubmit} className="relative">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-fg-3" />
          <input
            type="text"
            value={queryText}
            onChange={(e) => setQueryText(e.target.value)}
            placeholder="Ask about agent activity..."
            className="w-full pl-10 pr-12 py-2.5 bg-bg-2 border border-white/10 rounded-lg text-fg-1 placeholder-fg-3 focus:outline-none focus:border-purple-500/50 focus:ring-1 focus:ring-purple-500/30"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !queryText.trim()}
            className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded-md bg-purple-600 hover:bg-purple-500 disabled:bg-purple-600/50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </button>
        </div>
      </form>

      {/* Example queries */}
      {!showResponse && !isLoading && (
        <div className="flex flex-wrap gap-2">
          {exampleQueries.map((example, i) => (
            <button
              key={i}
              onClick={() => setQueryText(example)}
              className="text-xs px-2 py-1 bg-bg-2 hover:bg-bg-1 border border-white/10 rounded text-fg-3 hover:text-fg-1 transition-colors"
            >
              {example}
            </button>
          ))}
        </div>
      )}

      {/* Response display */}
      {showResponse && (response || error) && (
        <div
          className={`p-4 rounded-lg border ${error ? 'bg-red-900/20 border-red-500/30' : 'bg-purple-900/10 border-purple-500/20'}`}
        >
          <div className="flex items-start gap-2">
            <MessageSquare
              className={`w-4 h-4 mt-0.5 flex-shrink-0 ${error ? 'text-red-400' : 'text-purple-400'}`}
            />
            <div className="flex-1 min-w-0">
              {error ? (
                <p className="text-red-400 text-sm">{error}</p>
              ) : (
                <div className="text-fg-1 text-sm whitespace-pre-wrap">{response}</div>
              )}
            </div>
          </div>

          {data && !error && (
            <div className="mt-3 pt-3 border-t border-purple-500/20">
              <details className="text-xs">
                <summary className="text-fg-3 cursor-pointer hover:text-fg-2">
                  View raw data
                </summary>
                <pre className="mt-2 p-2 bg-bg-3 rounded overflow-x-auto text-fg-2 max-h-40">
                  {JSON.stringify(data, null, 2)}
                </pre>
              </details>
            </div>
          )}

          <button
            onClick={() => {
              setShowResponse(false);
              setQueryText('');
            }}
            className="mt-3 text-xs text-purple-400 hover:text-purple-300"
          >
            Clear response
          </button>
        </div>
      )}
    </div>
  );
}

export default ActivityQueryInput;
