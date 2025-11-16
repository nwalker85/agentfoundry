/**
 * Agent Foundry - Mock Domain Data
 * Sample domain models using DIS (Domain Intelligence Schema)
 */

import {
  Domain,
  Entity,
  Role,
  Relationship,
  Application,
  Endpoint,
  DomainTemplate,
} from '@/types';

export const mockDomains: Domain[] = [
  {
    id: 'dom-001',
    name: 'ecommerce-domain',
    display_name: 'E-Commerce Domain Model',
    description: 'Complete domain model for e-commerce operations including orders, customers, and inventory',
    version: '2.3.0',
    dossier_json: {
      domain: 'ecommerce',
      version: '2.3.0',
      entities: ['Customer', 'Order', 'Product', 'Payment', 'Shipment'],
      roles: ['CustomerServiceAgent', 'SalesAgent', 'InventoryManager'],
    },
    dossier_valid: true,
    entities: [
      {
        id: 'ent-001',
        domain_id: 'dom-001',
        name: 'Customer',
        display_name: 'Customer',
        description: 'Customer entity with contact and preference information',
        type: 'person',
        attributes: [
          { name: 'customer_id', type: 'string', required: true },
          { name: 'email', type: 'string', required: true },
          { name: 'name', type: 'string', required: true },
          { name: 'phone', type: 'string', required: false },
          { name: 'loyalty_tier', type: 'string', required: false },
          { name: 'created_at', type: 'date', required: true },
        ],
        position: { x: 100, y: 100 },
      },
      {
        id: 'ent-002',
        domain_id: 'dom-001',
        name: 'Order',
        display_name: 'Order',
        description: 'Customer order with items and status tracking',
        type: 'concept',
        attributes: [
          { name: 'order_id', type: 'string', required: true },
          { name: 'customer_id', type: 'string', required: true },
          { name: 'status', type: 'string', required: true, description: 'pending, processing, shipped, delivered, cancelled' },
          { name: 'total_amount', type: 'number', required: true },
          { name: 'items', type: 'array', required: true },
          { name: 'created_at', type: 'date', required: true },
          { name: 'shipped_at', type: 'date', required: false },
        ],
        position: { x: 400, y: 100 },
      },
      {
        id: 'ent-003',
        domain_id: 'dom-001',
        name: 'Product',
        display_name: 'Product',
        description: 'Product catalog item',
        type: 'concept',
        attributes: [
          { name: 'product_id', type: 'string', required: true },
          { name: 'name', type: 'string', required: true },
          { name: 'description', type: 'string', required: false },
          { name: 'price', type: 'number', required: true },
          { name: 'inventory_count', type: 'number', required: true },
          { name: 'category', type: 'string', required: false },
        ],
        position: { x: 700, y: 100 },
      },
      {
        id: 'ent-004',
        domain_id: 'dom-001',
        name: 'Payment',
        display_name: 'Payment',
        description: 'Payment transaction record',
        type: 'concept',
        attributes: [
          { name: 'payment_id', type: 'string', required: true },
          { name: 'order_id', type: 'string', required: true },
          { name: 'amount', type: 'number', required: true },
          { name: 'method', type: 'string', required: true },
          { name: 'status', type: 'string', required: true },
          { name: 'processed_at', type: 'date', required: false },
        ],
        position: { x: 400, y: 350 },
      },
    ],
    roles: [
      {
        id: 'role-001',
        domain_id: 'dom-001',
        name: 'CustomerServiceAgent',
        display_name: 'Customer Service Agent',
        description: 'Agent role for handling customer inquiries and order management',
        permissions: [
          { entity_id: 'ent-001', actions: ['read'] },
          { entity_id: 'ent-002', actions: ['read', 'update'] },
          { entity_id: 'ent-003', actions: ['read'] },
          { entity_id: 'ent-004', actions: ['read'] },
        ],
        function_bindings: [
          {
            function_name: 'get_order_status',
            tool_id: 'tool-custom-001',
            parameters_mapping: {
              order_id: '$.order_id',
            },
          },
          {
            function_name: 'cancel_order',
            tool_id: 'tool-custom-002',
            parameters_mapping: {
              order_id: '$.order_id',
              reason: '$.cancellation_reason',
            },
            access_gate: {
              id: 'gate-001',
              name: 'order_cancellation_gate',
              condition: 'order.status in ["pending", "processing"]',
              required_roles: ['CustomerServiceAgent'],
              required_permissions: ['order.update'],
            },
          },
        ],
      },
      {
        id: 'role-002',
        domain_id: 'dom-001',
        name: 'InventoryManager',
        display_name: 'Inventory Manager',
        description: 'Agent role for managing product inventory',
        permissions: [
          { entity_id: 'ent-003', actions: ['read', 'update'] },
        ],
        function_bindings: [
          {
            function_name: 'update_inventory',
            tool_id: 'tool-custom-003',
            parameters_mapping: {
              product_id: '$.product_id',
              quantity: '$.quantity',
            },
          },
        ],
      },
    ],
    applications: [
      {
        id: 'app-001',
        domain_id: 'dom-001',
        name: 'order-management-api',
        description: 'RESTful API for order management operations',
        endpoints: ['ep-001', 'ep-002', 'ep-003'],
      },
    ],
    endpoints: [
      {
        id: 'ep-001',
        application_id: 'app-001',
        domain_id: 'dom-001',
        name: 'get_order',
        path: '/api/orders/{order_id}',
        method: 'GET',
        description: 'Retrieve order details by order ID',
        request_schema: {
          type: 'object',
          properties: {
            order_id: { type: 'string' },
          },
        },
        response_schema: {
          type: 'object',
          properties: {
            order_id: { type: 'string' },
            customer_id: { type: 'string' },
            status: { type: 'string' },
            total_amount: { type: 'number' },
          },
        },
        function_binding_id: 'func-001',
      },
      {
        id: 'ep-002',
        application_id: 'app-001',
        domain_id: 'dom-001',
        name: 'cancel_order',
        path: '/api/orders/{order_id}/cancel',
        method: 'POST',
        description: 'Cancel an order',
        request_schema: {
          type: 'object',
          properties: {
            order_id: { type: 'string' },
            reason: { type: 'string' },
          },
        },
        response_schema: {
          type: 'object',
          properties: {
            success: { type: 'boolean' },
            message: { type: 'string' },
          },
        },
        function_binding_id: 'func-002',
      },
      {
        id: 'ep-003',
        application_id: 'app-001',
        domain_id: 'dom-001',
        name: 'create_order',
        path: '/api/orders',
        method: 'POST',
        description: 'Create a new order',
        request_schema: {
          type: 'object',
          properties: {
            customer_id: { type: 'string' },
            items: { type: 'array' },
          },
        },
        response_schema: {
          type: 'object',
          properties: {
            order_id: { type: 'string' },
            status: { type: 'string' },
          },
        },
      },
    ],
    relationships: [
      {
        id: 'rel-001',
        domain_id: 'dom-001',
        from_entity_id: 'ent-001',
        to_entity_id: 'ent-002',
        type: 'has_many',
        name: 'customer_orders',
        description: 'Customer can have multiple orders',
        cardinality: '1:N',
      },
      {
        id: 'rel-002',
        domain_id: 'dom-001',
        from_entity_id: 'ent-002',
        to_entity_id: 'ent-004',
        type: 'has_one',
        name: 'order_payment',
        description: 'Order has one payment',
        cardinality: '1:1',
      },
      {
        id: 'rel-003',
        domain_id: 'dom-001',
        from_entity_id: 'ent-002',
        to_entity_id: 'ent-003',
        type: 'many_to_many',
        name: 'order_products',
        description: 'Orders contain multiple products',
        cardinality: 'N:N',
      },
    ],
    created_at: '2024-10-15T09:00:00Z',
    updated_at: '2025-01-12T14:30:00Z',
    created_by: 'nwalker85',
    tags: ['ecommerce', 'retail', 'production'],
    used_by_agents: ['agt-001'],
  },
  {
    id: 'dom-002',
    name: 'banking-domain',
    display_name: 'Banking & Financial Services',
    description: 'Domain model for banking operations including accounts, transactions, and customers',
    version: '1.8.0',
    dossier_json: {
      domain: 'banking',
      version: '1.8.0',
      entities: ['Account', 'Transaction', 'Customer', 'Card'],
      roles: ['Teller', 'LoanOfficer', 'CustomerSupport'],
    },
    dossier_valid: true,
    entities: [
      {
        id: 'ent-101',
        domain_id: 'dom-002',
        name: 'Account',
        display_name: 'Bank Account',
        description: 'Customer bank account',
        type: 'concept',
        attributes: [
          { name: 'account_number', type: 'string', required: true },
          { name: 'customer_id', type: 'string', required: true },
          { name: 'account_type', type: 'string', required: true, description: 'checking, savings, credit' },
          { name: 'balance', type: 'number', required: true },
          { name: 'currency', type: 'string', required: true },
          { name: 'status', type: 'string', required: true },
        ],
        position: { x: 200, y: 100 },
      },
      {
        id: 'ent-102',
        domain_id: 'dom-002',
        name: 'Transaction',
        display_name: 'Transaction',
        description: 'Financial transaction record',
        type: 'concept',
        attributes: [
          { name: 'transaction_id', type: 'string', required: true },
          { name: 'account_number', type: 'string', required: true },
          { name: 'type', type: 'string', required: true, description: 'debit, credit, transfer' },
          { name: 'amount', type: 'number', required: true },
          { name: 'timestamp', type: 'date', required: true },
          { name: 'description', type: 'string', required: false },
        ],
        position: { x: 500, y: 100 },
      },
      {
        id: 'ent-103',
        domain_id: 'dom-002',
        name: 'Customer',
        display_name: 'Bank Customer',
        description: 'Banking customer profile',
        type: 'person',
        attributes: [
          { name: 'customer_id', type: 'string', required: true },
          { name: 'name', type: 'string', required: true },
          { name: 'email', type: 'string', required: true },
          { name: 'phone', type: 'string', required: false },
          { name: 'kyc_status', type: 'string', required: true },
        ],
        position: { x: 200, y: 350 },
      },
    ],
    roles: [
      {
        id: 'role-101',
        domain_id: 'dom-002',
        name: 'CustomerSupport',
        display_name: 'Customer Support Agent',
        description: 'Banking customer support role',
        permissions: [
          { entity_id: 'ent-101', actions: ['read'] },
          { entity_id: 'ent-102', actions: ['read'] },
          { entity_id: 'ent-103', actions: ['read'] },
        ],
        function_bindings: [
          {
            function_name: 'get_account_balance',
            tool_id: 'tool-banking-001',
            parameters_mapping: {
              account_number: '$.account_number',
            },
          },
          {
            function_name: 'get_transaction_history',
            tool_id: 'tool-banking-002',
            parameters_mapping: {
              account_number: '$.account_number',
              start_date: '$.start_date',
              end_date: '$.end_date',
            },
          },
        ],
      },
    ],
    applications: [
      {
        id: 'app-101',
        domain_id: 'dom-002',
        name: 'banking-api',
        description: 'Core banking API',
        endpoints: ['ep-101', 'ep-102'],
      },
    ],
    endpoints: [
      {
        id: 'ep-101',
        application_id: 'app-101',
        domain_id: 'dom-002',
        name: 'get_balance',
        path: '/api/accounts/{account_number}/balance',
        method: 'GET',
        description: 'Get account balance',
        request_schema: {
          type: 'object',
          properties: {
            account_number: { type: 'string' },
          },
        },
        response_schema: {
          type: 'object',
          properties: {
            balance: { type: 'number' },
            currency: { type: 'string' },
          },
        },
      },
      {
        id: 'ep-102',
        application_id: 'app-101',
        domain_id: 'dom-002',
        name: 'get_transactions',
        path: '/api/accounts/{account_number}/transactions',
        method: 'GET',
        description: 'Get transaction history',
        request_schema: {
          type: 'object',
          properties: {
            account_number: { type: 'string' },
            start_date: { type: 'string' },
            end_date: { type: 'string' },
          },
        },
        response_schema: {
          type: 'object',
          properties: {
            transactions: { type: 'array' },
          },
        },
      },
    ],
    relationships: [
      {
        id: 'rel-101',
        domain_id: 'dom-002',
        from_entity_id: 'ent-103',
        to_entity_id: 'ent-101',
        type: 'has_many',
        name: 'customer_accounts',
        description: 'Customer can have multiple accounts',
        cardinality: '1:N',
      },
      {
        id: 'rel-102',
        domain_id: 'dom-002',
        from_entity_id: 'ent-101',
        to_entity_id: 'ent-102',
        type: 'has_many',
        name: 'account_transactions',
        description: 'Account has many transactions',
        cardinality: '1:N',
      },
    ],
    created_at: '2024-09-20T10:00:00Z',
    updated_at: '2025-01-08T11:20:00Z',
    created_by: 'financial.team',
    tags: ['banking', 'finance', 'compliance'],
    used_by_agents: [],
  },
  {
    id: 'dom-003',
    name: 'healthcare-domain',
    display_name: 'Healthcare & Patient Management',
    description: 'Domain model for healthcare operations with HIPAA compliance',
    version: '1.2.0',
    dossier_json: {
      domain: 'healthcare',
      version: '1.2.0',
      entities: ['Patient', 'Appointment', 'MedicalRecord', 'Provider'],
      roles: ['Nurse', 'Doctor', 'Administrator'],
    },
    dossier_valid: false,
    validation_errors: [
      'Missing required access gate for MedicalRecord.read',
      'Provider entity missing required attribute: license_number',
    ],
    entities: [
      {
        id: 'ent-201',
        domain_id: 'dom-003',
        name: 'Patient',
        display_name: 'Patient',
        description: 'Patient demographic and contact information',
        type: 'person',
        attributes: [
          { name: 'patient_id', type: 'string', required: true },
          { name: 'name', type: 'string', required: true },
          { name: 'date_of_birth', type: 'date', required: true },
          { name: 'medical_record_number', type: 'string', required: true },
        ],
        position: { x: 150, y: 100 },
      },
      {
        id: 'ent-202',
        domain_id: 'dom-003',
        name: 'Appointment',
        display_name: 'Appointment',
        description: 'Patient appointment scheduling',
        type: 'concept',
        attributes: [
          { name: 'appointment_id', type: 'string', required: true },
          { name: 'patient_id', type: 'string', required: true },
          { name: 'provider_id', type: 'string', required: true },
          { name: 'scheduled_time', type: 'date', required: true },
          { name: 'status', type: 'string', required: true },
        ],
        position: { x: 450, y: 100 },
      },
    ],
    roles: [
      {
        id: 'role-201',
        domain_id: 'dom-003',
        name: 'Administrator',
        display_name: 'Healthcare Administrator',
        description: 'Administrative role for scheduling and patient coordination',
        permissions: [
          { entity_id: 'ent-201', actions: ['read', 'update'] },
          { entity_id: 'ent-202', actions: ['read', 'create', 'update'] },
        ],
        function_bindings: [],
      },
    ],
    applications: [],
    endpoints: [],
    relationships: [
      {
        id: 'rel-201',
        domain_id: 'dom-003',
        from_entity_id: 'ent-201',
        to_entity_id: 'ent-202',
        type: 'has_many',
        name: 'patient_appointments',
        description: 'Patient can have multiple appointments',
        cardinality: '1:N',
      },
    ],
    created_at: '2025-01-05T14:00:00Z',
    updated_at: '2025-01-10T16:20:00Z',
    created_by: 'health.admin',
    tags: ['healthcare', 'hipaa', 'draft'],
    used_by_agents: [],
  },
];

export const mockDomainTemplates: DomainTemplate[] = [
  {
    id: 'tpl-dom-001',
    name: 'ecommerce-starter',
    description: 'Complete e-commerce domain template with orders, products, and customers',
    category: 'ecommerce',
    dossier_json: {
      domain: 'ecommerce',
      entities: ['Customer', 'Order', 'Product', 'Payment'],
      roles: ['CustomerService', 'InventoryManager'],
    },
    verified: true,
    author: 'Agent Foundry Team',
    downloads: 234,
  },
  {
    id: 'tpl-dom-002',
    name: 'banking-core',
    description: 'Banking domain model with accounts, transactions, and compliance',
    category: 'banking',
    dossier_json: {
      domain: 'banking',
      entities: ['Account', 'Transaction', 'Customer'],
      roles: ['Teller', 'CustomerSupport'],
    },
    verified: true,
    author: 'Agent Foundry Team',
    downloads: 156,
  },
  {
    id: 'tpl-dom-003',
    name: 'saas-subscription',
    description: 'SaaS subscription and billing domain model',
    category: 'saas',
    dossier_json: {
      domain: 'saas',
      entities: ['Subscription', 'User', 'Organization', 'Invoice'],
      roles: ['CustomerSuccess', 'BillingAdmin'],
    },
    verified: true,
    author: 'Community Contributor',
    downloads: 89,
  },
];

// Helper functions
export function getDomainById(id: string): Domain | undefined {
  return mockDomains.find(domain => domain.id === id);
}

export function getValidDomains(): Domain[] {
  return mockDomains.filter(domain => domain.dossier_valid);
}

export function getDomainsByAgent(agentId: string): Domain[] {
  return mockDomains.filter(domain => domain.used_by_agents.includes(agentId));
}

export function getEntitiesByDomain(domainId: string): Entity[] {
  const domain = getDomainById(domainId);
  return domain?.entities || [];
}

export function getRolesByDomain(domainId: string): Role[] {
  const domain = getDomainById(domainId);
  return domain?.roles || [];
}

export function searchDomains(query: string): Domain[] {
  const lowercaseQuery = query.toLowerCase();
  return mockDomains.filter(
    domain =>
      domain.name.toLowerCase().includes(lowercaseQuery) ||
      domain.display_name.toLowerCase().includes(lowercaseQuery) ||
      domain.description.toLowerCase().includes(lowercaseQuery) ||
      domain.tags.some(tag => tag.toLowerCase().includes(lowercaseQuery))
  );
}
