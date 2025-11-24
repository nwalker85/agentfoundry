'use client';

import { useEffect, useState } from 'react';
import { MessageCircle, X } from 'lucide-react';

type ChatMessage = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
};

export function AdminAssistantPanel() {
  const [isOpen, setIsOpen] = useState(false);
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
    <>
      {/* Floating button bottom-left */}
      <button
        type="button"
        onClick={() => setIsOpen((open) => !open)}
        className="fixed bottom-6 right-6 z-40 flex h-11 w-11 items-center justify-center rounded-full border border-white/10 bg-blue-500/90 text-white shadow-lg shadow-blue-900/50 backdrop-blur-md hover:bg-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-300"
        aria-label="Open admin assistant"
      >
        <MessageCircle className="h-5 w-5" />
      </button>

      {/* Panel */}
      {isOpen && (
        <div className="fixed bottom-24 right-6 z-40 w-96 max-h-[60vh] rounded-xl border border-white/15 bg-bg-2/90 shadow-2xl shadow-black/60 backdrop-blur-md backdrop-saturate-150">
          <div className="flex items-center justify-between border-b border-white/10 px-3 py-2">
            <div className="flex flex-col">
              <span className="text-xs text-fg-2">Assistant</span>
              <span className="text-sm font-semibold text-fg-0 tracking-tight">Foundry Admin</span>
            </div>
            <button
              type="button"
              onClick={() => setIsOpen(false)}
              className="rounded p-1 text-fg-2 hover:bg-bg-3/80"
              aria-label="Close admin assistant"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          <div className="flex max-h-[36vh] flex-col gap-2 overflow-y-auto px-3 py-2 text-xs">
            {messages.length === 0 && (
              <div className="rounded-lg bg-bg-3/80 p-2 text-fg-2">
                Ask me about organizations, domains, instances, or how to use Forge and the control
                plane.
              </div>
            )}
            {messages.map((m) => (
              <div
                key={m.id}
                className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg px-2 py-1 ${
                    m.role === 'user'
                      ? 'bg-blue-500/90 text-white shadow-sm shadow-blue-900/40'
                      : 'bg-bg-3/90 text-fg-0 border border-white/10'
                  }`}
                >
                  {m.content}
                </div>
              </div>
            ))}
          </div>

          <div className="border-t border-white/10 px-3 py-2">
            <textarea
              rows={2}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about orgs, domains, Forge..."
              className="w-full resize-none rounded-md bg-bg-1/80 px-2 py-1 text-xs text-fg-0 placeholder:text-fg-2 focus:outline-none focus:ring-1 focus:ring-blue-500/70"
            />
            <div className="mt-1 flex justify-end">
              <button
                type="button"
                onClick={() => void sendMessage()}
                disabled={isSending || !input.trim()}
                className="rounded-md bg-blue-500/90 px-3 py-1 text-xs font-medium text-white shadow-sm shadow-blue-900/40 disabled:opacity-50"
              >
                {isSending ? 'Sending...' : 'Send'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
