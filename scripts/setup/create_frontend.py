#!/usr/bin/env python3
"""
Frontend Implementation Generator
Creates the critical missing chat UI components
"""

from pathlib import Path
from textwrap import dedent

def create_chat_page():
    """Create the missing chat interface page"""
    chat_dir = Path("app/chat")
    chat_dir.mkdir(parents=True, exist_ok=True)
    
    content = dedent('''
    'use client'
    
    import { useState, useEffect } from 'react'
    import ChatInterface from '@/components/ChatInterface'
    import MessageList from '@/components/MessageList'
    
    export default function ChatPage() {
        const [messages, setMessages] = useState([])
        const [loading, setLoading] = useState(false)
        
        const handleSendMessage = async (text: string) => {
            setLoading(true)
            
            // Add user message
            const userMessage = { role: 'user', content: text, timestamp: Date.now() }
            setMessages(prev => [...prev, userMessage])
            
            try {
                // Call MCP server through Next.js API route
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: text })
                })
                
                const data = await response.json()
                
                // Add agent response
                const agentMessage = { 
                    role: 'assistant', 
                    content: data.response,
                    artifacts: data.artifacts, // stories/issues created
                    timestamp: Date.now() 
                }
                setMessages(prev => [...prev, agentMessage])
                
            } catch (error) {
                console.error('Chat error:', error)
            } finally {
                setLoading(false)
            }
        }
        
        return (
            <div className="flex flex-col h-screen">
                <header className="p-4 border-b">
                    <h1 className="text-2xl font-bold">Engineering Department Chat</h1>
                </header>
                
                <MessageList messages={messages} />
                
                <ChatInterface 
                    onSendMessage={handleSendMessage}
                    disabled={loading}
                />
            </div>
        )
    }
    ''').strip()
    
    with open(chat_dir / "page.tsx", 'w') as f:
        f.write(content)
    
    print(f"✓ Created app/chat/page.tsx")

def create_api_routes():
    """Create the missing API routes for MCP integration"""
    api_dir = Path("app/api/chat")
    api_dir.mkdir(parents=True, exist_ok=True)
    
    content = dedent('''
    import { NextRequest, NextResponse } from 'next/server'
    
    const MCP_SERVER_URL = process.env.MCP_SERVER_URL || 'http://localhost:8001'
    
    export async function POST(request: NextRequest) {
        try {
            const { message } = await request.json()
            
            // Forward to MCP server's PM agent endpoint
            const response = await fetch(`${MCP_SERVER_URL}/api/agent/process`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message,
                    session_id: request.headers.get('x-session-id') || 'default'
                })
            })
            
            const data = await response.json()
            
            return NextResponse.json({
                response: data.response,
                artifacts: data.artifacts, // Created stories/issues
                session_id: data.session_id
            })
            
        } catch (error) {
            console.error('API route error:', error)
            return NextResponse.json(
                { error: 'Failed to process message' },
                { status: 500 }
            )
        }
    }
    ''').strip()
    
    with open(api_dir / "route.ts", 'w') as f:
        f.write(content)
    
    print(f"✓ Created app/api/chat/route.ts")

def create_components():
    """Create the missing UI components"""
    comp_dir = Path("app/components")
    comp_dir.mkdir(parents=True, exist_ok=True)
    
    # ChatInterface component
    chat_interface = dedent('''
    'use client'
    
    import { useState } from 'react'
    
    interface ChatInterfaceProps {
        onSendMessage: (message: string) => void
        disabled?: boolean
    }
    
    export default function ChatInterface({ onSendMessage, disabled }: ChatInterfaceProps) {
        const [input, setInput] = useState('')
        
        const handleSubmit = (e: React.FormEvent) => {
            e.preventDefault()
            if (input.trim() && !disabled) {
                onSendMessage(input)
                setInput('')
            }
        }
        
        return (
            <form onSubmit={handleSubmit} className="p-4 border-t">
                <div className="flex gap-2">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Describe what you want to build..."
                        className="flex-1 px-4 py-2 border rounded-lg"
                        disabled={disabled}
                    />
                    <button
                        type="submit"
                        disabled={disabled || !input.trim()}
                        className="px-6 py-2 bg-blue-500 text-white rounded-lg disabled:opacity-50"
                    >
                        Send
                    </button>
                </div>
            </form>
        )
    }
    ''').strip()
    
    with open(comp_dir / "ChatInterface.tsx", 'w') as f:
        f.write(chat_interface)
    
    print(f"✓ Created app/components/ChatInterface.tsx")
    
    # MessageList component
    message_list = dedent('''
    interface Message {
        role: 'user' | 'assistant'
        content: string
        artifacts?: any[]
        timestamp: number
    }
    
    interface MessageListProps {
        messages: Message[]
    }
    
    export default function MessageList({ messages }: MessageListProps) {
        return (
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((msg, idx) => (
                    <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-2xl p-4 rounded-lg ${
                            msg.role === 'user' 
                                ? 'bg-blue-500 text-white' 
                                : 'bg-gray-100'
                        }`}>
                            <div className="font-semibold mb-1">
                                {msg.role === 'user' ? 'You' : 'PM Agent'}
                            </div>
                            <div className="whitespace-pre-wrap">{msg.content}</div>
                            
                            {msg.artifacts && msg.artifacts.length > 0 && (
                                <div className="mt-3 pt-3 border-t border-gray-300">
                                    <div className="text-sm font-medium mb-2">Created:</div>
                                    {msg.artifacts.map((artifact, i) => (
                                        <div key={i} className="text-sm">
                                            • {artifact.type}: {artifact.title}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                ))}
            </div>
        )
    }
    ''').strip()
    
    with open(comp_dir / "MessageList.tsx", 'w') as f:
        f.write(message_list)
    
    print(f"✓ Created app/components/MessageList.tsx")

def create_dockerfile():
    """Create Docker configuration for containerization"""
    content = dedent('''
    # Multi-stage build for Python + Node.js
    FROM python:3.12-slim as python-base
    
    WORKDIR /app
    
    # Install Python dependencies
    COPY requirements.txt .
    RUN pip install --no-cache-dir -r requirements.txt
    
    # Copy Python code
    COPY mcp_server.py .
    COPY mcp/ ./mcp/
    COPY agent/ ./agent/
    
    # Node.js stage
    FROM node:20-alpine as node-builder
    
    WORKDIR /app
    
    # Install Node dependencies
    COPY package*.json .
    RUN npm ci
    
    # Copy and build Next.js
    COPY app/ ./app/
    COPY public/ ./public/
    COPY next.config.js .
    COPY tsconfig.json .
    
    RUN npm run build
    
    # Final stage
    FROM python:3.12-slim
    
    # Install Node.js runtime
    RUN apt-get update && apt-get install -y nodejs npm && rm -rf /var/lib/apt/lists/*
    
    WORKDIR /app
    
    # Copy Python from python-base
    COPY --from=python-base /app /app
    COPY --from=python-base /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
    
    # Copy Node.js build
    COPY --from=node-builder /app/.next ./.next
    COPY --from=node-builder /app/node_modules ./node_modules
    COPY --from=node-builder /app/public ./public
    COPY --from=node-builder /app/package.json ./package.json
    
    # Environment
    ENV NODE_ENV=production
    ENV PYTHONUNBUFFERED=1
    
    # Expose ports
    EXPOSE 3000 8001
    
    # Start both services
    CMD ["sh", "-c", "python mcp_server.py & npm start"]
    ''').strip()
    
    with open("Dockerfile", 'w') as f:
        f.write(content)
    
    print(f"✓ Created Dockerfile")
    
    # Docker Compose
    compose_content = dedent('''
    version: '3.8'
    
    services:
      engineering-dept:
        build: .
        ports:
          - "3000:3000"  # Next.js UI
          - "8001:8001"  # MCP Server
        environment:
          - NODE_ENV=production
          - MCP_SERVER_URL=http://localhost:8001
        env_file:
          - .env.local
        volumes:
          - ./audit:/app/audit  # Persist audit logs
        restart: unless-stopped
        
      redis:
        image: redis:7-alpine
        ports:
          - "6379:6379"
        volumes:
          - redis_data:/data
        restart: unless-stopped
    
    volumes:
      redis_data:
    ''').strip()
    
    with open("docker-compose.yml", 'w') as f:
        f.write(compose_content)
    
    print(f"✓ Created docker-compose.yml")

def main():
    print("=" * 50)
    print("🚀 Frontend Implementation Generator")
    print("=" * 50)
    
    print("\n📱 Creating Chat UI...")
    create_chat_page()
    
    print("\n🔌 Creating API Routes...")
    create_api_routes()
    
    print("\n🎨 Creating Components...")
    create_components()
    
    print("\n🐳 Creating Docker Configuration...")
    create_dockerfile()
    
    print("\n" + "=" * 50)
    print("✅ Frontend scaffold complete!")
    print("\nNext steps:")
    print("1. Review generated components")
    print("2. Update MCP server with /api/agent/process endpoint")
    print("3. Test chat interface locally")
    print("4. Build Docker image for containerized deployment")

if __name__ == "__main__":
    main()
