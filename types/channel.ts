/**
 * Agent Foundry - Channel Type Definitions
 * Types for communication channels and integrations
 */

export type ChannelType =
  | 'slack'
  | 'teams'
  | 'whatsapp'
  | 'twilio'
  | 'genesys'
  | 'aws_connect'
  | 'custom';

export type ChannelStatus = 'connected' | 'disconnected' | 'error' | 'configuring';

export interface Channel {
  id: string;
  name: string;
  display_name: string;
  type: ChannelType;
  status: ChannelStatus;

  // Configuration
  config: ChannelConfig;
  auth: ChannelAuth;

  // Routing
  agent_mappings: AgentMapping[];
  default_agent_id?: string;

  // Environment overrides
  environment_config?: {
    dev?: Partial<ChannelConfig>;
    staging?: Partial<ChannelConfig>;
    prod?: Partial<ChannelConfig>;
  };

  // Activity
  messages_24h: number;
  avg_response_time_ms: number;
  error_rate: number;

  // Metadata
  created_at: string;
  updated_at: string;
  last_activity_at?: string;

  // Icon & branding
  icon_url?: string;
  color?: string;
}

export interface ChannelConfig {
  webhook_url?: string;
  api_endpoint?: string;
  phone_number?: string;
  workspace_id?: string;
  app_id?: string;
  custom_fields?: Record<string, any>;
}

export interface ChannelAuth {
  type: 'oauth' | 'api_key' | 'bearer_token' | 'basic' | 'custom';
  credentials: {
    api_key?: string;
    access_token?: string;
    refresh_token?: string;
    client_id?: string;
    client_secret?: string;
    username?: string;
    password?: string;
  };
  expires_at?: string;
}

export interface AgentMapping {
  id: string;
  channel_id: string;
  agent_id: string;
  agent_name: string;

  // Routing rules
  trigger_keywords?: string[];
  trigger_regex?: string;
  route_by_user?: string[];
  route_by_channel?: string[];

  // Priority
  priority: number;
  is_default: boolean;
}

export interface ChannelMessage {
  id: string;
  channel_id: string;
  channel_type: ChannelType;

  // Message data
  direction: 'inbound' | 'outbound';
  content: string;
  user_id?: string;
  user_name?: string;

  // Timing
  received_at: string;
  processed_at?: string;
  responded_at?: string;

  // Agent execution
  agent_id?: string;
  trace_id?: string;
  response?: string;
  status: 'pending' | 'processing' | 'responded' | 'error';
  error_message?: string;
}

export interface ChannelActivity {
  channel_id: string;
  timestamp: string;
  event_type: 'message' | 'connection' | 'error' | 'config_change';
  description: string;
  metadata?: Record<string, any>;
}
