'use client';

import { useLocalParticipant, useRoomContext } from '@livekit/components-react';
import { Track } from 'livekit-client';
import { Mic, MicOff, PhoneOff } from 'lucide-react';

interface VoiceControlsProps {
  onDisconnect: () => void;
}

export function VoiceControls({ onDisconnect }: VoiceControlsProps) {
  const { localParticipant } = useLocalParticipant();
  const room = useRoomContext();

  const isMuted = localParticipant?.isMicrophoneEnabled === false;

  const toggleMute = async () => {
    await localParticipant?.setMicrophoneEnabled(!localParticipant.isMicrophoneEnabled);
  };

  const handleDisconnect = () => {
    room?.disconnect();
    onDisconnect();
  };

  return (
    <div className="voice-controls">
      <button
        onClick={toggleMute}
        className={`control-button ${isMuted ? 'muted' : 'active'}`}
        title={isMuted ? 'Unmute' : 'Mute'}
      >
        {isMuted ? <MicOff size={24} /> : <Mic size={24} />}
      </button>

      <button
        onClick={handleDisconnect}
        className="control-button disconnect"
        title="End call"
      >
        <PhoneOff size={24} />
      </button>
    </div>
  );
}
