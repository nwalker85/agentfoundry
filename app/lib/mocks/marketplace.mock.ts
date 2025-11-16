/**
 * Agent Foundry - Mock Marketplace Data
 * Agent templates, tools, and integrations available in marketplace
 */

import { AgentTemplate } from '@/types';

export interface MarketplaceItem {
  id: string;
  type: 'agent' | 'tool' | 'domain' | 'integration';
  name: string;
  display_name: string;
  description: string;
  category: string;
  author: string;
  author_verified: boolean;
  verified: boolean;

  // Stats
  downloads: number;
  rating: number;
  review_count: number;

  // Pricing
  price: number; // 0 for free
  pricing_model: 'free' | 'one_time' | 'subscription' | 'usage_based';

  // Metadata
  version: string;
  created_at: string;
  updated_at: string;
  tags: string[];

  // Media
  icon_url?: string;
  screenshot_urls?: string[];
  demo_url?: string;
  documentation_url?: string;

  // Installation
  install_count: number;
  compatible_versions: string[];

  // Content (varies by type)
  content?: any;
}

export const mockMarketplaceItems: MarketplaceItem[] = [
  // Popular Agent Templates
  {
    id: 'mkt-001',
    type: 'agent',
    name: 'customer-support-starter',
    display_name: 'Customer Support Starter',
    description: 'Pre-configured customer support agent with FAQ knowledge base, order tracking, and ticket creation. Includes Slack and email channel integrations.',
    category: 'Customer Service',
    author: 'Agent Foundry Team',
    author_verified: true,
    verified: true,
    downloads: 15234,
    rating: 4.8,
    review_count: 1247,
    price: 0,
    pricing_model: 'free',
    version: '3.2.0',
    created_at: '2024-06-15T10:00:00Z',
    updated_at: '2025-01-10T14:30:00Z',
    tags: ['customer-service', 'support', 'chat', 'faq', 'ticketing'],
    icon_url: '/marketplace/customer-support.svg',
    screenshot_urls: [
      '/marketplace/screenshots/customer-support-1.png',
      '/marketplace/screenshots/customer-support-2.png',
    ],
    demo_url: 'https://demo.agentfoundry.com/customer-support',
    documentation_url: 'https://docs.agentfoundry.com/templates/customer-support',
    install_count: 15234,
    compatible_versions: ['0.8.x', '0.9.x'],
    content: {
      graph_yaml: '# Agent YAML definition...',
      default_tools: ['slack', 'email', 'notion', 'web_search'],
      default_models: ['gpt-4o-mini'],
    },
  },
  {
    id: 'mkt-002',
    type: 'agent',
    name: 'sales-qualifier-pro',
    display_name: 'Sales Lead Qualifier Pro',
    description: 'Advanced lead qualification agent with CRM integration, scoring logic, and automated demo scheduling. Integrates with Salesforce, HubSpot, and Calendly.',
    category: 'Sales',
    author: 'Agent Foundry Team',
    author_verified: true,
    verified: true,
    downloads: 8921,
    rating: 4.7,
    review_count: 672,
    price: 0,
    pricing_model: 'free',
    version: '2.5.1',
    created_at: '2024-07-22T11:00:00Z',
    updated_at: '2025-01-08T16:15:00Z',
    tags: ['sales', 'lead-qualification', 'crm', 'automation'],
    icon_url: '/marketplace/sales-qualifier.svg',
    documentation_url: 'https://docs.agentfoundry.com/templates/sales-qualifier',
    install_count: 8921,
    compatible_versions: ['0.8.x', '0.9.x'],
    content: {
      graph_yaml: '# Agent YAML definition...',
      default_tools: ['salesforce', 'hubspot', 'calendar', 'email'],
      default_models: ['gpt-4o', 'claude-3-opus'],
    },
  },
  {
    id: 'mkt-003',
    type: 'agent',
    name: 'data-analyst-sql',
    display_name: 'SQL Data Analyst',
    description: 'Natural language to SQL agent with support for PostgreSQL, MySQL, BigQuery, and Snowflake. Includes chart generation and export capabilities.',
    category: 'Analytics',
    author: 'DataViz Labs',
    author_verified: true,
    verified: true,
    downloads: 6234,
    rating: 4.9,
    review_count: 523,
    price: 0,
    pricing_model: 'free',
    version: '4.1.0',
    created_at: '2024-05-10T09:00:00Z',
    updated_at: '2025-01-12T10:20:00Z',
    tags: ['analytics', 'sql', 'data', 'reporting', 'visualization'],
    icon_url: '/marketplace/data-analyst.svg',
    demo_url: 'https://demo.agentfoundry.com/data-analyst',
    documentation_url: 'https://docs.agentfoundry.com/templates/data-analyst',
    install_count: 6234,
    compatible_versions: ['0.8.x', '0.9.x'],
    content: {
      graph_yaml: '# Agent YAML definition...',
      default_tools: ['sql_database', 'chart_generator', 'csv_export'],
      default_models: ['gpt-4o'],
    },
  },
  {
    id: 'mkt-004',
    type: 'agent',
    name: 'hr-onboarding-complete',
    display_name: 'HR Onboarding Complete',
    description: 'Comprehensive employee onboarding agent with document collection, orientation scheduling, and IT provisioning workflows.',
    category: 'Human Resources',
    author: 'HR Automation Co.',
    author_verified: true,
    verified: true,
    downloads: 4532,
    rating: 4.6,
    review_count: 389,
    price: 29.99,
    pricing_model: 'one_time',
    version: '2.3.0',
    created_at: '2024-08-14T13:00:00Z',
    updated_at: '2025-01-05T11:45:00Z',
    tags: ['hr', 'onboarding', 'automation', 'workflows'],
    icon_url: '/marketplace/hr-onboarding.svg',
    documentation_url: 'https://docs.agentfoundry.com/templates/hr-onboarding',
    install_count: 4532,
    compatible_versions: ['0.8.x', '0.9.x'],
    content: {
      graph_yaml: '# Agent YAML definition...',
      default_tools: ['workday', 'docusign', 'email', 'calendar', 'active_directory'],
      default_models: ['gpt-4o-mini'],
    },
  },
  {
    id: 'mkt-005',
    type: 'agent',
    name: 'code-reviewer-ai',
    display_name: 'AI Code Reviewer',
    description: 'Automated code review agent that analyzes pull requests for bugs, security issues, performance problems, and style violations. Supports 15+ languages.',
    category: 'Development',
    author: 'DevTools Inc.',
    author_verified: true,
    verified: true,
    downloads: 7891,
    rating: 4.8,
    review_count: 645,
    price: 49.99,
    pricing_model: 'subscription',
    version: '3.0.2',
    created_at: '2024-09-01T10:00:00Z',
    updated_at: '2025-01-14T09:30:00Z',
    tags: ['development', 'code-review', 'security', 'quality'],
    icon_url: '/marketplace/code-reviewer.svg',
    demo_url: 'https://demo.agentfoundry.com/code-reviewer',
    documentation_url: 'https://docs.agentfoundry.com/templates/code-reviewer',
    install_count: 7891,
    compatible_versions: ['0.8.x', '0.9.x'],
    content: {
      graph_yaml: '# Agent YAML definition...',
      default_tools: ['github', 'sonarqube', 'security_scanner'],
      default_models: ['gpt-4o', 'claude-3-opus'],
    },
  },
  {
    id: 'mkt-006',
    type: 'agent',
    name: 'invoice-processor-ocr',
    display_name: 'Invoice Processor with OCR',
    description: 'Automated invoice processing with OCR extraction, validation, approval routing, and QuickBooks integration.',
    category: 'Finance',
    author: 'FinTech Solutions',
    author_verified: true,
    verified: true,
    downloads: 3421,
    rating: 4.4,
    review_count: 287,
    price: 0,
    pricing_model: 'free',
    version: '2.1.0',
    created_at: '2024-10-05T11:00:00Z',
    updated_at: '2025-01-10T15:20:00Z',
    tags: ['finance', 'ocr', 'invoicing', 'automation'],
    icon_url: '/marketplace/invoice-processor.svg',
    documentation_url: 'https://docs.agentfoundry.com/templates/invoice-processor',
    install_count: 3421,
    compatible_versions: ['0.8.x', '0.9.x'],
    content: {
      graph_yaml: '# Agent YAML definition...',
      default_tools: ['ocr_engine', 'quickbooks', 'email'],
      default_models: ['gpt-4o'],
    },
  },
  {
    id: 'mkt-007',
    type: 'agent',
    name: 'meeting-summarizer-pro',
    display_name: 'Meeting Summarizer Pro',
    description: 'Transcribe and summarize meetings from Zoom, Teams, or Google Meet. Generates action items, key decisions, and follow-up emails.',
    category: 'Productivity',
    author: 'MeetingAI Corp',
    author_verified: true,
    verified: true,
    downloads: 9234,
    rating: 4.7,
    review_count: 731,
    price: 19.99,
    pricing_model: 'subscription',
    version: '2.8.0',
    created_at: '2024-07-18T14:00:00Z',
    updated_at: '2025-01-11T12:10:00Z',
    tags: ['productivity', 'meetings', 'transcription', 'summarization'],
    icon_url: '/marketplace/meeting-summarizer.svg',
    demo_url: 'https://demo.agentfoundry.com/meeting-summarizer',
    documentation_url: 'https://docs.agentfoundry.com/templates/meeting-summarizer',
    install_count: 9234,
    compatible_versions: ['0.8.x', '0.9.x'],
    content: {
      graph_yaml: '# Agent YAML definition...',
      default_tools: ['transcription', 'email', 'calendar'],
      default_models: ['gpt-4o', 'whisper'],
    },
  },
  {
    id: 'mkt-008',
    type: 'agent',
    name: 'content-moderator-ml',
    display_name: 'AI Content Moderator',
    description: 'Real-time content moderation for text, images, and video. Detects policy violations, toxic content, and spam with 99.4% accuracy.',
    category: 'Safety',
    author: 'SafetyFirst AI',
    author_verified: true,
    verified: true,
    downloads: 5623,
    rating: 4.9,
    review_count: 478,
    price: 99.99,
    pricing_model: 'subscription',
    version: '4.2.1',
    created_at: '2024-06-22T10:00:00Z',
    updated_at: '2025-01-15T11:40:00Z',
    tags: ['moderation', 'safety', 'content', 'ml'],
    icon_url: '/marketplace/content-moderator.svg',
    documentation_url: 'https://docs.agentfoundry.com/templates/content-moderator',
    install_count: 5623,
    compatible_versions: ['0.8.x', '0.9.x'],
    content: {
      graph_yaml: '# Agent YAML definition...',
      default_tools: ['moderation_api', 'image_classifier', 'alert_system'],
      default_models: ['gpt-4o', 'claude-3-haiku'],
    },
  },
  {
    id: 'mkt-009',
    type: 'agent',
    name: 'social-media-manager',
    display_name: 'Social Media Manager',
    description: 'Automated social media monitoring and response agent for Twitter, LinkedIn, and Facebook. Handles mentions, DMs, and engagement.',
    category: 'Marketing',
    author: 'SocialAI Labs',
    author_verified: false,
    verified: false,
    downloads: 2134,
    rating: 4.2,
    review_count: 167,
    price: 0,
    pricing_model: 'free',
    version: '1.5.0',
    created_at: '2024-11-12T09:00:00Z',
    updated_at: '2025-01-09T10:30:00Z',
    tags: ['social-media', 'marketing', 'engagement', 'automation'],
    icon_url: '/marketplace/social-media.svg',
    documentation_url: 'https://docs.agentfoundry.com/templates/social-media',
    install_count: 2134,
    compatible_versions: ['0.8.x', '0.9.x'],
    content: {
      graph_yaml: '# Agent YAML definition...',
      default_tools: ['twitter_api', 'sentiment_analysis', 'notification'],
      default_models: ['gpt-4o-mini'],
    },
  },
  {
    id: 'mkt-010',
    type: 'agent',
    name: 'it-helpdesk-auto',
    display_name: 'IT Helpdesk Automation',
    description: 'Automated IT support agent that resolves common issues like password resets, VPN setup, and software installations. Integrates with Active Directory and Jira.',
    category: 'IT',
    author: 'ITOps Solutions',
    author_verified: true,
    verified: true,
    downloads: 6782,
    rating: 4.5,
    review_count: 534,
    price: 0,
    pricing_model: 'free',
    version: '3.1.2',
    created_at: '2024-08-05T11:30:00Z',
    updated_at: '2025-01-12T10:55:00Z',
    tags: ['it', 'helpdesk', 'support', 'automation'],
    icon_url: '/marketplace/it-helpdesk.svg',
    documentation_url: 'https://docs.agentfoundry.com/templates/it-helpdesk',
    install_count: 6782,
    compatible_versions: ['0.8.x', '0.9.x'],
    content: {
      graph_yaml: '# Agent YAML definition...',
      default_tools: ['jira', 'active_directory', 'knowledge_base'],
      default_models: ['gpt-4o', 'gpt-4o-mini'],
    },
  },

  // Tools & Integrations
  {
    id: 'mkt-101',
    type: 'tool',
    name: 'zendesk-integration',
    display_name: 'Zendesk Integration',
    description: 'Complete Zendesk integration for ticket management, customer lookup, and knowledge base search.',
    category: 'Customer Service',
    author: 'Zendesk',
    author_verified: true,
    verified: true,
    downloads: 7234,
    rating: 4.6,
    review_count: 523,
    price: 0,
    pricing_model: 'free',
    version: '2.5.0',
    created_at: '2024-09-10T10:00:00Z',
    updated_at: '2025-01-14T11:20:00Z',
    tags: ['support', 'helpdesk', 'tickets', 'integration'],
    icon_url: '/marketplace/zendesk.svg',
    documentation_url: 'https://docs.agentfoundry.com/tools/zendesk',
    install_count: 7234,
    compatible_versions: ['0.8.x', '0.9.x'],
  },
  {
    id: 'mkt-102',
    type: 'tool',
    name: 'hubspot-crm',
    display_name: 'HubSpot CRM',
    description: 'HubSpot integration for contact management, deal tracking, and marketing automation.',
    category: 'Sales',
    author: 'HubSpot',
    author_verified: true,
    verified: true,
    downloads: 9823,
    rating: 4.7,
    review_count: 687,
    price: 0,
    pricing_model: 'free',
    version: '3.7.2',
    created_at: '2024-07-15T09:00:00Z',
    updated_at: '2025-01-10T14:30:00Z',
    tags: ['crm', 'sales', 'marketing', 'integration'],
    icon_url: '/marketplace/hubspot.svg',
    documentation_url: 'https://docs.agentfoundry.com/tools/hubspot',
    install_count: 9823,
    compatible_versions: ['0.8.x', '0.9.x'],
  },
  {
    id: 'mkt-103',
    type: 'tool',
    name: 'stripe-payments',
    display_name: 'Stripe Payments',
    description: 'Stripe integration for payment processing, subscription management, and invoice generation.',
    category: 'Finance',
    author: 'Stripe',
    author_verified: true,
    verified: true,
    downloads: 14523,
    rating: 4.9,
    review_count: 1023,
    price: 0,
    pricing_model: 'free',
    version: '5.1.0',
    created_at: '2024-06-01T10:00:00Z',
    updated_at: '2025-01-13T15:45:00Z',
    tags: ['payments', 'billing', 'subscriptions', 'integration'],
    icon_url: '/marketplace/stripe.svg',
    documentation_url: 'https://docs.agentfoundry.com/tools/stripe',
    install_count: 14523,
    compatible_versions: ['0.8.x', '0.9.x'],
  },
  {
    id: 'mkt-104',
    type: 'tool',
    name: 'datadog-monitoring',
    display_name: 'Datadog Monitoring',
    description: 'Send metrics, logs, and traces to Datadog for comprehensive observability.',
    category: 'Analytics',
    author: 'Datadog',
    author_verified: true,
    verified: true,
    downloads: 8923,
    rating: 4.7,
    review_count: 612,
    price: 0,
    pricing_model: 'free',
    version: '1.9.0',
    created_at: '2024-08-20T11:00:00Z',
    updated_at: '2025-01-15T09:20:00Z',
    tags: ['monitoring', 'observability', 'metrics', 'logs'],
    icon_url: '/marketplace/datadog.svg',
    documentation_url: 'https://docs.agentfoundry.com/tools/datadog',
    install_count: 8923,
    compatible_versions: ['0.8.x', '0.9.x'],
  },
  {
    id: 'mkt-105',
    type: 'tool',
    name: 'anthropic-claude',
    display_name: 'Anthropic Claude Models',
    description: 'Access to Claude 3 Opus, Sonnet, and Haiku models for advanced reasoning and long context.',
    category: 'AI Models',
    author: 'Anthropic',
    author_verified: true,
    verified: true,
    downloads: 12456,
    rating: 4.9,
    review_count: 892,
    price: 0,
    pricing_model: 'usage_based',
    version: '1.0.0',
    created_at: '2024-10-01T10:00:00Z',
    updated_at: '2025-01-14T16:30:00Z',
    tags: ['llm', 'ai', 'claude', 'anthropic'],
    icon_url: '/marketplace/anthropic.svg',
    documentation_url: 'https://docs.agentfoundry.com/tools/claude',
    install_count: 12456,
    compatible_versions: ['0.8.x', '0.9.x'],
  },

  // Domain Templates
  {
    id: 'mkt-201',
    type: 'domain',
    name: 'ecommerce-complete',
    display_name: 'E-Commerce Domain (Complete)',
    description: 'Comprehensive e-commerce domain model with orders, products, inventory, payments, and shipping.',
    category: 'E-Commerce',
    author: 'Agent Foundry Team',
    author_verified: true,
    verified: true,
    downloads: 2341,
    rating: 4.8,
    review_count: 187,
    price: 0,
    pricing_model: 'free',
    version: '2.3.0',
    created_at: '2024-09-15T10:00:00Z',
    updated_at: '2025-01-12T14:30:00Z',
    tags: ['ecommerce', 'retail', 'domain', 'dis'],
    icon_url: '/marketplace/ecommerce-domain.svg',
    documentation_url: 'https://docs.agentfoundry.com/domains/ecommerce',
    install_count: 2341,
    compatible_versions: ['0.8.x', '0.9.x'],
  },
  {
    id: 'mkt-202',
    type: 'domain',
    name: 'banking-core-domain',
    display_name: 'Banking Core Domain',
    description: 'Banking domain model with accounts, transactions, customers, and compliance frameworks.',
    category: 'Banking',
    author: 'FinTech Consortium',
    author_verified: true,
    verified: true,
    downloads: 1567,
    rating: 4.6,
    review_count: 123,
    price: 149.99,
    pricing_model: 'one_time',
    version: '1.8.0',
    created_at: '2024-08-10T09:00:00Z',
    updated_at: '2025-01-08T11:20:00Z',
    tags: ['banking', 'finance', 'compliance', 'domain'],
    icon_url: '/marketplace/banking-domain.svg',
    documentation_url: 'https://docs.agentfoundry.com/domains/banking',
    install_count: 1567,
    compatible_versions: ['0.8.x', '0.9.x'],
  },
  {
    id: 'mkt-203',
    type: 'domain',
    name: 'saas-subscription-domain',
    display_name: 'SaaS Subscription Domain',
    description: 'SaaS business domain with subscriptions, billing, organizations, and usage tracking.',
    category: 'SaaS',
    author: 'SaaS Builders',
    author_verified: false,
    verified: false,
    downloads: 892,
    rating: 4.3,
    review_count: 67,
    price: 0,
    pricing_model: 'free',
    version: '1.2.0',
    created_at: '2024-11-01T10:00:00Z',
    updated_at: '2025-01-05T15:10:00Z',
    tags: ['saas', 'subscription', 'billing', 'domain'],
    icon_url: '/marketplace/saas-domain.svg',
    documentation_url: 'https://docs.agentfoundry.com/domains/saas',
    install_count: 892,
    compatible_versions: ['0.8.x', '0.9.x'],
  },
];

// Helper functions
export function getMarketplaceItemById(id: string): MarketplaceItem | undefined {
  return mockMarketplaceItems.find(item => item.id === id);
}

export function getMarketplaceItemsByType(type: string): MarketplaceItem[] {
  return mockMarketplaceItems.filter(item => item.type === type);
}

export function getMarketplaceItemsByCategory(category: string): MarketplaceItem[] {
  return mockMarketplaceItems.filter(item => item.category === category);
}

export function getFeaturedItems(limit: number = 6): MarketplaceItem[] {
  return [...mockMarketplaceItems]
    .filter(item => item.verified)
    .sort((a, b) => b.downloads - a.downloads)
    .slice(0, limit);
}

export function getPopularItems(limit: number = 10): MarketplaceItem[] {
  return [...mockMarketplaceItems]
    .sort((a, b) => b.downloads - a.downloads)
    .slice(0, limit);
}

export function getRecentItems(limit: number = 10): MarketplaceItem[] {
  return [...mockMarketplaceItems]
    .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
    .slice(0, limit);
}

export function getTopRatedItems(limit: number = 10): MarketplaceItem[] {
  return [...mockMarketplaceItems]
    .sort((a, b) => {
      if (b.rating !== a.rating) return b.rating - a.rating;
      return b.review_count - a.review_count;
    })
    .slice(0, limit);
}

export function searchMarketplace(query: string): MarketplaceItem[] {
  const lowercaseQuery = query.toLowerCase();
  return mockMarketplaceItems.filter(
    item =>
      item.name.toLowerCase().includes(lowercaseQuery) ||
      item.display_name.toLowerCase().includes(lowercaseQuery) ||
      item.description.toLowerCase().includes(lowercaseQuery) ||
      item.tags.some(tag => tag.toLowerCase().includes(lowercaseQuery))
  );
}

export function getMarketplaceStats() {
  return {
    total_items: mockMarketplaceItems.length,
    total_agents: mockMarketplaceItems.filter(i => i.type === 'agent').length,
    total_tools: mockMarketplaceItems.filter(i => i.type === 'tool').length,
    total_domains: mockMarketplaceItems.filter(i => i.type === 'domain').length,
    total_downloads: mockMarketplaceItems.reduce((sum, i) => sum + i.downloads, 0),
    verified_items: mockMarketplaceItems.filter(i => i.verified).length,
    free_items: mockMarketplaceItems.filter(i => i.price === 0).length,
    paid_items: mockMarketplaceItems.filter(i => i.price > 0).length,
  };
}
