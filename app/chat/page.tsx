'use client';

import { useState, useEffect, useRef } from 'react';
import { MessageThread } from './components/MessageThread';
import { MessageInput } from './components/MessageInput';
import { ConnectionStatus } from './components/ConnectionStatus';
import { useChatStore } from '@/lib/stores/chat.store';

export default function ChatPage() {
  const { 
    messages, 
    connectionStatus, 
    sendMessage, 
    isProcessing 
  } = useChatStore();
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async (text: string) => {
    if (!text.trim() || isProcessing) return;
    await sendMessage(text);
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b px-6 py-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <h1 className="text-xl font-semibold text-gray-900">
            Engineering Department Chat
          </h1>
          <ConnectionStatus status={connectionStatus} />
        </div>
      </header>

      {/* Messages Area */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto py-4">
          <MessageThread messages={messages} isProcessing={isProcessing} />
          <div ref={messagesEndRef} />
        </div>
      </main>

      {/* Input Area */}
      <footer className="bg-white border-t">
        <div className="max-w-4xl mx-auto p-4">
          <MessageInput 
            onSend={handleSendMessage} 
            disabled={isProcessing || connectionStatus === 'disconnected'}
            placeholder={
              connectionStatus === 'disconnected' 
                ? 'Connection lost. Reconnecting...' 
                : 'Describe what you want to build...'
            }
          />
        </div>
      </footer>
    </div>
  );
}
