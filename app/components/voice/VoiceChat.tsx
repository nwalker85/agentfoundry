'use client';

import { LiveKitRoom, RoomAudioRenderer } from '@livekit/components-react';
import '@livekit/components-styles';
import { VoiceControls } from './VoiceControls';
import { AudioVisualizer } from './AudioVisualizer';
import { ParticipantList } from './ParticipantList';

interface VoiceChatProps {
  token: string;
  serverUrl: string;
  roomName: string;
  userName: string;
  agentId: string;
  onDisconnect: () => void;
}

export function VoiceChat({
  token,
  serverUrl,
  roomName,
  userName,
  agentId,
  onDisconnect,
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
