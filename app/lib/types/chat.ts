export type ConnectionStatus = 'connected' | 'connecting' | 'disconnected';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  artifacts?: MessageArtifact[];
  error?: string;
  metadata?: Record<string, any>;
}

export interface MessageArtifact {
  type: 'story' | 'issue' | 'clarification' | 'plan';
  data: any;
}

export interface ConversationContext {
  sessionId: string;
  startedAt: string;
  lastActivity: string;
  messageCount: number;
  currentState?: 'idle' | 'understanding' | 'clarifying' | 'planning' | 'creating';
}

export interface ToolExecution {
  toolName: string;
  status: 'pending' | 'running' | 'success' | 'error';
  startedAt: string;
  completedAt?: string;
  result?: any;
  error?: string;
}

export interface StoryData {
  id: string;
  title: string;
  epic: string;
  priority: 'P0' | 'P1' | 'P2' | 'P3';
  url?: string;
  acceptanceCriteria?: string[];
  technicalDetails?: string;
}

export interface IssueData {
  id: string;
  title: string;
  number: number;
  url: string;
  labels?: string[];
  assignees?: string[];
}
