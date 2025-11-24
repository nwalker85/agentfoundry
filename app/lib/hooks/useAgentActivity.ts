/**
 * Hook: useAgentActivity
 * WebSocket connection for streaming real-time agent activity
 */

import { useState, useEffect, useRef, useCallback } from 'react';

export interface AgentActivity {
  agent_id: string;
  agent_name: string;
  event_type:
    | 'started'
    | 'processing'
    | 'tool_call'
    | 'completed'
    | 'error'
    | 'interrupted'
    | 'resumed'
    | 'user_message'
    | 'agent_message';
  timestamp: number;
  message: string;
  metadata?: Record<string, any>;
}

export function useAgentActivity(sessionId: string | null) {
  const [activities, setActivities] = useState<AgentActivity[]>([]);
  const [activeAgent, setActiveAgent] = useState<string | null>(null);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!sessionId) return;

    // Determine WebSocket URL based on environment
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const wsUrl = apiUrl.replace(/^http/, 'ws');
    const fullWsUrl = `${wsUrl}/api/monitoring/ws/agent-activity/${sessionId}`;

    console.log(`🔌 Connecting to agent activity stream: ${fullWsUrl}`);

    const ws = new WebSocket(fullWsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('✅ Agent activity stream connected');
      setConnected(true);

      // Send keepalive ping every 30 seconds
      pingIntervalRef.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send('ping');
        }
      }, 30000);
    };

    ws.onmessage = (event) => {
      // Handle pong response
      if (event.data === 'pong') {
        return;
      }

      try {
        const data = JSON.parse(event.data);

        if (data.type === 'agent_activity') {
          const activity: AgentActivity = {
            agent_id: data.agent_id,
            agent_name: data.agent_name,
            event_type: data.event_type,
            timestamp: data.timestamp,
            message: data.message,
            metadata: data.metadata,
          };

          console.log(`📡 Activity received: ${activity.agent_name} - ${activity.event_type}`);

          // Add to activity log
          setActivities((prev) => [...prev, activity]);

          // Update active agent
          if (
            activity.event_type === 'started' ||
            activity.event_type === 'processing' ||
            activity.event_type === 'resumed'
          ) {
            setActiveAgent(activity.agent_id);
          } else if (activity.event_type === 'completed' || activity.event_type === 'error') {
            setActiveAgent(null);
          } else if (activity.event_type === 'interrupted') {
            // Keep agent active but in paused state
            setActiveAgent(activity.agent_id);
          }
        }
      } catch (err) {
        console.error('Error parsing WebSocket message:', err);
      }
    };

    ws.onerror = (error) => {
      console.error('❌ WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('🔌 Agent activity stream disconnected');
      setConnected(false);
      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current);
        pingIntervalRef.current = null;
      }
    };

    return () => {
      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current);
      }
      ws.close();
    };
  }, [sessionId]);

  const clearActivities = useCallback(() => {
    setActivities([]);
  }, []);

  return { activities, activeAgent, connected, clearActivities };
}
