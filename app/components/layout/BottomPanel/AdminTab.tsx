'use client';

import { useEffect, useState } from 'react';
import { Send } from 'lucide-react';
import { ScrollArea } from '@/components/ui/scroll-area';

type ChatMessage = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
};

export function AdminTab() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isSending, setIsSending] = useState(false);

  // Restore last few messages from localStorage
  useEffect(() => {
    try {
      const raw = localStorage.getItem('adminAssistantMessages');
      if (raw) {
        setMessages(JSON.parse(raw));
      }
    } catch (e) {
      console.error('Failed to restore admin assistant messages:', e);
    }
  }, []);

  // Persist messages
  useEffect(() => {
    try {
      localStorage.setItem('adminAssistantMessages', JSON.stringify(messages.slice(-20)));
    } catch {
      // ignore
    }
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || isSending) return;

    const message = input.trim();
    setInput('');

    const newMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: message,
    };
    setMessages((prev) => [...prev, newMessage]);
    setIsSending(true);

    try {
      const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const res = await fetch(`${apiBase}/api/admin/assistant/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: message }),
      });

      if (!res.ok) {
        const errorText = await res.text();
        setMessages((prev) => [
          ...prev,
          {
            id: crypto.randomUUID(),
            role: 'assistant',
            content: `⚠️ Admin assistant error (${res.status}): ${errorText || 'Unknown error'}`,
          },
        ]);
        return;
      }

      const data = await res.json();
      const reply = (data && data.reply) || 'I received your request.';

      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: reply,
        },
      ]);
    } catch (e: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: `⚠️ Failed to reach admin assistant: ${e?.message || String(e)}`,
        },
      ]);
    } finally {
      setIsSending(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      void sendMessage();
    }
  };

  return (
    <div className="flex flex-col h-full">
      <ScrollArea className="flex-1 px-3 py-2">
        <div className="flex flex-col gap-2">
          {messages.length === 0 && (
            <div className="rounded-lg bg-bg-3/80 p-3 text-xs text-fg-2">
              <p className="font-medium text-fg-1 mb-1">
                👋 Hello! I'm your Foundry Admin Assistant
              </p>
              <p>Ask me about:</p>
              <ul className="list-disc list-inside mt-1 space-y-0.5">
                <li>Organizations, domains, and instances</li>
                <li>Agents and deployments</li>
                <li>How to use Forge and the control plane</li>
                <li>Platform features and capabilities</li>
              </ul>
            </div>
          )}
          {messages.map((m) => (
            <div
              key={m.id}
              className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[85%] rounded-lg px-3 py-2 text-xs ${
                  m.role === 'user'
                    ? 'bg-blue-500/90 text-white shadow-sm shadow-blue-900/40'
                    : 'bg-bg-3/90 text-fg-0 border border-white/10'
                }`}
              >
                <div className="whitespace-pre-wrap">{m.content}</div>
              </div>
            </div>
          ))}
        </div>
      </ScrollArea>

      <div className="border-t border-white/10 px-3 py-2 bg-bg-1/50">
        <div className="flex gap-2">
          <textarea
            rows={2}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about orgs, domains, agents, Forge... (Cmd+K to focus)"
            className="flex-1 resize-none rounded-md bg-bg-2/80 px-3 py-2 text-xs text-fg-0 placeholder:text-fg-2 focus:outline-none focus:ring-1 focus:ring-blue-500/70 border border-white/10"
          />
          <button
            type="button"
            onClick={() => void sendMessage()}
            disabled={isSending || !input.trim()}
            className="px-4 rounded-md bg-blue-500/90 text-white shadow-sm shadow-blue-900/40 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2 text-xs font-medium"
          >
            <Send className="h-3.5 w-3.5" />
            {isSending ? 'Sending...' : 'Send'}
          </button>
        </div>
        <div className="mt-1 text-[10px] text-fg-3">
          Press Enter to send, Shift+Enter for new line
        </div>
      </div>
    </div>
  );
}
