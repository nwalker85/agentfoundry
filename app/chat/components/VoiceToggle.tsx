'use client';

import { useState } from 'react';
import { Phone, PhoneOff } from 'lucide-react';
import { VoiceChat } from '@/components/voice/VoiceChat';

interface VoiceToggleProps {
  userId: string;
  agentId: string;
}

export function VoiceToggle({ userId, agentId }: VoiceToggleProps) {
  const [isVoiceActive, setIsVoiceActive] = useState(false);
  const [voiceSession, setVoiceSession] = useState<{
    token: string;
    serverUrl: string;
    roomName: string;
  } | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const startVoiceChat = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/voice/session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          agent_id: agentId,
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
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start voice chat');
      console.error('Voice session error:', err);
    } finally {
      setIsLoading(false);
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
  };

  return (
    <div className="voice-toggle-container">
      {!isVoiceActive ? (
        <button
          onClick={startVoiceChat}
          disabled={isLoading}
          className="voice-toggle-button"
          title="Start voice chat"
        >
          <Phone size={20} />
          {isLoading ? 'Connecting...' : 'Start Voice'}
        </button>
      ) : (
        voiceSession && (
          <div className="voice-chat-active">
            <VoiceChat
              token={voiceSession.token}
              serverUrl={voiceSession.serverUrl}
              roomName={voiceSession.roomName}
              userName={userId}
              agentId={agentId}
              onDisconnect={endVoiceChat}
            />
          </div>
        )
      )}

      {error && (
        <div className="voice-error">
          {error}
        </div>
      )}
    </div>
  );
}
