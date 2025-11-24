'use client';

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, MicOff, Bot } from 'lucide-react';
import { VoiceOrb, type VoiceOrbState } from './components/VoiceOrb';
import { AtomIndicator } from './components/AtomIndicator';
import { MessageInput } from './components/MessageInput';
import { ConnectionStatus } from './components/ConnectionStatus';
import { VoiceChat } from '@/components/voice/VoiceChat';
import { EnhancedMessage } from '@/components/messages/EnhancedMessage';
import { useChatStore } from '@/lib/stores/chat.store';
import { Toaster, toast } from 'sonner';
import { Badge } from '@/components/ui/badge';
import { Toolbar, type ToolbarAction } from '@/components/layout/Toolbar';
import { Settings, Download } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useDeployedAgents } from '@/lib/hooks/useDeployedAgents';
import { useBackendReadiness } from '@/lib/hooks/useBackendReadiness';
import { AgentActivityStream } from '@/components/monitoring/AgentActivityStream';
import { useAgentActivity } from '@/lib/hooks/useAgentActivity';
import { AlertCircle, Loader2 } from 'lucide-react';
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

export default function PlaygroundPage() {
  const { messages, connectionStatus, sendMessage, isProcessing, error, latency, setSelectedAgentId } = useChatStore();

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

  // Selected agent for voice sessions
  const [selectedAgentId, setLocalSelectedAgentId] = useState<string>('pm-agent');

  // Check backend readiness before allowing interactions
  const {
    readiness,
    loading: readinessLoading,
    error: readinessError,
    isReady: backendReady,
  } = useBackendReadiness();

  // Fetch deployed agents for the current domain
  const {
    data: agentsData,
    loading: agentsLoading,
    error: agentsError,
  } = useDeployedAgents('card-services');

  // Get selected agent details (only from user-created agents)
  const selectedAgent = agentsData?.domain_agents?.find(
    (a: any) => a.id === selectedAgentId
  ) || null;

  // Generate or retrieve session ID for activity streaming
  const [sessionId] = useState(() => {
    if (typeof window !== 'undefined') {
      let id = sessionStorage.getItem('agentfoundry_session_id');
      if (!id) {
        id = `session_${Date.now()}_${Math.random().toString(36).substring(2, 15)}`;
        sessionStorage.setItem('agentfoundry_session_id', id);
      }
      return id;
    }
    return null;
  });

  // Connect to agent activity stream
  const {
    activities,
    activeAgent: activeAgentFromStream,
    connected: activityStreamConnected,
    clearActivities,
  } = useAgentActivity(sessionId);

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
    if (!selectedAgentId) {
      toast.error('Please select an agent first');
      return;
    }

    setIsTyping(true);
    await sendMessage(text, selectedAgentId);
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
          agent_id: selectedAgentId,
          session_duration_hours: 4,
          session_id: sessionId,
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

    if (isVoiceActive) {
      if (level > 0.1 && voiceOrbState === 'listening') {
        setVoiceOrbState('speaking');
      } else if (level <= 0.1 && voiceOrbState === 'speaking') {
        setVoiceOrbState('listening');
      }
    }
  };

  // Update orb state based on text message processing
  useEffect(() => {
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
    <div className="flex flex-col h-full bg-gradient-to-br from-bg-0 via-bg-0 to-bg-1 relative">
      <Toaster position="top-center" richColors />

      {/* Backend Not Ready Overlay */}
      {!backendReady && (
        <div className="absolute inset-0 z-50 bg-bg-0/95 backdrop-blur-sm flex items-center justify-center">
          <div className="flex flex-col items-center gap-4 p-8 rounded-xl bg-bg-1 border border-white/10 shadow-2xl max-w-md mx-4">
            {readinessLoading ? (
              <>
                <Loader2 className="w-12 h-12 text-blue-400 animate-spin" />
                <h2 className="text-xl font-semibold text-fg-0">Connecting to Backend</h2>
                <p className="text-sm text-fg-2 text-center">
                  Please wait while we establish connection with the agent system...
                </p>
              </>
            ) : readinessError ? (
              <>
                <AlertCircle className="w-12 h-12 text-red-400" />
                <h2 className="text-xl font-semibold text-fg-0">Connection Error</h2>
                <p className="text-sm text-red-400 text-center">{readinessError}</p>
                <p className="text-xs text-fg-2 text-center">
                  Make sure the backend server is running on port 8000
                </p>
              </>
            ) : (
              <>
                <Loader2 className="w-12 h-12 text-amber-400 animate-spin" />
                <h2 className="text-xl font-semibold text-fg-0">Backend Initializing</h2>
                <p className="text-sm text-fg-2 text-center">
                  {readiness?.message || 'Waiting for agents to load...'}
                </p>
                <div className="flex flex-col gap-1 text-xs text-fg-2 mt-2">
                  <div className="flex items-center gap-2">
                    <div className={cn(
                      "w-2 h-2 rounded-full",
                      readiness?.marshal_initialized ? "bg-green-400" : "bg-amber-400 animate-pulse"
                    )} />
                    <span>Marshal Agent: {readiness?.marshal_initialized ? 'Ready' : 'Initializing'}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className={cn(
                      "w-2 h-2 rounded-full",
                      readiness?.database_connected ? "bg-green-400" : "bg-amber-400 animate-pulse"
                    )} />
                    <span>Database: {readiness?.database_connected ? 'Connected' : 'Connecting'}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className={cn(
                      "w-2 h-2 rounded-full",
                      (readiness?.agents_loaded ?? 0) > 0 ? "bg-green-400" : "bg-amber-400 animate-pulse"
                    )} />
                    <span>Agents Loaded: {readiness?.agents_loaded ?? 0}</span>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* Toolbar with Agent Selector */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-white/10 bg-bg-0/80 backdrop-blur-sm">
        {/* Agent Selector */}
        <div className="flex items-center gap-3">
          <Bot className="w-5 h-5 text-blue-400" />
          <Select value={selectedAgentId} onValueChange={(val) => { setLocalSelectedAgentId(val); setSelectedAgentId(val); }}>
            <SelectTrigger className="w-64 bg-bg-1 border-white/10">
              <SelectValue placeholder="Select an agent..." />
            </SelectTrigger>
            <SelectContent className="bg-bg-1 border-white/10">
              {agentsLoading && (
                <div className="px-2 py-4 text-sm text-fg-2 text-center">Loading agents...</div>
              )}
              {agentsError && (
                <div className="px-2 py-4 text-sm text-red-400 text-center">
                  Failed to load agents
                </div>
              )}
              {agentsData && (
                <>
                  {agentsData.domain_agents && agentsData.domain_agents.length > 0 ? (
                    <SelectGroup>
                      <SelectLabel className="text-fg-2">Your Agents</SelectLabel>
                      {agentsData.domain_agents.map((agent: any) => (
                        <SelectItem key={agent.id} value={agent.id} className="cursor-pointer">
                          <div className="flex items-center gap-2">
                            <span>{agent.name}</span>
                            {agent.version && (
                              <Badge variant="outline" className="text-[10px] px-1.5 py-0 text-blue-400 border-blue-400/40">
                                v{agent.version}
                              </Badge>
                            )}
                            <Badge
                              variant="outline"
                              className={cn(
                                "text-[10px] px-1 py-0",
                                agent.status === 'healthy' && "text-green-400 border-green-400/40",
                                agent.status === 'degraded' && "text-amber-400 border-amber-400/40",
                                agent.status === 'error' && "text-red-400 border-red-400/40",
                                !agent.status && "text-fg-2 border-white/20"
                              )}
                            >
                              {agent.status || 'active'}
                            </Badge>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectGroup>
                  ) : (
                    <div className="px-2 py-4 text-sm text-fg-2 text-center">
                      No agents deployed yet
                    </div>
                  )}
                </>
              )}
            </SelectContent>
          </Select>
          {selectedAgent && (
            <span className="text-xs text-fg-2 max-w-xs truncate hidden md:inline">
              {selectedAgent.description}
            </span>
          )}
        </div>

        {/* Toolbar Actions */}
        <div className="flex items-center gap-2">
          {toolbarActions.map((action, idx) => (
            <button
              key={idx}
              onClick={action.onClick}
              className="p-2 rounded-md hover:bg-bg-2 text-fg-1 hover:text-fg-0 transition-colors"
              title={action.label}
            >
              <action.icon className="w-4 h-4" />
            </button>
          ))}
        </div>
      </div>

      {/* Hidden LiveKit Component */}
      {isVoiceActive && voiceSession && (
        <div className="hidden">
          <VoiceChat
            token={voiceSession.token}
            serverUrl={voiceSession.serverUrl}
            roomName={voiceSession.roomName}
            userName={userId}
            agentId={selectedAgentId}
            onDisconnect={endVoiceChat}
            onAudioLevel={handleAudioLevel}
          />
        </div>
      )}

      {/* Main Content - Two Column Layout */}
      <main className="flex-1 overflow-hidden flex">
        {/* Center Panel: Chat Interface */}
        <div className="flex-1 overflow-hidden flex flex-col">
          <div className="flex-1 overflow-y-auto">
            <div className="max-w-4xl mx-auto px-4 py-6">
              {/* Empty State */}
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
                    transition={{ delay: 0.2, type: 'spring' }}
                  >
                    <AtomIndicator isSpeaking={isSpeaking} size="lg" className="w-32 h-32" />
                  </motion.div>

                  {/* Agent Info */}
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.25 }}
                    className="text-center"
                  >
                    <h2 className="text-xl font-semibold text-fg-0">
                      {selectedAgent?.name || 'Select an Agent'}
                    </h2>
                    <p className="text-sm text-fg-2 mt-1 max-w-md">
                      {selectedAgent?.description ||
                        'Choose an agent from the dropdown above to start chatting'}
                    </p>
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
                        'flex items-center gap-3 px-6 py-3 rounded-full font-semibold text-sm transition-all shadow-lg',
                        isVoiceActive
                          ? 'bg-red-500 hover:bg-red-600 text-white'
                          : 'bg-blue-600 hover:bg-blue-700 text-white',
                        isLoadingVoice && 'opacity-50 cursor-not-allowed'
                      )}
                    >
                      {isLoadingVoice ? (
                        <>
                          <motion.div
                            animate={{ rotate: 360 }}
                            transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
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
                </motion.div>
              )}

              {/* Messages Section */}
              {messages.length > 0 && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
                  <AnimatePresence>
                    {messages.map((message) => (
                      <EnhancedMessage key={message.id} message={message} showTimestamp={true} />
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
                  Press{' '}
                  <kbd className="px-2 py-0.5 bg-bg-2 border border-white/10 rounded text-xs">
                    Enter
                  </kbd>{' '}
                  to send,
                  <kbd className="ml-1 px-2 py-0.5 bg-bg-2 border border-white/10 rounded text-xs">
                    Shift + Enter
                  </kbd>{' '}
                  for new line
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
        </div>

        {/* Right Panel: Enhanced Activity Feed */}
        <div className="w-[480px] border-l border-white/10 bg-bg-0/50 overflow-hidden flex flex-col">
          <AgentActivityStream
            activities={activities}
            connected={activityStreamConnected}
            onClear={clearActivities}
            activeAgent={activeAgentFromStream}
          />
        </div>
      </main>
    </div>
  );
}
