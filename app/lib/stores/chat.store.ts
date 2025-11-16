import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { v4 as uuidv4 } from 'uuid';
import type { 
  ChatMessage, 
  ConnectionStatus, 
  ConversationContext,
  ToolExecution 
} from '@/lib/types/chat';
import { WebSocketTransport, getWebSocketTransport, WebSocketMessage } from '@/lib/websocket/client';

interface ChatStore {
  // State
  messages: ChatMessage[];
  connectionStatus: ConnectionStatus;
  isProcessing: boolean;
  context: ConversationContext;
  activeRequest: string | null;
  toolExecutions: ToolExecution[];
  error: string | null;
  transport: WebSocketTransport | null;
  useWebSocket: boolean;
  latency: number;

  // Actions
  sendMessage: (content: string) => Promise<void>;
  sendMessageViaHTTP: (content: string) => Promise<void>;
  sendMessageViaWebSocket: (content: string) => Promise<void>;
  receiveMessage: (message: ChatMessage) => void;
  setConnectionStatus: (status: ConnectionStatus) => void;
  setProcessing: (processing: boolean) => void;
  addToolExecution: (execution: ToolExecution) => void;
  updateToolExecution: (toolName: string, updates: Partial<ToolExecution>) => void;
  setError: (error: string | null) => void;
  clearChat: () => void;
  initializeWebSocket: () => void;
  handleWebSocketMessage: (message: WebSocketMessage) => void;
  reconnectWebSocket: () => void;
  disconnectWebSocket: () => void;
}

const initialContext: ConversationContext = {
  sessionId: uuidv4(),
  startedAt: new Date().toISOString(),
  lastActivity: new Date().toISOString(),
  messageCount: 0,
  currentState: 'idle'
};

export const useChatStore = create<ChatStore>()(
  devtools(
    (set, get) => ({
      // Initial State
      messages: [],
      connectionStatus: 'disconnected',
      isProcessing: false,
      context: initialContext,
      activeRequest: null,
      toolExecutions: [],
      error: null,
      transport: null,
      useWebSocket: typeof window !== 'undefined' && 
        (process.env.NEXT_PUBLIC_ENABLE_WEBSOCKET === 'true' || true), // Default to WebSocket
      latency: -1,

      // Initialize WebSocket connection
      initializeWebSocket: () => {
        if (typeof window === 'undefined') return;
        
        const { context, transport: existingTransport } = get();
        
        // Don't reinitialize if already connected
        if (existingTransport && existingTransport.state === 'connected') {
          return;
        }
        
        const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
        const fullUrl = `${wsUrl}/ws/chat?session_id=${context.sessionId}`;
        
        console.log('[Chat Store] Initializing WebSocket:', fullUrl);
        
        try {
          const transport = getWebSocketTransport({
            url: fullUrl,
            reconnect: true,
            reconnectInterval: 1000,
            maxReconnectAttempts: 10,
            heartbeatInterval: 30000
          });
          
          // Set up event listeners
          transport.on('connecting', () => {
            console.log('[Chat Store] WebSocket connecting...');
            set({ connectionStatus: 'connecting' });
          });
          
          transport.on('connected', () => {
            console.log('[Chat Store] WebSocket connected');
            set({ 
              connectionStatus: 'connected',
              error: null
            });
          });
          
          transport.on('disconnected', ({ code, reason }) => {
            console.log('[Chat Store] WebSocket disconnected:', code, reason);
            set({ connectionStatus: 'disconnected' });
          });
          
          transport.on('reconnecting', ({ attempt, delay }) => {
            console.log(`[Chat Store] Reconnecting (attempt ${attempt}, delay ${delay}ms)`);
            set({ 
              connectionStatus: 'reconnecting',
              error: `Reconnecting (attempt ${attempt})...`
            });
          });
          
          transport.on('reconnect_failed', () => {
            console.error('[Chat Store] Max reconnection attempts reached');
            set({ 
              connectionStatus: 'disconnected',
              error: 'Could not reconnect to server. Please refresh the page.'
            });
          });
          
          transport.on('message', (message: WebSocketMessage) => {
            get().handleWebSocketMessage(message);
          });
          
          transport.on('error', (error) => {
            console.error('[Chat Store] WebSocket error:', error);
            set({ error: error.message || 'WebSocket error occurred' });
          });
          
          // Update latency periodically
          const updateLatency = () => {
            const currentLatency = transport.latency;
            if (currentLatency >= 0) {
              set({ latency: currentLatency });
            }
          };
          setInterval(updateLatency, 5000);
          
          // Store transport and initiate connection
          set({ transport });
          
          // Connect asynchronously
          transport.connect().catch((error) => {
            console.error('[Chat Store] WebSocket connection failed:', error);
            set({ 
              connectionStatus: 'disconnected',
              error: 'Failed to connect to server',
              useWebSocket: false // Fall back to HTTP
            });
          });
          
        } catch (error) {
          console.error('[Chat Store] Failed to initialize WebSocket:', error);
          set({ 
            error: error instanceof Error ? error.message : 'WebSocket initialization failed',
            useWebSocket: false // Fall back to HTTP
          });
        }
      },

      // Handle incoming WebSocket messages
      handleWebSocketMessage: (message: WebSocketMessage) => {
        const { messages, context } = get();
        
        console.log('[Chat Store] Received WebSocket message:', message.type);
        
        switch (message.type) {
          case 'status':
            // Handle status updates (e.g., "Understanding your request...")
            if (message.data?.status === 'processing') {
              set({ isProcessing: true });
            }
            // Could show status message in UI
            break;
            
          case 'tool_execution':
            // Track tool execution progress
            const toolData = message.data;
            const existingTool = get().toolExecutions.find(
              t => t.toolName === toolData.tool
            );
            
            if (existingTool) {
              get().updateToolExecution(toolData.tool, {
                status: toolData.status,
                input: toolData.details
              });
            } else {
              get().addToolExecution({
                toolName: toolData.tool,
                status: toolData.status,
                startTime: message.timestamp,
                input: toolData.details
              });
            }
            break;
            
          case 'message':
            // Add assistant message
            const assistantMsg: ChatMessage = {
              id: uuidv4(),
              role: 'assistant',
              content: message.data.content || 'Processing complete.',
              timestamp: message.timestamp,
              artifacts: message.data.artifacts || []
            };
            
            set({ 
              messages: [...messages, assistantMsg],
              isProcessing: false,
              activeRequest: null,
              context: {
                ...context,
                lastActivity: new Date().toISOString(),
                messageCount: context.messageCount + 1,
                currentState: 'idle'
              }
            });
            break;
            
          case 'error':
            // Handle error
            const errorMsg: ChatMessage = {
              id: uuidv4(),
              role: 'assistant',
              content: 'Sorry, I encountered an error processing your request.',
              timestamp: message.timestamp,
              error: message.data?.error || 'Unknown error'
            };
            
            set({ 
              messages: [...messages, errorMsg],
              isProcessing: false,
              activeRequest: null,
              error: message.data?.error || 'An error occurred'
            });
            break;
        }
      },

      // Send message via WebSocket
      sendMessageViaWebSocket: async (content: string) => {
        const { transport, messages, context } = get();
        
        if (!transport || transport.state !== 'connected') {
          throw new Error('WebSocket not connected');
        }
        
        // Create user message
        const userMessage: ChatMessage = {
          id: uuidv4(),
          role: 'user',
          content,
          timestamp: new Date().toISOString()
        };
        
        // Add to UI immediately (optimistic update)
        set({
          messages: [...messages, userMessage],
          isProcessing: true,
          error: null,
          activeRequest: userMessage.id,
          toolExecutions: [], // Clear previous tool executions
          context: {
            ...context,
            lastActivity: new Date().toISOString(),
            messageCount: context.messageCount + 1
          }
        });
        
        // Send via WebSocket
        try {
          transport.send({
            type: 'message',
            data: {
              content,
              session_id: context.sessionId,
              message_history: messages.slice(-10) // Send last 10 for context
            }
          });
        } catch (error) {
          console.error('[Chat Store] Failed to send message:', error);
          set({
            isProcessing: false,
            error: 'Failed to send message'
          });
          throw error;
        }
      },

      // Send message via HTTP (fallback)
      sendMessageViaHTTP: async (content: string) => {
        const { messages, context } = get();
        
        // Create user message
        const userMessage: ChatMessage = {
          id: uuidv4(),
          role: 'user',
          content,
          timestamp: new Date().toISOString()
        };

        // Add to messages and set processing
        set({
          messages: [...messages, userMessage],
          isProcessing: true,
          error: null,
          activeRequest: userMessage.id,
          toolExecutions: [],
          context: {
            ...context,
            lastActivity: new Date().toISOString(),
            messageCount: context.messageCount + 1
          }
        });

        try {
          // Send to backend API
          const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              message: content,
              sessionId: context.sessionId,
              messageHistory: messages.slice(-10)
            })
          });

          if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
          }

          const data = await response.json();
          
          // Create assistant message
          const assistantMessage: ChatMessage = {
            id: uuidv4(),
            role: 'assistant',
            content: data.response || 'Processing your request...',
            timestamp: new Date().toISOString(),
            artifacts: data.artifacts
          };

          // Update state with response
          set((state) => ({
            messages: [...state.messages, assistantMessage],
            isProcessing: false,
            activeRequest: null,
            context: {
              ...state.context,
              lastActivity: new Date().toISOString(),
              messageCount: state.context.messageCount + 1,
              currentState: data.currentState || 'idle'
            }
          }));

        } catch (error) {
          console.error('[Chat Store] Failed to send message via HTTP:', error);
          
          // Add error message
          const errorMessage: ChatMessage = {
            id: uuidv4(),
            role: 'assistant',
            content: 'Sorry, I encountered an error processing your request. Please try again.',
            timestamp: new Date().toISOString(),
            error: error instanceof Error ? error.message : 'Unknown error'
          };

          set((state) => ({
            messages: [...state.messages, errorMessage],
            isProcessing: false,
            activeRequest: null,
            error: error instanceof Error ? error.message : 'Failed to send message'
          }));
        }
      },

      // Send message (routes to WebSocket or HTTP)
      sendMessage: async (content: string) => {
        const { useWebSocket, transport } = get();
        
        // Use WebSocket if enabled and connected
        if (useWebSocket && transport && transport.state === 'connected') {
          console.log('[Chat Store] Sending message via WebSocket');
          return get().sendMessageViaWebSocket(content);
        } else {
          console.log('[Chat Store] Sending message via HTTP (WebSocket not available)');
          return get().sendMessageViaHTTP(content);
        }
      },

      // Receive message from backend (for WebSocket later)
      receiveMessage: (message: ChatMessage) => {
        set((state) => ({
          messages: [...state.messages, message],
          context: {
            ...state.context,
            lastActivity: new Date().toISOString(),
            messageCount: state.context.messageCount + 1
          }
        }));
      },

      // Connection management
      setConnectionStatus: (status: ConnectionStatus) => {
        set({ connectionStatus: status });
      },

      // Processing state
      setProcessing: (processing: boolean) => {
        set({ isProcessing: processing });
      },

      // Tool execution tracking
      addToolExecution: (execution: ToolExecution) => {
        set((state) => ({
          toolExecutions: [...state.toolExecutions, execution]
        }));
      },

      updateToolExecution: (toolName: string, updates: Partial<ToolExecution>) => {
        set((state) => ({
          toolExecutions: state.toolExecutions.map(exec =>
            exec.toolName === toolName
              ? { ...exec, ...updates }
              : exec
          )
        }));
      },

      // Error handling
      setError: (error: string | null) => {
        set({ error });
      },

      // Reconnect WebSocket
      reconnectWebSocket: () => {
        const { transport } = get();
        if (transport) {
          transport.connect().catch((error) => {
            console.error('[Chat Store] Manual reconnection failed:', error);
          });
        } else {
          get().initializeWebSocket();
        }
      },

      // Disconnect WebSocket
      disconnectWebSocket: () => {
        const { transport } = get();
        if (transport) {
          transport.disconnect();
          set({ 
            transport: null,
            connectionStatus: 'disconnected'
          });
        }
      },

      // Clear chat
      clearChat: () => {
        const newSessionId = uuidv4();
        set({
          messages: [],
          context: {
            ...initialContext,
            sessionId: newSessionId
          },
          activeRequest: null,
          toolExecutions: [],
          error: null,
          isProcessing: false
        });
        
        // Reinitialize WebSocket with new session
        get().disconnectWebSocket();
        get().initializeWebSocket();
      }
    }),
    {
      name: 'chat-store'
    }
  )
);

// Initialize WebSocket on mount (client-side only)
if (typeof window !== 'undefined') {
  // Small delay to ensure environment is ready
  setTimeout(() => {
    useChatStore.getState().initializeWebSocket();
  }, 100);
}
