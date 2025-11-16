'use client';

import { useTrackVolume } from '@livekit/components-react';
import { Track } from 'livekit-client';
import { useLocalParticipant } from '@livekit/components-react';

export function AudioVisualizer() {
  const { localParticipant } = useLocalParticipant();
  const micTrackPub = localParticipant?.getTrackPublication(Track.Source.Microphone);
  const volume = useTrackVolume(micTrackPub?.track);

  // Normalize volume to 0-100 range
  const volumeLevel = Math.min(100, Math.max(0, volume * 100));

  return (
    <div className="audio-visualizer">
      <div className="visualizer-label">Your voice level</div>
      <div className="visualizer-bar-container">
        <div
          className="visualizer-bar"
          style={{
            width: `${volumeLevel}%`,
            backgroundColor: volumeLevel > 70 ? '#ef4444' : volumeLevel > 40 ? '#f59e0b' : '#10b981'
          }}
        />
      </div>
    </div>
  );
}
