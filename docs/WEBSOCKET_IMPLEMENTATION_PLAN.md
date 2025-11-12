# WebSocket Implementation Plan

**Date**: November 11, 2025  
**Version**: v0.7.0 Target  
**Status**: Ready for Implementation  
**Effort**: 6-8 hours  

---

## Overview

Upgrade from HTTP polling to WebSocket transport for real-time bidirectional communication between frontend and backend. This enables streaming responses, live status updates, and reduced latency.

## Current State

### Backend ✅
- `/ws/chat` endpoint exists in `mcp_server.py`
- `ConnectionManager` class handles multiple connections
- `handle_websocket_message` processes incoming messages
- Supports message types: `message`, `tool_execution`, `status`, `error`, `ping`, `pong`
- Audit logging integrated

### Frontend ✅
- `WebSocketTransport` class fully implemented in `app/lib/websocket/client.ts`
- Event-driven architecture with EventEmitter
- Automatic reconnection with exponential backoff
- Heartbeat/ping-pong for connection health
- Message queuing during disconnection
- Singleton pattern with `getWebSocketTransport()`

### Gap 🔄
- Chat store still uses HTTP fetch
- WebSocket transport not integrated into Zustand store
- UI doesn't handle streaming updates
- No connection recovery UI

---

## Implementation Steps

### Phase 1: Chat Store WebSocket Integration (2 hours)

#### 1.1 Update chat.store.ts
**File**: `/app/lib/stores/chat.store.ts`

```typescript
import { WebSocketTransport, getWebSocketTransport, WebSocketMessage } from '@/lib/websocket/client';

interface ChatStore {
  // ... existing state ...
  transport: WebSocketTransport | null;
  
  // New actions
  initializeWebSocket: () => void;
  handleWebSocketMessage: (message: WebSocketMessage) => void;
  sendMessageViaWebSocket: (content: string) => Promise<void>;
}

// In store implementation:
const store = create<ChatStore>()(
  devtools(
    (set, get) => ({
      // ... existing state ...
      transport: null,
      
      // Initialize WebSocket on mount
      initializeWebSocket: () => {
        const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8001/ws/chat';
        const sessionId = get().context.sessionId;
        
        const transport = getWebSocketTransport({
          url: `${wsUrl}?session_id=${sessionId}`,
          reconnect: true,
          reconnectInterval: 1000,
          maxReconnectAttempts: 10,
          heartbeatInterval: 30000
        });
        
        // Set up event listeners
        transport.on('connected', () => {
          set({ connectionStatus: 'connected' });
        });
        
        transport.on('disconnected', () => {
          set({ connectionStatus: 'disconnected' });
        });
        
        transport.on('reconnecting', ({ attempt, delay }) => {
          set({ 
            connectionStatus: 'reconnecting',
            error: `Reconnecting (attempt ${attempt})...`
          });
        });
        
        transport.on('message', (message: WebSocketMessage) => {
          get().handleWebSocketMessage(message);
        });
        
        transport.on('error', (error) => {
          set({ error: error.message });
        });
        
        // Connect
        transport.connect().catch((error) => {
          console.error('WebSocket connection failed:', error);
          set({ 
            connectionStatus: 'disconnected',
            error: 'Failed to connect to server'
          });
        });
        
        set({ transport });
      },
      
      // Handle incoming WebSocket messages
      handleWebSocketMessage: (message: WebSocketMessage) => {
        const { messages } = get();
        
        switch (message.type) {
          case 'message':
            // Add assistant message
            const assistantMsg: ChatMessage = {
              id: uuidv4(),
              role: 'assistant',
              content: message.data.content,
              timestamp: message.timestamp,
              artifacts: message.data.artifacts || []
            };
            set({ 
              messages: [...messages, assistantMsg],
              isProcessing: false,
              activeRequest: null
            });
            break;
            
          case 'status':
            // Update UI with status (e.g., "Understanding your request...")
            set({ 
              error: null,
              // Could add status message to UI
            });
            break;
            
          case 'tool_execution':
            // Track tool execution in progress
            get().addToolExecution({
              toolName: message.data.tool,
              status: message.data.status,
              startTime: message.timestamp,
              input: message.data.details
            });
            break;
            
          case 'error':
            set({ 
              error: message.data.error,
              isProcessing: false 
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
          activeRequest: userMessage.id
        });
        
        // Send via WebSocket
        transport.send({
          type: 'message',
          data: {
            content,
            session_id: context.sessionId,
            message_history: messages.slice(-10)
          }
        });
      }
    })
  )
);
```

#### 1.2 Update sendMessage to use WebSocket
```typescript
sendMessage: async (content: string) => {
  const { transport } = get();
  
  // Use WebSocket if available, otherwise fall back to HTTP
  if (transport && transport.state === 'connected') {
    return get().sendMessageViaWebSocket(content);
  } else {
    // Fallback to existing HTTP implementation
    return get().sendMessageViaHTTP(content);
  }
}
```

### Phase 2: UI Updates for Streaming (2 hours)

#### 2.1 Add Streaming Indicator Component
**File**: `/app/chat/components/StreamingIndicator.tsx`

```typescript
'use client';

import { motion } from 'framer-motion';
import { Loader2 } from 'lucide-react';

interface StreamingIndicatorProps {
  status: string;
}

export function StreamingIndicator({ status }: StreamingIndicatorProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="flex items-center gap-2 text-sm text-gray-500 px-4 py-2 bg-blue-50 rounded-lg"
    >
      <Loader2 className="w-4 h-4 animate-spin" />
      <span>{status}</span>
    </motion.div>
  );
}
```

#### 2.2 Add Tool Execution Progress
**File**: `/app/chat/components/ToolExecutionProgress.tsx`

```typescript
'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle, Circle, Loader2 } from 'lucide-react';
import { ToolExecution } from '@/lib/types/chat';

interface ToolExecutionProgressProps {
  executions: ToolExecution[];
}

export function ToolExecutionProgress({ executions }: ToolExecutionProgressProps) {
  if (executions.length === 0) return null;
  
  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: 'auto' }}
      exit={{ opacity: 0, height: 0 }}
      className="px-4 py-3 bg-gray-50 rounded-lg space-y-2"
    >
      <p className="text-xs font-medium text-gray-600">Processing Steps</p>
      <AnimatePresence>
        {executions.map((exec) => (
          <motion.div
            key={exec.toolName}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex items-center gap-2 text-sm"
          >
            {exec.status === 'completed' ? (
              <CheckCircle className="w-4 h-4 text-green-500" />
            ) : exec.status === 'running' ? (
              <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />
            ) : (
              <Circle className="w-4 h-4 text-gray-300" />
            )}
            <span className="text-gray-700">{exec.toolName}</span>
          </motion.div>
        ))}
      </AnimatePresence>
    </motion.div>
  );
}
```

#### 2.3 Update ChatPage to show tool progress
```typescript
// In app/chat/page.tsx
import { ToolExecutionProgress } from './components/ToolExecutionProgress';

// In component:
const { toolExecutions } = useChatStore();

// In render:
{isProcessing && toolExecutions.length > 0 && (
  <ToolExecutionProgress executions={toolExecutions} />
)}
```

### Phase 3: Connection Recovery UI (1 hour)

#### 3.1 Enhanced ConnectionStatus Component
**File**: Update `/app/chat/components/ConnectionStatus.tsx`

```typescript
'use client';

import { motion } from 'framer-motion';
import { Wifi, WifiOff, RefreshCw } from 'lucide-react';
import { ConnectionStatus as Status } from '@/lib/types/chat';

interface ConnectionStatusProps {
  status: Status;
  latency?: number;
  onReconnect?: () => void;
}

export function ConnectionStatus({ status, latency, onReconnect }: ConnectionStatusProps) {
  const getStatusConfig = () => {
    switch (status) {
      case 'connected':
        return {
          icon: Wifi,
          text: latency ? `Connected (${latency}ms)` : 'Connected',
          color: 'text-green-600',
          bgColor: 'bg-green-50',
          animate: false
        };
      case 'connecting':
      case 'reconnecting':
        return {
          icon: RefreshCw,
          text: status === 'reconnecting' ? 'Reconnecting...' : 'Connecting...',
          color: 'text-yellow-600',
          bgColor: 'bg-yellow-50',
          animate: true
        };
      case 'disconnected':
        return {
          icon: WifiOff,
          text: 'Disconnected',
          color: 'text-red-600',
          bgColor: 'bg-red-50',
          animate: false
        };
    }
  };
  
  const config = getStatusConfig();
  const Icon = config.icon;
  
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className={`flex items-center gap-2 px-3 py-1.5 rounded-full ${config.bgColor}`}
    >
      <motion.div
        animate={config.animate ? { rotate: 360 } : {}}
        transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
      >
        <Icon className={`w-4 h-4 ${config.color}`} />
      </motion.div>
      <span className={`text-xs font-medium ${config.color}`}>
        {config.text}
      </span>
      {status === 'disconnected' && onReconnect && (
        <button
          onClick={onReconnect}
          className="text-xs underline hover:no-underline"
        >
          Retry
        </button>
      )}
    </motion.div>
  );
}
```

### Phase 4: Backend Streaming Enhancement (2 hours)

#### 4.1 Update PM Agent for Streaming
**File**: Update `/agent/pm_graph.py`

Add streaming callback parameter:
```python
async def process_message(
    self,
    message: str,
    stream_callback: Optional[Callable] = None
) -> Dict[str, Any]:
    """
    Process a message through the PM agent.
    
    Args:
        message: User message to process
        stream_callback: Optional callback for streaming updates
    """
    
    # Example streaming updates during processing:
    if stream_callback:
        await stream_callback("clarification", {"status": "analyzing request"})
    
    # ... existing processing ...
    
    if stream_callback:
        await stream_callback("planning", {"tasks_identified": len(tasks)})
    
    # ... more processing ...
    
    if stream_callback:
        await stream_callback("notion", {"status": "creating story"})
```

#### 4.2 Update WebSocket Handler
Already supports `stream_callback` in existing implementation! ✅

### Phase 5: Testing & Validation (1 hour)

#### 5.1 Manual Testing Checklist
```bash
# Terminal 1: Start backend
python mcp_server.py

# Terminal 2: Start frontend  
npm run dev

# Test scenarios:
- [ ] Send message via WebSocket
- [ ] Verify streaming status updates appear
- [ ] Test connection recovery (kill/restart server)
- [ ] Verify message queuing during disconnect
- [ ] Test heartbeat/ping-pong
- [ ] Verify tool execution progress displays
- [ ] Check audit logs for WebSocket events
```

#### 5.2 Integration Tests
**File**: `/tests/integration/test_websocket.py`

```python
import pytest
import asyncio
from websockets import connect

@pytest.mark.asyncio
async def test_websocket_connection():
    """Test WebSocket connection and basic message flow."""
    uri = "ws://localhost:8001/ws/chat?session_id=test-123"
    
    async with connect(uri) as websocket:
        # Should receive connection status
        message = await websocket.recv()
        data = json.loads(message)
        assert data["type"] == "status"
        assert data["data"]["status"] == "connected"
        
        # Send message
        await websocket.send(json.dumps({
            "type": "message",
            "data": {"content": "Create a P1 story for test"}
        }))
        
        # Should receive response
        message = await websocket.recv()
        data = json.loads(message)
        assert data["type"] == "message"
        assert "content" in data["data"]

@pytest.mark.asyncio
async def test_websocket_reconnection():
    """Test reconnection logic."""
    # Test reconnection after disconnect
    pass

@pytest.mark.asyncio
async def test_websocket_heartbeat():
    """Test ping/pong heartbeat."""
    # Test heartbeat mechanism
    pass
```

---

## Migration Strategy

### Option A: Gradual (Recommended)
1. Deploy WebSocket alongside HTTP
2. Add feature flag: `ENABLE_WEBSOCKET=true`
3. Roll out to 10% of users
4. Monitor error rates and latency
5. Gradually increase to 100%
6. Deprecate HTTP endpoint after 2 weeks

### Option B: Big Bang
1. Switch all traffic to WebSocket
2. Keep HTTP as emergency fallback
3. Monitor closely for 24 hours
4. Roll back if issues detected

**Recommendation**: Use Option A with feature flag.

---

## Environment Variables

Add to `.env.local`:
```bash
# WebSocket Configuration
ENABLE_WEBSOCKET=true
NEXT_PUBLIC_WS_URL=ws://localhost:8001
WS_HEARTBEAT_INTERVAL=30000
WS_MAX_RECONNECT_ATTEMPTS=10
WS_RECONNECT_INTERVAL=1000
```

---

## Monitoring & Observability

### Metrics to Track
- WebSocket connection count
- Average connection duration
- Reconnection frequency
- Message latency (send → receive)
- Failed connection attempts
- Queue size during disconnections

### Logging
```typescript
// Add to chat.store.ts
transport.on('connected', () => {
  console.log('[WebSocket] Connected', {
    sessionId: get().context.sessionId,
    timestamp: new Date().toISOString()
  });
});

transport.on('message', (msg) => {
  console.log('[WebSocket] Message received', {
    type: msg.type,
    latency: Date.now() - new Date(msg.timestamp).getTime()
  });
});
```

---

## Rollback Plan

If WebSocket implementation causes issues:

1. **Immediate**: Set `ENABLE_WEBSOCKET=false` in environment
2. **Code rollback**: Revert chat.store.ts to HTTP implementation
3. **Redeploy**: Push previous version
4. **Verify**: Test HTTP fallback working
5. **Investigate**: Check logs for root cause

---

## Success Criteria

- [ ] WebSocket connects automatically on page load
- [ ] Messages sent/received via WebSocket
- [ ] Streaming status updates display in UI
- [ ] Tool execution progress shows in real-time
- [ ] Connection recovers automatically after disconnect
- [ ] Latency < 100ms for message round-trip
- [ ] No message loss during normal operation
- [ ] Queue handles up to 100 messages during disconnect
- [ ] Heartbeat keeps connection alive
- [ ] Audit logs capture WebSocket events

---

## Next Steps After Implementation

1. **Token Streaming**: Stream LLM tokens character-by-character
2. **Multi-Tab Sync**: Synchronize state across browser tabs
3. **Presence Indicators**: Show who else is online
4. **Collaborative Editing**: Real-time collaborative document editing
5. **Push Notifications**: Server-initiated notifications

---

**Estimated Timeline**: 6-8 hours  
**Risk Level**: Medium (well-tested client library exists)  
**Priority**: P1 (unlocks better UX)  
**Dependencies**: None (can implement immediately)

---

**Ready to start?** Begin with Phase 1: Chat Store Integration
