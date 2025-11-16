'use client';

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageSquare, Mic, MicOff } from 'lucide-react';
import { VoiceOrb, type VoiceOrbState } from './components/VoiceOrb';
import { AtomIndicator } from './components/AtomIndicator';
import { MessageInput } from './components/MessageInput';
import { ConnectionStatus } from './components/ConnectionStatus';
import { VoiceChat } from '@/components/voice/VoiceChat';
import { EnhancedMessage } from '@/components/messages/EnhancedMessage';
import { useChatStore } from '@/lib/stores/chat.store';
import { Toaster, toast } from 'sonner';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Toolbar, type ToolbarAction } from '@/components/layout/Toolbar';
import { Settings, Download } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function PlaygroundPage() {
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
  const [voiceOrbState, setVoiceOrbState] = useState<VoiceOrbState>('idle');
  const [audioLevel, setAudioLevel] = useState(0);

  // LiveKit voice session state
  const [isVoiceActive, setIsVoiceActive] = useState(false);
  const [voiceSession, setVoiceSession] = useState<{
    token: string;
    serverUrl: string;
    roomName: string;
  } | null>(null);
  const [isLoadingVoice, setIsLoadingVoice] = useState(false);
  const [voiceError, setVoiceError] = useState<string | null>(null);

  // Simple boolean: is the agent currently speaking/processing?
  const isSpeaking = isProcessing || isTyping || (isVoiceActive && voiceOrbState === 'speaking');

  // Generate or retrieve user ID
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

    setIsTyping(true);
    await sendMessage(text);
    setTimeout(() => setIsTyping(false), 1000);
  };

  const startVoiceChat = async () => {
    setIsLoadingVoice(true);
    setVoiceError(null);
    setVoiceOrbState('processing');

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/voice/session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          agent_id: 'pm-agent',
          session_duration_hours: 4,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to create voice session');
      }

      const data = await response.json();
      setVoiceSession({
        token: data.token,
        serverUrl: data.livekit_url,
        roomName: data.room_name,
      });
      setIsVoiceActive(true);
      setVoiceOrbState('listening');
      toast.success('Voice chat started');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to start voice chat';
      setVoiceError(errorMessage);
      setVoiceOrbState('idle');
      toast.error(errorMessage);
      console.error('Voice session error:', err);
    } finally {
      setIsLoadingVoice(false);
    }
  };

  const endVoiceChat = async () => {
    if (voiceSession) {
      try {
        await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/api/voice/session/${voiceSession.roomName}`,
          { method: 'DELETE' }
        );
      } catch (err) {
        console.error('Failed to end session:', err);
      }
    }
    setVoiceSession(null);
    setIsVoiceActive(false);
    setVoiceOrbState('idle');
    setAudioLevel(0);
    toast.info('Voice chat ended');
  };

  const handleVoiceToggle = () => {
    if (!isVoiceActive) {
      startVoiceChat();
    } else {
      endVoiceChat();
    }
  };

  // Handle audio level updates from LiveKit
  const handleAudioLevel = (level: number) => {
    setAudioLevel(level);

    // Only update orb state if voice is active
    if (isVoiceActive) {
      // Update orb state based on audio activity
      if (level > 0.1 && voiceOrbState === 'listening') {
        setVoiceOrbState('speaking');
      } else if (level <= 0.1 && voiceOrbState === 'speaking') {
        setVoiceOrbState('listening');
      }
    }
  };

  // Update orb state based on text message processing (only when voice is not active)
  useEffect(() => {
    // Don't interfere with voice states
    if (isVoiceActive) return;

    if (isProcessing && voiceOrbState === 'idle') {
      setVoiceOrbState('processing');
    } else if (!isProcessing && voiceOrbState === 'processing') {
      setVoiceOrbState('idle');
    }
  }, [isProcessing, voiceOrbState, isVoiceActive]);

  const toolbarActions: ToolbarAction[] = [
    {
      icon: Settings,
      label: 'Settings',
      onClick: () => toast.info('Settings coming soon'),
      variant: 'ghost',
    },
    {
      icon: Download,
      label: 'Export',
      onClick: () => toast.info('Export conversation'),
      variant: 'ghost',
    },
  ];

  return (
    <div className="flex flex-col h-full bg-gradient-to-br from-bg-0 via-bg-0 to-bg-1">
      <Toaster position="top-center" richColors />

      {/* Toolbar */}
      <Toolbar actions={toolbarActions} />

      {/* Hidden LiveKit Component */}
      {isVoiceActive && voiceSession && (
        <div className="hidden">
          <VoiceChat
            token={voiceSession.token}
            serverUrl={voiceSession.serverUrl}
            roomName={voiceSession.roomName}
            userName={userId}
            agentId="pm-agent"
            onDisconnect={endVoiceChat}
            onAudioLevel={handleAudioLevel}
          />
        </div>
      )}

      {/* Main Content */}
      <main className="flex-1 overflow-hidden flex flex-col">
        <div className="flex-1 overflow-y-auto">
          <div className="max-w-4xl mx-auto px-4 py-6">

            {/* Empty State - Large Centered Atom */}
            {messages.length === 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex flex-col items-center justify-center min-h-[500px] space-y-6"
              >
                {/* Large Atom Indicator */}
                <motion.div
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.2, type: "spring" }}
                >
                  <AtomIndicator isSpeaking={isSpeaking} size="lg" className="w-32 h-32" />
                </motion.div>

                {/* Voice Button */}
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 }}
                >
                  <button
                    onClick={handleVoiceToggle}
                    disabled={isLoadingVoice}
                    className={cn(
                      "flex items-center gap-3 px-6 py-3 rounded-full font-semibold text-sm transition-all shadow-lg",
                      isVoiceActive
                        ? "bg-red-500 hover:bg-red-600 text-white"
                        : "bg-blue-600 hover:bg-blue-700 text-white",
                      isLoadingVoice && "opacity-50 cursor-not-allowed"
                    )}
                  >
                    {isLoadingVoice ? (
                      <>
                        <motion.div
                          animate={{ rotate: 360 }}
                          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                        >
                          <Mic className="w-5 h-5" />
                        </motion.div>
                        <span>Connecting...</span>
                      </>
                    ) : isVoiceActive ? (
                      <>
                        <MicOff className="w-5 h-5" />
                        <span>End Voice Chat</span>
                      </>
                    ) : (
                      <>
                        <Mic className="w-5 h-5" />
                        <span>Start Voice Chat</span>
                      </>
                    )}
                  </button>
                </motion.div>

                {/* Quick Suggestions - Compact */}
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.6 }}
                  className="grid grid-cols-1 md:grid-cols-2 gap-3 w-full max-w-2xl"
                >
                  {[
                    "Help me design a user authentication flow",
                    "Explain microservices architecture",
                    "Create a project timeline",
                    "Review API design best practices"
                  ].map((suggestion, idx) => (
                    <motion.button
                      key={idx}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.7 + idx * 0.05 }}
                      onClick={() => handleSendMessage(suggestion)}
                      className="text-left p-3 bg-bg-1/50 backdrop-blur-sm border border-white/10 rounded-lg hover:border-blue-500/50 hover:bg-bg-2/50 transition-all group"
                    >
                      <div className="flex items-start gap-3">
                        <MessageSquare className="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5 group-hover:scale-110 transition-transform" />
                        <span className="text-sm text-fg-1 group-hover:text-fg-0 transition-colors">
                          {suggestion}
                        </span>
                      </div>
                    </motion.button>
                  ))}
                </motion.div>
              </motion.div>
            )}

            {/* Messages Section */}
            {messages.length > 0 && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="space-y-4"
              >
                <AnimatePresence>
                  {messages.map((message) => (
                    <EnhancedMessage
                      key={message.id}
                      message={message}
                      showTimestamp={true}
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
                    <div className="bg-bg-1 border border-white/10 rounded-2xl rounded-bl-sm px-4 py-3">
                      <div className="flex items-center gap-1">
                        {[0, 1, 2].map((i) => (
                          <motion.div
                            key={i}
                            animate={{ opacity: [0.4, 1, 0.4] }}
                            transition={{ duration: 1.5, delay: i * 0.2, repeat: Infinity }}
                            className="w-2 h-2 bg-blue-400 rounded-full"
                          />
                        ))}
                      </div>
                    </div>
                  </motion.div>
                )}

                <div ref={messagesEndRef} />
              </motion.div>
            )}
          </div>
        </div>

        {/* Input Area */}
        <motion.footer
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="bg-bg-1/80 backdrop-blur-xl border-t border-white/10"
        >
          <div className="max-w-4xl mx-auto p-6">
            <ConnectionStatus status={connectionStatus} latency={latency} />

            <div className="mt-4">
              <MessageInput
                onSend={handleSendMessage}
                disabled={isProcessing || connectionStatus === 'disconnected'}
                placeholder={
                  connectionStatus === 'disconnected'
                    ? 'Connection lost. Reconnecting...'
                    : isProcessing
                    ? 'Processing your request...'
                    : 'Type your message or use voice...'
                }
              />
            </div>

            <div className="flex items-center justify-between mt-3">
              <p className="text-xs text-fg-2">
                Press <kbd className="px-2 py-0.5 bg-bg-2 border border-white/10 rounded text-xs">Enter</kbd> to send,
                <kbd className="ml-1 px-2 py-0.5 bg-bg-2 border border-white/10 rounded text-xs">Shift + Enter</kbd> for new line
              </p>
              {connectionStatus === 'connected' && (
                <p className="text-xs text-green-400 flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                  Connected
                </p>
              )}
            </div>
          </div>
        </motion.footer>
      </main>
    </div>
  );
}
