/**
 * WebSocket Transport Client
 * ==========================
 *
 * Robust WebSocket client with automatic reconnection, heartbeat,
 * and message queuing for Agent Foundry real-time communication.
 *
 * Features:
 * - Automatic reconnection with exponential backoff
 * - Heartbeat/ping-pong to detect stale connections
 * - Message queuing when disconnected
 * - Event-based API using EventEmitter
 * - Connection state management
 *
 * @module lib/websocket/client
 *
 * @example
 * ```typescript
 * import { getWebSocketTransport, closeWebSocketTransport } from '@/lib/websocket/client';
 *
 * // Initialize and connect
 * const ws = getWebSocketTransport({
 *   url: 'ws://localhost:8000/ws/chat',
 *   reconnect: true,
 *   heartbeatInterval: 30000,
 * });
 *
 * await ws.connect();
 *
 * // Listen for events
 * ws.on('message', (msg) => console.log('Received:', msg));
 * ws.on('connected', () => console.log('Connected!'));
 * ws.on('disconnected', ({ code, reason }) => console.log('Disconnected:', code));
 *
 * // Send messages
 * ws.send({ type: 'message', data: { content: 'Hello!' } });
 *
 * // Cleanup
 * closeWebSocketTransport();
 * ```
 */

import { EventEmitter } from 'events';

/**
 * WebSocket message structure
 */
export interface WebSocketMessage {
  type: 'message' | 'tool_execution' | 'status' | 'error' | 'ping' | 'pong' | 'select_agent';
  data: any;
  timestamp?: string;
  sessionId?: string;
}

export interface WebSocketConfig {
  url: string;
  reconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  heartbeatInterval?: number;
  messageQueueSize?: number;
}

export class WebSocketTransport extends EventEmitter {
  private ws: WebSocket | null = null;
  private config: Required<WebSocketConfig>;
  private reconnectAttempts = 0;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private heartbeatTimeoutTimer: NodeJS.Timeout | null = null;
  private messageQueue: WebSocketMessage[] = [];
  private isConnecting = false;
  private isReconnecting = false;
  private shouldReconnect = true;
  private lastPingTime = 0;
  private lastPongTime = 0;
  private connectionTimeoutTimer: NodeJS.Timeout | null = null;

  constructor(config: WebSocketConfig) {
    super();

    this.config = {
      url: config.url,
      reconnect: config.reconnect ?? true,
      reconnectInterval: config.reconnectInterval ?? 1000,
      maxReconnectAttempts: config.maxReconnectAttempts ?? 10,
      heartbeatInterval: config.heartbeatInterval ?? 30000,
      messageQueueSize: config.messageQueueSize ?? 100,
    };

    this.shouldReconnect = this.config.reconnect;
  }

  /**
   * Connect to WebSocket server
   */
  async connect(): Promise<void> {
    // Don't connect if already connected or connecting
    if (this.isConnecting || this.ws?.readyState === WebSocket.OPEN) {
      console.log('[WebSocket] Already connecting or connected, skipping');
      return;
    }

    // Clean up any existing connection first
    this.cleanupConnection();

    this.isConnecting = true;
    this.emit('connecting');

    return new Promise<void>((resolve, reject) => {
      let isResolved = false;

      // Set connection timeout (15 seconds)
      this.connectionTimeoutTimer = setTimeout(() => {
        if (isResolved) return;
        isResolved = true;

        console.error('[WebSocket] Connection timeout after 15s');
        this.cleanupConnection();
        this.isConnecting = false;

        const error = new Error('Connection timeout');
        this.emit('error', error);
        reject(error);
      }, 15000);

      try {
        this.ws = new WebSocket(this.config.url);

        // Connection opened
        this.ws.onopen = () => {
          if (isResolved) return;
          isResolved = true;

          if (this.connectionTimeoutTimer) {
            clearTimeout(this.connectionTimeoutTimer);
            this.connectionTimeoutTimer = null;
          }

          this.handleOpen();
          resolve();
        };

        // Message received
        this.ws.onmessage = this.handleMessage.bind(this);

        // Error occurred
        this.ws.onerror = (event) => {
          console.error('[WebSocket] Connection error:', event);

          if (!isResolved) {
            isResolved = true;

            if (this.connectionTimeoutTimer) {
              clearTimeout(this.connectionTimeoutTimer);
              this.connectionTimeoutTimer = null;
            }

            this.isConnecting = false;
            const error = new Error('WebSocket connection error');
            this.handleError(event);
            reject(error);
          } else {
            this.handleError(event);
          }
        };

        // Connection closed
        this.ws.onclose = (event) => {
          if (!isResolved) {
            isResolved = true;

            if (this.connectionTimeoutTimer) {
              clearTimeout(this.connectionTimeoutTimer);
              this.connectionTimeoutTimer = null;
            }

            this.isConnecting = false;
            reject(new Error(`Connection closed during connect: ${event.code} - ${event.reason}`));
          }

          this.handleClose(event);
        };
      } catch (error) {
        if (!isResolved) {
          isResolved = true;

          if (this.connectionTimeoutTimer) {
            clearTimeout(this.connectionTimeoutTimer);
            this.connectionTimeoutTimer = null;
          }

          this.isConnecting = false;
          reject(error);
        }
      }
    });
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    console.log('[WebSocket] Disconnecting...');
    this.shouldReconnect = false;
    this.config.reconnect = false;
    this.cleanupConnection();
    this.clearAllTimers();

    if (this.ws) {
      if (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING) {
        this.ws.close(1000, 'Client disconnect');
      }
      this.ws = null;
    }

    this.emit('disconnected', { code: 1000, reason: 'Client disconnect' });
  }

  /**
   * Send a message through WebSocket
   */
  send(message: Omit<WebSocketMessage, 'timestamp'>): void {
    const fullMessage: WebSocketMessage = {
      ...message,
      timestamp: new Date().toISOString(),
    };

    if (this.ws?.readyState === WebSocket.OPEN) {
      try {
        this.ws.send(JSON.stringify(fullMessage));
        this.emit('message_sent', fullMessage);
      } catch (error) {
        console.error('[WebSocket] Failed to send message:', error);
        this.queueMessage(fullMessage);
      }
    } else {
      console.warn('[WebSocket] Not connected, queueing message');
      this.queueMessage(fullMessage);

      // Attempt to reconnect if not already doing so
      if (this.shouldReconnect && !this.isReconnecting && !this.isConnecting) {
        this.reconnect();
      }
    }
  }

  /**
   * Get connection state
   */
  get state(): 'connecting' | 'connected' | 'disconnected' | 'reconnecting' {
    if (this.isConnecting) return 'connecting';
    if (this.isReconnecting) return 'reconnecting';
    if (this.ws?.readyState === WebSocket.OPEN) return 'connected';
    return 'disconnected';
  }

  /**
   * Get max reconnect attempts
   */
  get maxReconnectAttempts(): number {
    return this.config.maxReconnectAttempts;
  }

  /**
   * Get connection latency
   */
  get latency(): number {
    if (this.lastPongTime && this.lastPingTime && this.lastPongTime > this.lastPingTime) {
      return this.lastPongTime - this.lastPingTime;
    }
    return -1;
  }

  private handleOpen(): void {
    console.log('[WebSocket] Connected successfully');
    this.isConnecting = false;
    this.isReconnecting = false;
    this.reconnectAttempts = 0;

    this.emit('connected');
    this.startHeartbeat();
    this.flushMessageQueue();
  }

  private handleMessage(event: MessageEvent): void {
    try {
      const message: WebSocketMessage = JSON.parse(event.data);

      // Handle ping/pong for heartbeat
      if (message.type === 'ping') {
        this.send({ type: 'pong', data: null });
        return;
      }

      if (message.type === 'pong') {
        this.lastPongTime = Date.now();

        // Clear heartbeat timeout since we got a response
        if (this.heartbeatTimeoutTimer) {
          clearTimeout(this.heartbeatTimeoutTimer);
          this.heartbeatTimeoutTimer = null;
        }
        return;
      }

      this.emit('message', message);
      this.emit(message.type, message.data);
    } catch (error) {
      console.error('[WebSocket] Failed to parse message:', error);
      this.emit('error', error);
    }
  }

  private handleError(event: Event): void {
    console.error('[WebSocket] Error event:', event);
    this.emit('error', new Error('WebSocket error'));
  }

  private handleClose(event: CloseEvent): void {
    console.log(
      `[WebSocket] Closed: ${event.code} - ${event.reason || 'No reason'} (clean: ${event.wasClean})`
    );

    this.isConnecting = false;
    this.clearAllTimers();

    this.emit('disconnected', {
      code: event.code,
      reason: event.reason,
    });

    // Attempt reconnection if enabled and not a clean close
    if (this.shouldReconnect && !event.wasClean && event.code !== 1000) {
      this.reconnect();
    }
  }

  private reconnect(): void {
    // Don't reconnect if already reconnecting or not allowed
    if (this.isReconnecting || !this.shouldReconnect || this.isConnecting) {
      console.log(
        '[WebSocket] Skipping reconnect (isReconnecting:',
        this.isReconnecting,
        'shouldReconnect:',
        this.shouldReconnect,
        'isConnecting:',
        this.isConnecting,
        ')'
      );
      return;
    }

    // Check if max attempts reached
    if (this.reconnectAttempts >= this.config.maxReconnectAttempts) {
      console.error('[WebSocket] Max reconnection attempts reached');
      this.isReconnecting = false;
      this.emit('reconnect_failed');
      return;
    }

    this.isReconnecting = true;
    this.reconnectAttempts++;

    // Exponential backoff with jitter (capped at 30s)
    const baseDelay = this.config.reconnectInterval * Math.pow(1.5, this.reconnectAttempts - 1);
    const jitter = Math.random() * 1000;
    const delay = Math.min(baseDelay + jitter, 30000);

    console.log(
      `[WebSocket] Reconnecting in ${Math.round(delay)}ms (attempt ${this.reconnectAttempts}/${this.config.maxReconnectAttempts})`
    );

    this.emit('reconnecting', {
      attempt: this.reconnectAttempts,
      delay: Math.round(delay),
    });

    // Clear any existing reconnect timer
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }

    this.reconnectTimer = setTimeout(async () => {
      this.reconnectTimer = null;

      try {
        console.log('[WebSocket] Attempting reconnection...');
        await this.connect();
        console.log('[WebSocket] Reconnection successful');
      } catch (error) {
        console.error('[WebSocket] Reconnection attempt failed:', error);
        this.isReconnecting = false;

        // Try again if we haven't hit max attempts
        if (this.reconnectAttempts < this.config.maxReconnectAttempts) {
          this.reconnect();
        } else {
          this.emit('reconnect_failed');
        }
      }
    }, delay);
  }

  private startHeartbeat(): void {
    this.stopHeartbeat();

    this.heartbeatTimer = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.lastPingTime = Date.now();
        this.send({ type: 'ping', data: null });

        // Set timeout to detect missing pong (5 seconds)
        this.heartbeatTimeoutTimer = setTimeout(() => {
          const timeSinceLastPong = Date.now() - this.lastPongTime;

          // Only close if we haven't received a pong recently
          if (timeSinceLastPong > this.config.heartbeatInterval) {
            console.warn('[WebSocket] Heartbeat timeout - no pong received, closing connection');
            this.ws?.close(1006, 'Heartbeat timeout');
          }
        }, 5000);
      }
    }, this.config.heartbeatInterval);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }

    if (this.heartbeatTimeoutTimer) {
      clearTimeout(this.heartbeatTimeoutTimer);
      this.heartbeatTimeoutTimer = null;
    }
  }

  private clearAllTimers(): void {
    this.stopHeartbeat();

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.connectionTimeoutTimer) {
      clearTimeout(this.connectionTimeoutTimer);
      this.connectionTimeoutTimer = null;
    }
  }

  private cleanupConnection(): void {
    // Remove event listeners to prevent leaks
    if (this.ws) {
      this.ws.onopen = null;
      this.ws.onmessage = null;
      this.ws.onerror = null;
      this.ws.onclose = null;

      if (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING) {
        try {
          this.ws.close();
        } catch (e) {
          // Ignore errors during cleanup
        }
      }
    }
  }

  private queueMessage(message: WebSocketMessage): void {
    this.messageQueue.push(message);

    // Limit queue size
    if (this.messageQueue.length > this.config.messageQueueSize) {
      const removed = this.messageQueue.shift();
      console.warn('[WebSocket] Message queue full, dropped oldest message:', removed?.type);
    }
  }

  private flushMessageQueue(): void {
    console.log(`[WebSocket] Flushing ${this.messageQueue.length} queued messages`);

    while (this.messageQueue.length > 0 && this.ws?.readyState === WebSocket.OPEN) {
      const message = this.messageQueue.shift();
      if (message) {
        try {
          this.ws.send(JSON.stringify(message));
        } catch (error) {
          console.error('[WebSocket] Failed to flush message:', error);
          // Put it back if send failed
          this.messageQueue.unshift(message);
          break;
        }
      }
    }
  }
}

// Singleton instance for the application
let wsTransport: WebSocketTransport | null = null;

export function getWebSocketTransport(config?: WebSocketConfig): WebSocketTransport {
  if (!wsTransport && config) {
    wsTransport = new WebSocketTransport(config);
  }

  if (!wsTransport) {
    throw new Error('WebSocket transport not initialized');
  }

  return wsTransport;
}

export function closeWebSocketTransport(): void {
  if (wsTransport) {
    wsTransport.disconnect();
    wsTransport = null;
  }
}
