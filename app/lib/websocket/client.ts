import { EventEmitter } from 'events';

export interface WebSocketMessage {
  type: 'message' | 'tool_execution' | 'status' | 'error' | 'ping' | 'pong';
  data: any;
  timestamp: string;
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
  private messageQueue: WebSocketMessage[] = [];
  private isConnecting = false;
  private isReconnecting = false;
  private lastPingTime = 0;
  private lastPongTime = 0;

  constructor(config: WebSocketConfig) {
    super();
    
    this.config = {
      url: config.url,
      reconnect: config.reconnect ?? true,
      reconnectInterval: config.reconnectInterval ?? 1000,
      maxReconnectAttempts: config.maxReconnectAttempts ?? 10,
      heartbeatInterval: config.heartbeatInterval ?? 30000,
      messageQueueSize: config.messageQueueSize ?? 100
    };
  }

  /**
   * Connect to WebSocket server
   */
  async connect(): Promise<void> {
    if (this.isConnecting || this.ws?.readyState === WebSocket.OPEN) {
      return;
    }

    this.isConnecting = true;
    this.emit('connecting');

    try {
      this.ws = new WebSocket(this.config.url);
      
      this.ws.onopen = this.handleOpen.bind(this);
      this.ws.onmessage = this.handleMessage.bind(this);
      this.ws.onerror = this.handleError.bind(this);
      this.ws.onclose = this.handleClose.bind(this);

      // Wait for connection to be established
      await new Promise<void>((resolve, reject) => {
        const timeout = setTimeout(() => {
          reject(new Error('Connection timeout'));
        }, 10000);

        this.once('connected', () => {
          clearTimeout(timeout);
          resolve();
        });

        this.once('error', (error) => {
          clearTimeout(timeout);
          reject(error);
        });
      });
    } catch (error) {
      this.isConnecting = false;
      throw error;
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    this.config.reconnect = false;
    this.clearTimers();
    
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
    
    this.emit('disconnected');
  }

  /**
   * Send a message through WebSocket
   */
  send(message: Omit<WebSocketMessage, 'timestamp'>): void {
    const fullMessage: WebSocketMessage = {
      ...message,
      timestamp: new Date().toISOString()
    };

    if (this.ws?.readyState === WebSocket.OPEN) {
      try {
        this.ws.send(JSON.stringify(fullMessage));
        this.emit('message_sent', fullMessage);
      } catch (error) {
        console.error('Failed to send message:', error);
        this.queueMessage(fullMessage);
      }
    } else {
      this.queueMessage(fullMessage);
      
      // Attempt to reconnect if not already doing so
      if (this.config.reconnect && !this.isReconnecting) {
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
   * Get connection latency
   */
  get latency(): number {
    if (this.lastPongTime && this.lastPingTime) {
      return this.lastPongTime - this.lastPingTime;
    }
    return -1;
  }

  private handleOpen(): void {
    console.log('WebSocket connected');
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
        return;
      }
      
      this.emit('message', message);
      this.emit(message.type, message.data);
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error);
      this.emit('error', error);
    }
  }

  private handleError(event: Event): void {
    console.error('WebSocket error:', event);
    this.emit('error', new Error('WebSocket error'));
  }

  private handleClose(event: CloseEvent): void {
    console.log(`WebSocket closed: ${event.code} - ${event.reason}`);
    this.isConnecting = false;
    this.clearTimers();
    
    this.emit('disconnected', {
      code: event.code,
      reason: event.reason
    });
    
    // Attempt reconnection if enabled
    if (this.config.reconnect && !event.wasClean) {
      this.reconnect();
    }
  }

  private reconnect(): void {
    if (this.isReconnecting || !this.config.reconnect) {
      return;
    }
    
    if (this.reconnectAttempts >= this.config.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      this.emit('reconnect_failed');
      return;
    }
    
    this.isReconnecting = true;
    this.reconnectAttempts++;
    
    // Exponential backoff with jitter
    const delay = Math.min(
      this.config.reconnectInterval * Math.pow(2, this.reconnectAttempts - 1) + 
      Math.random() * 1000,
      30000 // Max 30 seconds
    );
    
    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
    this.emit('reconnecting', {
      attempt: this.reconnectAttempts,
      delay
    });
    
    this.reconnectTimer = setTimeout(async () => {
      try {
        await this.connect();
      } catch (error) {
        console.error('Reconnection failed:', error);
        this.reconnect();
      }
    }, delay);
  }

  private startHeartbeat(): void {
    this.stopHeartbeat();
    
    this.heartbeatTimer = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.lastPingTime = Date.now();
        this.send({ type: 'ping', data: null });
        
        // Check for pong timeout
        setTimeout(() => {
          if (Date.now() - this.lastPongTime > this.config.heartbeatInterval * 2) {
            console.warn('Heartbeat timeout - connection may be dead');
            this.ws?.close();
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
  }

  private clearTimers(): void {
    this.stopHeartbeat();
    
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  private queueMessage(message: WebSocketMessage): void {
    this.messageQueue.push(message);
    
    // Limit queue size
    if (this.messageQueue.length > this.config.messageQueueSize) {
      this.messageQueue.shift();
    }
  }

  private flushMessageQueue(): void {
    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift();
      if (message) {
        this.send(message);
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
