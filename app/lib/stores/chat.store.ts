import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { v4 as uuidv4 } from 'uuid';
import type { 
  ChatMessage, 
  ConnectionStatus, 
  ConversationContext,
  ToolExecution 
} from '@/lib/types/chat';

interface ChatStore {
  // State
  messages: ChatMessage[];
  connectionStatus: ConnectionStatus;
  isProcessing: boolean;
  context: ConversationContext;
  activeRequest: string | null;
  toolExecutions: ToolExecution[];
  error: string | null;

  // Actions
  sendMessage: (content: string) => Promise<void>;
  receiveMessage: (message: ChatMessage) => void;
  setConnectionStatus: (status: ConnectionStatus) => void;
  setProcessing: (processing: boolean) => void;
  addToolExecution: (execution: ToolExecution) => void;
  updateToolExecution: (toolName: string, updates: Partial<ToolExecution>) => void;
  setError: (error: string | null) => void;
  clearChat: () => void;
  initializeSession: () => void;
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

      // Send message to backend
      sendMessage: async (content: string) => {
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
              messageHistory: messages.slice(-10) // Send last 10 messages for context
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
          console.error('Failed to send message:', error);
          
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
      },

      // Initialize session
      initializeSession: () => {
        set({ 
          connectionStatus: 'connecting',
          context: initialContext 
        });

        // Simulate connection (replace with real connection logic)
        setTimeout(() => {
          set({ connectionStatus: 'connected' });
        }, 1000);
      }
    }),
    {
      name: 'chat-store'
    }
  )
);

// Initialize store on mount
if (typeof window !== 'undefined') {
  useChatStore.getState().initializeSession();
}
