'use client';

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageInput } from './components/MessageInput';
import { ConnectionStatus } from './components/ConnectionStatus';
import { VoiceToggle } from './components/VoiceToggle';
import { EnhancedMessage } from '@/components/messages/EnhancedMessage';
import { useChatStore } from '@/lib/stores/chat.store';
import { Toaster, toast } from 'sonner';
import { Sparkles, MessageSquare } from 'lucide-react';
import { ThemeToggle } from '@/components/ThemeToggle';

export default function ChatPage() {
  const { 
    messages, 
    connectionStatus, 
    sendMessage, 
    isProcessing,
    error,
    latency
  } = useChatStore();
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [isTyping, setIsTyping] = useState(false);

  // Generate or retrieve user ID (for demo, using localStorage)
  const [userId] = useState(() => {
    if (typeof window !== 'undefined') {
      let id = localStorage.getItem('agentfoundry_user_id');
      if (!id) {
        id = `user_${Math.random().toString(36).substring(2, 15)}`;
        localStorage.setItem('agentfoundry_user_id', id);
      }
      return id;
    }
    return 'user_default';
  });

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Show error toasts
  useEffect(() => {
    if (error) {
      toast.error(error);
    }
  }, [error]);

  const handleSendMessage = async (text: string) => {
    if (!text.trim() || isProcessing) return;
    
    // Simulate typing indicator
    setIsTyping(true);
    await sendMessage(text);
    
    // Keep typing indicator for a bit after sending
    setTimeout(() => setIsTyping(false), 1000);
  };

  // Group consecutive messages from the same sender
  const groupedMessages = messages.reduce((acc, message, index) => {
    const prevMessage = index > 0 ? messages[index - 1] : null;
    const isGrouped = prevMessage && 
      prevMessage.role === message.role &&
      new Date(message.timestamp).getTime() - new Date(prevMessage.timestamp).getTime() < 60000; // Within 1 minute
    
    acc.push({ ...message, isGrouped });
    return acc;
  }, [] as Array<any>);

  return (
    <div className="flex flex-col h-screen bg-gradient-to-b from-gray-50 to-white dark:from-gray-900 dark:to-gray-800">
      <Toaster position="top-center" richColors />
      
      {/* Header */}
      <motion.header 
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="bg-white dark:bg-gray-800 border-b dark:border-gray-700 shadow-sm px-6 py-4"
      >
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                Engineering Department
              </h1>
              <p className="text-xs text-gray-500 dark:text-gray-400">AI-Powered Development Assistant</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <ConnectionStatus status={connectionStatus} latency={latency} />
            <ThemeToggle />
          </div>
        </div>
      </motion.header>

      {/* Messages Area */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto py-4 px-4">
          {/* Empty State */}
          {messages.length === 0 && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="flex flex-col items-center justify-center min-h-[400px] text-center"
            >
              <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-full mb-4">
                <MessageSquare className="w-8 h-8 text-blue-600 dark:text-blue-400" />
              </div>
              <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
                Start a Conversation
              </h2>
              <p className="text-gray-600 dark:text-gray-300 mb-6 max-w-md">
                Describe what you want to build and I'll help you create stories, 
                manage your backlog, and coordinate development tasks.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl">
                {[
                  "Create a user authentication system with OAuth",
                  "Add rate limiting to our API endpoints",
                  "Build a real-time notification system",
                  "Implement data export functionality"
                ].map((suggestion, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSendMessage(suggestion)}
                    className="text-left p-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:border-blue-300 dark:hover:border-blue-600 hover:shadow-sm transition-all duration-200"
                  >
                    <span className="text-sm text-gray-700 dark:text-gray-300">{suggestion}</span>
                  </button>
                ))}
              </div>
            </motion.div>
          )}

          {/* Message Thread */}
          <AnimatePresence>
            {groupedMessages.map((message) => (
              <EnhancedMessage 
                key={message.id}
                message={message}
                isGrouped={message.isGrouped}
                showTimestamp={!message.isGrouped}
              />
            ))}
          </AnimatePresence>

          {/* Typing Indicator */}
          {(isProcessing || isTyping) && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="flex justify-start mt-4"
            >
              <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-2xl rounded-bl-sm px-4 py-3">
                <div className="flex items-center gap-1">
                  <motion.div
                    animate={{ opacity: [0.4, 1, 0.4] }}
                    transition={{ duration: 1.5, repeat: Infinity }}
                    className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full"
                  />
                  <motion.div
                    animate={{ opacity: [0.4, 1, 0.4] }}
                    transition={{ duration: 1.5, delay: 0.2, repeat: Infinity }}
                    className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full"
                  />
                  <motion.div
                    animate={{ opacity: [0.4, 1, 0.4] }}
                    transition={{ duration: 1.5, delay: 0.4, repeat: Infinity }}
                    className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full"
                  />
                </div>
              </div>
            </motion.div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </main>

      {/* Input Area */}
      <motion.footer 
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="bg-white dark:bg-gray-800 border-t dark:border-gray-700 shadow-lg"
      >
        <div className="max-w-4xl mx-auto p-4">
          {/* Voice Toggle */}
          <VoiceToggle userId={userId} agentId="pm-agent" />
          
          <MessageInput 
            onSend={handleSendMessage} 
            disabled={isProcessing || connectionStatus === 'disconnected'}
            placeholder={
              connectionStatus === 'disconnected' 
                ? 'Connection lost. Reconnecting...' 
                : isProcessing
                ? 'Processing your request...'
                : 'Describe what you want to build...'
            }
          />
          <div className="flex items-center justify-between mt-2">
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Press <kbd className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-700 rounded text-xs">Enter</kbd> to send, 
              <kbd className="ml-1 px-1.5 py-0.5 bg-gray-100 dark:bg-gray-700 rounded text-xs">Shift + Enter</kbd> for new line
            </p>
            {connectionStatus === 'connected' && (
              <p className="text-xs text-green-600 dark:text-green-400 flex items-center gap-1">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                Ready
              </p>
            )}
          </div>
        </div>
      </motion.footer>
    </div>
  );
}
