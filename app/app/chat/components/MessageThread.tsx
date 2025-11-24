'use client';

import { Message } from './Message';
import { LoadingMessage } from './LoadingMessage';
import type { ChatMessage } from '@/lib/types/chat';

interface MessageThreadProps {
  messages: ChatMessage[];
  isProcessing?: boolean;
}

export function MessageThread({ messages, isProcessing }: MessageThreadProps) {
  if (messages.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-gray-500">
        <svg className="w-12 h-12 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
          />
        </svg>
        <p className="text-center">
          Start a conversation by describing what you&apos;d like to build.
        </p>
        <p className="text-sm text-gray-400 mt-2">
          I&apos;ll help you create stories and issues for your engineering team.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4 px-4">
      {messages.map((message) => (
        <Message key={message.id} message={message} />
      ))}
      {isProcessing && <LoadingMessage />}
    </div>
  );
}
