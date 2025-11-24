'use client';

import { formatDistanceToNow } from 'date-fns';
import type { ChatMessage } from '@/lib/types/chat';

interface MessageProps {
  message: ChatMessage;
}

export function Message({ message }: MessageProps) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`
          max-w-2xl px-4 py-3 rounded-lg
          ${isUser ? 'bg-blue-600 text-white' : 'bg-white border border-gray-200 text-gray-900'}
        `}
      >
        {/* Message Header */}
        <div className={`text-xs mb-1 ${isUser ? 'text-blue-100' : 'text-gray-500'}`}>
          {isUser ? 'You' : 'PM Agent'} •{' '}
          {formatDistanceToNow(new Date(message.timestamp), { addSuffix: true })}
        </div>

        {/* Message Content */}
        <div className="whitespace-pre-wrap break-words">{message.content}</div>

        {/* Artifacts/Tools Results */}
        {message.artifacts && message.artifacts.length > 0 && (
          <div className="mt-3 space-y-2">
            {message.artifacts.map((artifact, idx) => (
              <div
                key={idx}
                className={`
                  text-sm p-2 rounded
                  ${isUser ? 'bg-blue-700' : 'bg-gray-50 border border-gray-200'}
                `}
              >
                {artifact.type === 'story' && (
                  <div className="flex items-center justify-between">
                    <span className="font-medium">📝 Story Created</span>
                    {artifact.data.url && (
                      <a
                        href={artifact.data.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className={`
                          underline hover:no-underline
                          ${isUser ? 'text-blue-200' : 'text-blue-600'}
                        `}
                      >
                        View in Notion →
                      </a>
                    )}
                  </div>
                )}
                {artifact.type === 'issue' && (
                  <div className="flex items-center justify-between">
                    <span className="font-medium">🎯 Issue Created</span>
                    {artifact.data.url && (
                      <a
                        href={artifact.data.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className={`
                          underline hover:no-underline
                          ${isUser ? 'text-blue-200' : 'text-blue-600'}
                        `}
                      >
                        View in GitHub →
                      </a>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Error State */}
        {message.error && (
          <div className="mt-2 text-sm text-red-600 bg-red-50 p-2 rounded">⚠️ {message.error}</div>
        )}
      </div>
    </div>
  );
}
