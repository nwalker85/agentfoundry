# Frontend Development Plan

**Created:** November 10, 2025  
**Status:** 🔴 Critical Path - Blocking POC Demo  
**Priority:** P0 - Immediate Implementation Required  
**Version:** 1.0

---

## Executive Summary

The frontend is the **critical missing piece** preventing POC demonstration. While the LangGraph PM agent (v0.4.0) and MCP server are operational, there's no way for users to interact with the system. This plan provides a focused, pragmatic path to complete frontend implementation within 1 week.

**Current State:** Basic status page only (20% complete)  
**Target State:** Fully functional chat interface with tool results (80% complete)  
**Timeline:** 5-7 days  
**Blocker for:** POC demonstrations, user testing, stakeholder reviews

---

## Current Gap Analysis

### ✅ What's Working
- Next.js 14.2 setup with App Router
- Dependencies installed (React Query, Zustand, Socket.io-client)
- Basic status page at `/`
- Tailwind CSS configured
- Navigation structure defined

### 🔴 Critical Gaps
| Gap | Impact | Resolution |
|-----|--------|------------|
| No `/chat` route | Can't interact with PM agent | Implement chat UI |
| No WebSocket layer | No real-time responses | Add transport layer |
| No API bridge | Frontend can't reach MCP | Create API routes |
| No tool result display | Can't show stories/issues | Build result cards |
| No state management | Lost context on refresh | Implement Zustand store |

---

## Implementation Phases

### Phase 1: Core Chat Infrastructure (Days 1-2)
**Objective:** Get messages flowing between UI and PM agent

#### 1.1 Create Chat Route Structure
```bash
# Create directory structure
mkdir -p app/chat/components
mkdir -p app/chat/hooks
mkdir -p app/lib/transport
mkdir -p app/lib/stores
mkdir -p app/components/tool-results
```

#### 1.2 Implement Message Transport
```typescript
// app/lib/transport/websocket.ts
export class ChatTransport {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private messageQueue: Message[] = []
  
  connect(url: string): void
  send(message: ChatMessage): void
  onMessage(handler: MessageHandler): void
  reconnect(): void
}
```

#### 1.3 Build Chat UI Components
```typescript
// app/chat/page.tsx
- MessageThread component
- InputArea with send button
- ConnectionStatus indicator
- LoadingStates for pending messages
```

#### 1.4 Wire State Management
```typescript
// app/lib/stores/chat.store.ts
interface ChatState {
  messages: Message[]
  activeRequest: Request | null
  toolExecutions: ToolExecution[]
  connectionStatus: ConnectionStatus
  
  // Actions
  sendMessage: (text: string) => void
  receiveMessage: (message: Message) => void
  executeToolAction: (tool: ToolCall) => void
}
```

**Deliverables:**
- [ ] Chat page loads at `/chat`
- [ ] Messages display in thread
- [ ] Input sends to store
- [ ] Connection status shows

---

### Phase 2: API Bridge Layer (Day 3)
**Objective:** Connect frontend to MCP server and PM agent

#### 2.1 Create API Routes
```typescript
// app/api/chat/route.ts
export async function POST(request: Request) {
  const { message, sessionId } = await request.json()
  
  // Forward to PM agent via MCP
  const response = await fetch('http://localhost:8001/api/agent/process', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, session_id: sessionId })
  })
  
  return Response.json(await response.json())
}
```

#### 2.2 Add WebSocket Support
```typescript
// app/api/ws/route.ts
export function GET(request: Request) {
  // Upgrade to WebSocket
  // Forward messages to MCP
  // Stream responses back
}
```

#### 2.3 Update MCP Server
```python
# Add to mcp_server.py
@app.post("/api/agent/process")
async def process_agent_message(
    message: str = Body(...),
    session_id: str = Body(default="default")
) -> Dict:
    """Process message through PM agent"""
    from agent.pm_graph import PMAgent
    
    agent = PMAgent()
    result = await agent.process_message(message)
    
    return {
        "response": result.get("response"),
        "artifacts": result.get("artifacts", []),
        "requires_clarification": result.get("requires_clarification", False),
        "session_id": session_id
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    # Handle streaming responses
```

**Deliverables:**
- [ ] API route handles POST requests
- [ ] MCP server processes messages
- [ ] Responses return to frontend
- [ ] WebSocket connection established

---

### Phase 3: Tool Results & Artifacts (Days 4-5)
**Objective:** Display story/issue creation results beautifully

#### 3.1 Build Result Card Components
```typescript
// app/components/tool-results/StoryCreatedCard.tsx
export function StoryCreatedCard({ story }: { story: NotionStory }) {
  return (
    <Card>
      <CardHeader>
        <Badge>Story Created</Badge>
        <h3>{story.title}</h3>
      </CardHeader>
      <CardContent>
        <p>Epic: {story.epic}</p>
        <p>Priority: {story.priority}</p>
        <Link href={story.url}>View in Notion →</Link>
      </CardContent>
    </Card>
  )
}
```

#### 3.2 Handle Multi-Step Clarification
```typescript
// app/chat/components/ClarificationPrompt.tsx
export function ClarificationPrompt({ 
  question, 
  onAnswer 
}: ClarificationPromptProps) {
  return (
    <div className="border-l-4 border-yellow-500 p-4">
      <p className="text-yellow-800">{question}</p>
      <Input onSubmit={onAnswer} placeholder="Your answer..." />
    </div>
  )
}
```

#### 3.3 Implement Streaming Responses
```typescript
// app/chat/hooks/useStreamingResponse.ts
export function useStreamingResponse() {
  const [chunks, setChunks] = useState<string[]>([])
  
  const handleChunk = (chunk: string) => {
    setChunks(prev => [...prev, chunk])
  }
  
  return { text: chunks.join(''), handleChunk }
}
```

**Deliverables:**
- [ ] Story creation shows card with links
- [ ] Issue creation shows GitHub link
- [ ] Clarification prompts work
- [ ] Streaming text displays progressively

---

### Phase 4: Backlog View (Day 6)
**Objective:** Show Notion stories in organized view

#### 4.1 Create Backlog Page
```typescript
// app/backlog/page.tsx
export default async function BacklogPage() {
  const stories = await fetchStories()
  
  return (
    <div>
      <PriorityTabs>
        <Tab value="P0">Critical</Tab>
        <Tab value="P1">High</Tab>
        <Tab value="P2">Medium</Tab>
        <Tab value="P3">Low</Tab>
      </PriorityTabs>
      
      <StoryList stories={filteredStories} />
    </div>
  )
}
```

#### 4.2 Add Filtering & Search
```typescript
// app/backlog/components/StoryFilters.tsx
- Priority filter
- Status filter
- Epic grouping
- Search by title
```

**Deliverables:**
- [ ] Backlog page shows all stories
- [ ] Priority filtering works
- [ ] Links to Notion/GitHub functional
- [ ] Search filters results

---

### Phase 5: Polish & Production Readiness (Day 7)
**Objective:** Make it demo-ready

#### 5.1 Error Handling
- Network failure recovery
- Invalid response handling
- User-friendly error messages
- Retry with exponential backoff

#### 5.2 Loading States
- Skeleton loaders for messages
- Pending indicators for tool actions
- Connection status banner
- Progress indicators for long operations

#### 5.3 Accessibility
- ARIA labels on all interactive elements
- Keyboard navigation (Tab, Enter, Escape)
- Screen reader announcements
- Focus management in modal/cards

#### 5.4 Demo Optimizations
- Seed data for impressive demos
- Quick action buttons
- Example prompts
- Reset/clear conversation

**Deliverables:**
- [ ] No console errors
- [ ] All loading states smooth
- [ ] Keyboard fully navigable
- [ ] Demo script prepared

---

## Technical Architecture

### Component Hierarchy
```
app/
├── layout.tsx                    # Root layout with providers
├── page.tsx                      # Landing/status page
├── chat/
│   ├── page.tsx                  # Main chat interface
│   ├── components/
│   │   ├── MessageThread.tsx    # Message list display
│   │   ├── MessageInput.tsx     # Input with send button
│   │   ├── Message.tsx          # Individual message
│   │   ├── ClarificationPrompt.tsx
│   │   └── ConnectionStatus.tsx
│   └── hooks/
│       ├── useChat.ts           # Chat logic hook
│       ├── useWebSocket.ts      # WS connection hook
│       └── useStreamingResponse.ts
├── backlog/
│   ├── page.tsx                  # Story list view
│   └── components/
│       ├── StoryList.tsx
│       ├── StoryCard.tsx
│       └── StoryFilters.tsx
├── api/
│   ├── chat/
│   │   └── route.ts              # HTTP endpoint
│   ├── ws/
│   │   └── route.ts              # WebSocket upgrade
│   └── backlog/
│       └── route.ts              # Notion proxy
├── components/
│   ├── tool-results/
│   │   ├── StoryCreatedCard.tsx
│   │   ├── IssueCreatedCard.tsx
│   │   ├── QueryResultsTable.tsx
│   │   └── ErrorCard.tsx
│   └── ui/                       # Shared UI components
└── lib/
    ├── transport/
    │   ├── websocket.ts
    │   └── http.ts
    ├── stores/
    │   ├── chat.store.ts
    │   └── backlog.store.ts
    └── utils/
        ├── formatting.ts
        └── validation.ts
```

### Data Flow
```
User Input → Chat UI → Store → Transport → API Route → MCP Server → PM Agent
                ↑                                              ↓
                ←──────── Tool Results ←───────────────────────┘
```

### State Management Design
```typescript
// Zustand store structure
interface AppState {
  // Chat state
  chat: {
    messages: Message[]
    activeRequest: Request | null
    connectionStatus: ConnectionStatus
  }
  
  // Backlog state  
  backlog: {
    stories: Story[]
    filters: FilterState
    lastFetch: Date | null
  }
  
  // Actions
  actions: {
    sendMessage: (text: string) => Promise<void>
    fetchStories: (filters?: Filter) => Promise<void>
    clearChat: () => void
  }
}
```

---

## Implementation Checklist

### Day 1-2: Core Chat ✅
- [ ] Create `/chat` route structure
- [ ] Implement basic message UI
- [ ] Add input component
- [ ] Setup Zustand store
- [ ] Create WebSocket client
- [ ] Display connection status

### Day 3: API Bridge ✅
- [ ] Create `/api/chat` route
- [ ] Add MCP proxy logic
- [ ] Update MCP server endpoint
- [ ] Test message round trip
- [ ] Add error handling

### Day 4-5: Tool Results ✅
- [ ] Build StoryCreatedCard
- [ ] Build IssueCreatedCard
- [ ] Handle clarification prompts
- [ ] Implement streaming text
- [ ] Add loading states

### Day 6: Backlog ✅
- [ ] Create `/backlog` route
- [ ] Fetch stories from MCP
- [ ] Add priority filters
- [ ] Display story cards
- [ ] Link to external systems

### Day 7: Polish ✅
- [ ] Add error boundaries
- [ ] Improve loading states
- [ ] Test keyboard navigation
- [ ] Prepare demo script
- [ ] Fix any bugs

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| WebSocket complexity | High | Start with HTTP polling, add WS later |
| PM agent response variability | Medium | Add Zod schemas for validation |
| State synchronization issues | Medium | Use single store, avoid prop drilling |
| Performance with long threads | Low | Implement virtual scrolling |
| Authentication not ready | Low | Use session IDs for now |

---

## Testing Strategy

### Manual Testing Checklist
- [ ] Can send message and receive response
- [ ] Story creation shows Notion link
- [ ] Issue creation shows GitHub link
- [ ] Clarification prompts work
- [ ] Backlog displays all stories
- [ ] Filters work correctly
- [ ] Error states display properly
- [ ] Can recover from disconnection

### E2E Test Scenarios
```typescript
// tests/e2e/chat.test.ts
describe('Chat Interface', () => {
  it('sends message and receives response')
  it('displays story creation card')
  it('handles clarification flow')
  it('recovers from network error')
  it('maintains conversation context')
})
```

---

## Success Metrics

### Minimum Viable (Day 5)
- ✅ User can chat with PM agent
- ✅ Story/Issue creation visible
- ✅ Basic error handling works

### Demo Ready (Day 7)  
- ✅ Smooth conversation flow
- ✅ All tool results display nicely
- ✅ Backlog view functional
- ✅ No console errors
- ✅ Keyboard navigable

### Production Ready (Future)
- Real-time WebSocket streaming
- Multi-user sessions
- Persistent conversation history
- Full observability integration
- 100% accessibility compliance

---

## Quick Start Commands

```bash
# Start everything for development
# Terminal 1: MCP Server
cd /Users/nwalker/Development/Projects/Engineering\ Department/engineeringdepartment
source venv/bin/activate
python mcp_server.py

# Terminal 2: Frontend
npm run dev

# Terminal 3: Test the flow
curl -X POST http://localhost:3000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Create a story for adding healthcheck endpoint"}'

# Visit http://localhost:3000/chat
```

---

## Dependencies & Prerequisites

### Required Running Services
- MCP Server on port 8001
- LangGraph PM Agent configured
- Notion API credentials set
- GitHub API credentials set
- OpenAI API key configured

### NPM Packages Needed
```json
{
  "dependencies": {
    "next": "14.2.33",            ✅ Installed
    "react": "18.2.0",            ✅ Installed  
    "react-dom": "18.2.0",        ✅ Installed
    "@tanstack/react-query": "^5.17.0",  ✅ Installed
    "zustand": "^4.5.0",          ✅ Installed
    "socket.io-client": "^4.6.0", ✅ Installed
    "zod": "^3.22.4",             ✅ Installed
    "lucide-react": "^0.314.0",   ✅ Installed
    "@radix-ui/themes": "^2.0.0", ✅ Installed
    "tailwindcss": "^3.4.1"       ✅ Installed
  }
}
```

---

## Notes & Considerations

### Why This Plan Will Succeed
1. **Incremental delivery** - Each day produces visible progress
2. **Fallback options** - HTTP before WebSocket, polling before streaming
3. **Reuses existing code** - MCP server and PM agent ready
4. **Clear validation** - Checklist ensures nothing missed
5. **Risk aware** - Mitigations for every identified risk

### What Can Be Deferred
- Authentication/authorization (use session IDs)
- Persistent storage (in-memory for POC)
- Multi-tenant isolation (single tenant POC)
- Advanced UI features (animations, themes)
- Comprehensive error recovery (basic is enough)

### Critical Success Factors
1. **MCP endpoint must handle agent requests** - Add immediately
2. **Simple message flow first** - Complexity can be added
3. **Visual feedback crucial** - Users need to see progress
4. **Tool results must be clear** - Links and status obvious
5. **Demo script prepared** - Practice the happy path

---

## Appendix: Code Templates

### A1: WebSocket Client Template
```typescript
// app/lib/transport/websocket.ts
import { EventEmitter } from 'events'

export class WebSocketClient extends EventEmitter {
  private ws: WebSocket | null = null
  private url: string
  private reconnectTimer: NodeJS.Timeout | null = null
  private messageQueue: any[] = []
  
  constructor(url: string) {
    super()
    this.url = url
  }
  
  connect(): void {
    try {
      this.ws = new WebSocket(this.url)
      
      this.ws.onopen = () => {
        this.emit('connected')
        this.flushQueue()
      }
      
      this.ws.onmessage = (event) => {
        const data = JSON.parse(event.data)
        this.emit('message', data)
      }
      
      this.ws.onclose = () => {
        this.emit('disconnected')
        this.scheduleReconnect()
      }
      
      this.ws.onerror = (error) => {
        this.emit('error', error)
      }
    } catch (error) {
      this.emit('error', error)
      this.scheduleReconnect()
    }
  }
  
  send(data: any): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    } else {
      this.messageQueue.push(data)
    }
  }
  
  private flushQueue(): void {
    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift()
      this.send(message)
    }
  }
  
  private scheduleReconnect(): void {
    if (this.reconnectTimer) return
    
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null
      this.connect()
    }, 5000)
  }
  
  disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }
}
```

### A2: MCP Server Agent Endpoint
```python
# Add to mcp_server.py

from typing import Dict, Optional
from fastapi import WebSocket, WebSocketDisconnect
from agent.pm_graph import PMAgent
import json
import asyncio

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
    
    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
    
    async def send_message(self, message: dict, session_id: str):
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            await websocket.send_json(message)

manager = ConnectionManager()

@app.post("/api/agent/process")
async def process_agent_message(
    message: str = Body(...),
    session_id: str = Body(default="default")
) -> Dict:
    """Process a message through the PM agent"""
    try:
        # Get or create agent for session
        agent = PMAgent()
        
        # Process the message
        result = await agent.aprocess_message(message)
        
        # Extract artifacts if any
        artifacts = []
        if result.get("story_created"):
            artifacts.append({
                "type": "story",
                "data": result["story_created"]
            })
        if result.get("issue_created"):
            artifacts.append({
                "type": "issue", 
                "data": result["issue_created"]
            })
        
        return {
            "success": True,
            "response": result.get("response", "Processing your request..."),
            "artifacts": artifacts,
            "requires_clarification": result.get("requires_clarification", False),
            "clarification_prompt": result.get("clarification_prompt"),
            "session_id": session_id
        }
        
    except Exception as e:
        logger.error(f"Agent processing error: {e}")
        return {
            "success": False,
            "error": str(e),
            "session_id": session_id
        }

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect(websocket, session_id)
    agent = PMAgent()
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Process through agent with streaming
            async for chunk in agent.astream_message(message_data["message"]):
                await manager.send_message({
                    "type": "chunk",
                    "content": chunk
                }, session_id)
            
            # Send completion
            await manager.send_message({
                "type": "complete",
                "artifacts": []  # Add any created artifacts
            }, session_id)
            
    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(session_id)
```

---

**This plan provides the clear path from 20% to 80% frontend completion in 1 week.**

*Priority: This is the #1 blocker for POC demonstrations. Start immediately.*
