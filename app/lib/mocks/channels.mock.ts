/**
 * Agent Foundry - Mock Channel Data
 * Sample communication channels and integrations
 */

import { Channel, ChannelMessage, ChannelActivity, ChannelType } from '@/types';

export const mockChannels: Channel[] = [
  {
    id: 'chn-001',
    name: 'main-workspace',
    display_name: 'Main Slack Workspace',
    type: 'slack',
    status: 'connected',
    config: {
      workspace_id: 'T0123456789',
      app_id: 'A0987654321',
    },
    auth: {
      type: 'oauth',
      credentials: {
        access_token: 'xoxb-***',
        refresh_token: 'xoxr-***',
      },
      expires_at: '2025-06-15T00:00:00Z',
    },
    agent_mappings: [
      {
        id: 'map-001',
        channel_id: 'chn-001',
        agent_id: 'agt-001',
        agent_name: 'customer-support-agent',
        trigger_keywords: ['order', 'support', 'help'],
        priority: 1,
        is_default: true,
      },
      {
        id: 'map-002',
        channel_id: 'chn-001',
        agent_id: 'agt-005',
        agent_name: 'it-helpdesk-agent',
        trigger_keywords: ['password', 'reset', 'access', 'laptop'],
        priority: 2,
        is_default: false,
      },
    ],
    default_agent_id: 'agt-001',
    environment_config: {
      dev: { workspace_id: 'T0123456789-dev' },
      staging: { workspace_id: 'T0123456789-staging' },
      prod: { workspace_id: 'T0123456789' },
    },
    messages_24h: 1247,
    avg_response_time_ms: 1823,
    error_rate: 0.018,
    created_at: '2024-11-01T10:00:00Z',
    updated_at: '2025-01-15T14:30:00Z',
    last_activity_at: '2025-01-16T11:45:23Z',
    icon_url: '/icons/slack.svg',
    color: '#4A154B',
  },
  {
    id: 'chn-002',
    name: 'sales-team',
    display_name: 'Sales Team (Microsoft Teams)',
    type: 'teams',
    status: 'connected',
    config: {
      app_id: 'teams-app-id-123',
    },
    auth: {
      type: 'oauth',
      credentials: {
        access_token: 'ey***',
        refresh_token: 'ref***',
      },
      expires_at: '2025-05-20T00:00:00Z',
    },
    agent_mappings: [
      {
        id: 'map-003',
        channel_id: 'chn-002',
        agent_id: 'agt-002',
        agent_name: 'sales-qualifying-agent',
        priority: 1,
        is_default: true,
      },
    ],
    default_agent_id: 'agt-002',
    messages_24h: 543,
    avg_response_time_ms: 2341,
    error_rate: 0.059,
    created_at: '2024-12-10T09:00:00Z',
    updated_at: '2025-01-14T16:45:00Z',
    last_activity_at: '2025-01-16T10:32:11Z',
    icon_url: '/icons/teams.svg',
    color: '#6264A7',
  },
  {
    id: 'chn-003',
    name: 'customer-sms',
    display_name: 'Customer SMS (Twilio)',
    type: 'twilio',
    status: 'connected',
    config: {
      phone_number: '+1-555-0123',
    },
    auth: {
      type: 'api_key',
      credentials: {
        api_key: 'SK***',
        client_id: 'AC***',
      },
    },
    agent_mappings: [
      {
        id: 'map-004',
        channel_id: 'chn-003',
        agent_id: 'agt-001',
        agent_name: 'customer-support-agent',
        priority: 1,
        is_default: true,
      },
    ],
    default_agent_id: 'agt-001',
    messages_24h: 234,
    avg_response_time_ms: 1456,
    error_rate: 0.008,
    created_at: '2024-12-01T14:00:00Z',
    updated_at: '2025-01-10T11:20:00Z',
    last_activity_at: '2025-01-16T09:15:42Z',
    icon_url: '/icons/twilio.svg',
    color: '#F22F46',
  },
  {
    id: 'chn-004',
    name: 'support-email',
    display_name: 'Support Email (support@company.com)',
    type: 'custom',
    status: 'connected',
    config: {
      api_endpoint: 'smtp.company.com',
      custom_fields: {
        email_address: 'support@company.com',
        protocol: 'IMAP',
        port: 993,
      },
    },
    auth: {
      type: 'basic',
      credentials: {
        username: 'support@company.com',
        password: '***',
      },
    },
    agent_mappings: [
      {
        id: 'map-005',
        channel_id: 'chn-004',
        agent_id: 'agt-001',
        agent_name: 'customer-support-agent',
        priority: 1,
        is_default: true,
      },
      {
        id: 'map-006',
        channel_id: 'chn-004',
        agent_id: 'agt-004',
        agent_name: 'hr-onboarding-agent',
        trigger_keywords: ['onboarding', 'new hire', 'orientation'],
        priority: 2,
        is_default: false,
      },
    ],
    default_agent_id: 'agt-001',
    messages_24h: 892,
    avg_response_time_ms: 2987,
    error_rate: 0.026,
    created_at: '2024-10-15T08:00:00Z',
    updated_at: '2025-01-13T15:30:00Z',
    last_activity_at: '2025-01-16T11:52:03Z',
    icon_url: '/icons/email.svg',
    color: '#EA4335',
  },
  {
    id: 'chn-005',
    name: 'contact-center',
    display_name: 'AWS Connect Contact Center',
    type: 'aws_connect',
    status: 'connected',
    config: {
      api_endpoint: 'https://contact-center.us-west-2.amazonaws.com',
      custom_fields: {
        instance_id: 'arn:aws:connect:us-west-2:123456789012:instance/abcd-1234',
        contact_flow_id: 'flow-xyz-789',
      },
    },
    auth: {
      type: 'bearer_token',
      credentials: {
        access_token: 'aws-token-***',
      },
    },
    agent_mappings: [
      {
        id: 'map-007',
        channel_id: 'chn-005',
        agent_id: 'agt-001',
        agent_name: 'customer-support-agent',
        priority: 1,
        is_default: true,
      },
    ],
    default_agent_id: 'agt-001',
    messages_24h: 567,
    avg_response_time_ms: 3421,
    error_rate: 0.042,
    created_at: '2024-11-20T10:30:00Z',
    updated_at: '2025-01-12T09:15:00Z',
    last_activity_at: '2025-01-16T08:22:34Z',
    icon_url: '/icons/aws.svg',
    color: '#FF9900',
  },
  {
    id: 'chn-006',
    name: 'genesys-cloud',
    display_name: 'Genesys Cloud Voice',
    type: 'genesys',
    status: 'error',
    config: {
      api_endpoint: 'https://api.mypurecloud.com',
      custom_fields: {
        org_id: 'org-123456',
        queue_id: 'queue-abc-789',
      },
    },
    auth: {
      type: 'oauth',
      credentials: {
        client_id: 'client-***',
        client_secret: 'secret-***',
      },
    },
    agent_mappings: [
      {
        id: 'map-008',
        channel_id: 'chn-006',
        agent_id: 'agt-001',
        agent_name: 'customer-support-agent',
        priority: 1,
        is_default: true,
      },
    ],
    default_agent_id: 'agt-001',
    messages_24h: 0,
    avg_response_time_ms: 0,
    error_rate: 1.0,
    created_at: '2025-01-05T11:00:00Z',
    updated_at: '2025-01-15T16:30:00Z',
    last_activity_at: '2025-01-15T16:30:00Z',
    icon_url: '/icons/genesys.svg',
    color: '#FF4F1F',
  },
];

export const mockChannelMessages: ChannelMessage[] = [
  {
    id: 'msg-001',
    channel_id: 'chn-001',
    channel_type: 'slack',
    direction: 'inbound',
    content: 'What is the status of my order #12345?',
    user_id: 'U0123456',
    user_name: 'john.doe',
    received_at: '2025-01-16T10:15:23.000Z',
    processed_at: '2025-01-16T10:15:23.234Z',
    responded_at: '2025-01-16T10:15:27.234Z',
    agent_id: 'agt-001',
    trace_id: 'trace-001',
    response: 'Your order #12345 is currently in transit and expected to arrive tomorrow.',
    status: 'responded',
  },
  {
    id: 'msg-002',
    channel_id: 'chn-003',
    channel_type: 'twilio',
    direction: 'inbound',
    content: 'I need help resetting my password',
    user_id: '+1-555-9876',
    received_at: '2025-01-16T09:30:12.000Z',
    processed_at: '2025-01-16T09:30:12.456Z',
    responded_at: '2025-01-16T09:30:15.678Z',
    agent_id: 'agt-005',
    trace_id: 'trace-003',
    response: 'I can help with that. Please check your email for a password reset link.',
    status: 'responded',
  },
  {
    id: 'msg-003',
    channel_id: 'chn-004',
    channel_type: 'custom',
    direction: 'inbound',
    content: 'When is my orientation scheduled?',
    user_id: 'new.employee@company.com',
    user_name: 'New Employee',
    received_at: '2025-01-16T08:45:00.000Z',
    status: 'processing',
    agent_id: 'agt-004',
    trace_id: 'trace-004',
  },
  {
    id: 'msg-004',
    channel_id: 'chn-002',
    channel_type: 'teams',
    direction: 'inbound',
    content: 'Can you help me qualify this lead?',
    user_id: 'sarah.chen@company.com',
    user_name: 'Sarah Chen',
    received_at: '2025-01-16T11:20:00.000Z',
    processed_at: '2025-01-16T11:20:00.123Z',
    status: 'error',
    agent_id: 'agt-002',
    error_message: 'Salesforce API timeout',
  },
];

export const mockChannelActivity: ChannelActivity[] = [
  {
    channel_id: 'chn-001',
    timestamp: '2025-01-16T10:15:23.234Z',
    event_type: 'message',
    description: 'New message from john.doe: "What is the status of my order #12345?"',
    metadata: { user: 'john.doe', trace_id: 'trace-001' },
  },
  {
    channel_id: 'chn-006',
    timestamp: '2025-01-15T16:30:00.000Z',
    event_type: 'error',
    description: 'Connection failed: OAuth token expired',
    metadata: { error_code: 'OAUTH_EXPIRED' },
  },
  {
    channel_id: 'chn-001',
    timestamp: '2025-01-15T14:30:00.000Z',
    event_type: 'config_change',
    description: 'Updated agent mapping for customer-support-agent',
    metadata: { changed_by: 'nwalker85' },
  },
  {
    channel_id: 'chn-005',
    timestamp: '2025-01-12T09:15:00.000Z',
    event_type: 'connection',
    description: 'Successfully reconnected to AWS Connect',
    metadata: { connection_id: 'conn-abc-123' },
  },
];

// Helper functions
export function getChannelById(id: string): Channel | undefined {
  return mockChannels.find((channel) => channel.id === id);
}

export function getChannelsByType(type: ChannelType): Channel[] {
  return mockChannels.filter((channel) => channel.type === type);
}

export function getChannelsByStatus(status: string): Channel[] {
  return mockChannels.filter((channel) => channel.status === status);
}

export function getActiveChannels(): Channel[] {
  return mockChannels.filter((channel) => channel.status === 'connected');
}

export function getMessagesByChannel(channelId: string): ChannelMessage[] {
  return mockChannelMessages.filter((msg) => msg.channel_id === channelId);
}

export function getChannelActivity(channelId: string, limit: number = 10): ChannelActivity[] {
  return mockChannelActivity
    .filter((activity) => activity.channel_id === channelId)
    .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
    .slice(0, limit);
}

export function getChannelStats() {
  return {
    total_channels: mockChannels.length,
    connected: mockChannels.filter((c) => c.status === 'connected').length,
    disconnected: mockChannels.filter((c) => c.status === 'disconnected').length,
    errors: mockChannels.filter((c) => c.status === 'error').length,
    total_messages_24h: mockChannels.reduce((sum, c) => sum + c.messages_24h, 0),
    avg_response_time_ms:
      mockChannels.reduce((sum, c) => sum + c.avg_response_time_ms, 0) / mockChannels.length,
  };
}
