'use client';

import { useParticipants, useLocalParticipant } from '@livekit/components-react';
import { User, Bot } from 'lucide-react';

export function ParticipantList() {
  const participants = useParticipants();
  const { localParticipant } = useLocalParticipant();

  return (
    <div className="participant-list">
      <h4>In this conversation</h4>
      <div className="participants">
        {participants.map((participant) => {
          const isLocal = participant.sid === localParticipant?.sid;
          const isAgent = participant.identity.startsWith('agent-');
          const isSpeaking = participant.isSpeaking;

          return (
            <div
              key={participant.sid}
              className={`participant ${isSpeaking ? 'speaking' : ''}`}
            >
              <div className="participant-icon">
                {isAgent ? <Bot size={16} /> : <User size={16} />}
              </div>
              <span className="participant-name">
                {participant.name || participant.identity}
                {isLocal && ' (You)'}
              </span>
              {isSpeaking && <div className="speaking-indicator" />}
            </div>
          );
        })}
      </div>
    </div>
  );
}
