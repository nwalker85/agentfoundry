/**
 * React hook for subscribing to real-time events via WebSocket
 *
 * Usage:
 * ```typescript
 * const { subscribe, isConnected } = useEventSubscription()
 *
 * useEffect(() => {
 *   const unsubscribe = subscribe(
 *     {
 *       type: 'agent.*',
 *       organization_id: 'quant',
 *       domain_id: 'demo'
 *     },
 *     (event) => {
 *       console.log('Received event:', event)
 *       // Update local state
 *     }
 *   )
 *
 *   return unsubscribe
 * }, [])
 * ```
 */

import { useEffect, useRef, useState, useCallback } from 'react';

export interface EventFilter {
  type?: string; // e.g., "agent.*" for all agent events, "agent.created" for specific
  organization_id?: string;
  domain_id?: string;
}

export interface Event {
  type: string;
  timestamp: string;
  data: Record<string, any>;
  organization_id?: string;
  domain_id?: string;
  actor?: string;
}

type EventHandler = (event: Event) => void;

export function useEventSubscription() {
  const wsRef = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const handlersRef = useRef<Map<string, EventHandler>>(new Map());
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 10;

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    // Use service discovery for WebSocket URL
    const { API } = require('@/lib/config/services');
    const wsUrl = API.websocket.events();
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('🔌 WebSocket connected');
      setIsConnected(true);
      reconnectAttempts.current = 0;

      // Resubscribe all handlers
      handlersRef.current.forEach((handler, filterId) => {
        const filter = JSON.parse(filterId);
        ws.send(
          JSON.stringify({
            action: 'subscribe',
            filter,
          })
        );
      });
    };

    ws.onmessage = (event) => {
      try {
        const data: Event = JSON.parse(event.data);

        // Ignore non-event messages (like subscription_confirmed, pong)
        if (
          data.type === 'subscription_confirmed' ||
          data.type === 'pong' ||
          data.type === 'unsubscribed'
        ) {
          return;
        }

        // Call all matching handlers
        handlersRef.current.forEach((handler) => {
          handler(data);
        });
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    ws.onclose = () => {
      console.log('🔌 WebSocket disconnected');
      setIsConnected(false);
      wsRef.current = null;

      // Attempt to reconnect with exponential backoff
      if (reconnectAttempts.current < maxReconnectAttempts) {
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
        console.log(
          `Reconnecting in ${delay}ms (attempt ${reconnectAttempts.current + 1}/${maxReconnectAttempts})`
        );

        reconnectTimeoutRef.current = setTimeout(() => {
          reconnectAttempts.current++;
          connect();
        }, delay);
      } else {
        console.error('Max reconnection attempts reached');
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    wsRef.current = ws;
  }, []);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  const subscribe = useCallback((filter: EventFilter, handler: EventHandler): (() => void) => {
    const filterId = JSON.stringify(filter);
    handlersRef.current.set(filterId, handler);

    // Send subscription message to server
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          action: 'subscribe',
          filter,
        })
      );
    }

    // Return unsubscribe function
    return () => {
      handlersRef.current.delete(filterId);

      // If no more handlers, unsubscribe from server
      if (handlersRef.current.size === 0 && wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ action: 'unsubscribe' }));
      }
    };
  }, []);

  return {
    subscribe,
    isConnected,
  };
}
