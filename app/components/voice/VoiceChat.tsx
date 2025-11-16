'use client';

import { useEffect } from 'react';
import { LiveKitRoom, RoomAudioRenderer, useLocalParticipant, useTrackVolume } from '@livekit/components-react';
import '@livekit/components-styles';
import { Track } from 'livekit-client';
import { VoiceControls } from './VoiceControls';
import { AudioVisualizer } from './AudioVisualizer';
import { ParticipantList } from './ParticipantList';

// Helper component to track audio levels and call callback
function AudioLevelTracker({ onAudioLevel }: { onAudioLevel?: (level: number) => void }) {
  const { localParticipant } = useLocalParticipant();
  const micTrackPub = localParticipant?.getTrackPublication(Track.Source.Microphone);
  const volume = useTrackVolume(micTrackPub?.track as any);

  useEffect(() => {
    if (onAudioLevel) {
      // Volume is already in 0-1 range from useTrackVolume
      onAudioLevel(volume);
    }
  }, [volume, onAudioLevel]);

  return null; // This component doesn't render anything
}

interface VoiceChatProps {
  token: string;
  serverUrl: string;
  roomName: string;
  userName: string;
  agentId: string;
  onDisconnect: () => void;
  onAudioLevel?: (level: number) => void; // 0-1 range
}

export function VoiceChat({
  token,
  serverUrl,
  roomName,
  userName,
  agentId,
  onDisconnect,
  onAudioLevel,
}: VoiceChatProps) {
  return (
    <LiveKitRoom
      token={token}
      serverUrl={serverUrl}
      connect={true}
      audio={true}
      video={false}
      onDisconnected={onDisconnect}
      className="voice-chat-container"
    >
      {/* Audio renderer for playback */}
      <RoomAudioRenderer />

      {/* Track audio levels and send to parent */}
      {onAudioLevel && <AudioLevelTracker onAudioLevel={onAudioLevel} />}

      <div className="voice-chat-ui">
        <div className="voice-header">
          <h3>Voice Chat with {agentId}</h3>
          <span className="room-name">{roomName}</span>
        </div>

        <AudioVisualizer />
        <ParticipantList />
        <VoiceControls onDisconnect={onDisconnect} />
      </div>
    </LiveKitRoom>
  );
}
