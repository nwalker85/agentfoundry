// MongoDB Initialization Script for DIS Dossier Storage
// Agent Foundry - DIS 1.6.0 Compliant Dossier Management
// This script runs automatically on first MongoDB startup

print('🏭 Agent Foundry - Initializing Dossier Database');
print('================================================');

// Switch to dossiers database
db = db.getSiblingDB('dossiers');

// Create foundry user with readWrite access to dossiers database
db.createUser({
  user: 'foundry_dossier',
  pwd: 'foundry',
  roles: [
    {
      role: 'readWrite',
      db: 'dossiers',
    },
  ],
});

print('✅ Created dossier database user');

// ============================================
// Collection: dossiers
// ============================================
// Main collection for DIS 1.6.0 compliant dossiers

db.createCollection('dossiers', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['dossierId', 'version', 'organizationId', 'header', 'metadata'],
      properties: {
        dossierId: {
          bsonType: 'string',
          description: 'Unique dossier identifier - required',
        },
        version: {
          bsonType: 'string',
          pattern: '^[0-9]+\\.[0-9]+\\.[0-9]+$',
          description: 'Semantic version (e.g., "2.2.0") - required',
        },
        organizationId: {
          bsonType: 'string',
          description: 'Organization owner - required for multi-tenancy',
        },
        header: {
          bsonType: 'object',
          required: [
            'dossierId',
            'domainName',
            'version',
            'disSpecificationRef',
            'dossierType',
            'dossierStatus',
          ],
          properties: {
            dossierId: { bsonType: 'string' },
            domainName: { bsonType: 'string' },
            description: { bsonType: 'string' },
            version: { bsonType: 'string' },
            versionDate: { bsonType: 'date' },
            disSpecificationRef: {
              bsonType: 'string',
              description: 'DIS specification version (e.g., "1.6.0")',
            },
            dossierType: {
              bsonType: 'string',
              enum: ['DESIGN', 'OPERATIONAL', 'REFERENCE'],
              description: 'Type of dossier',
            },
            dossierStatus: {
              bsonType: 'string',
              enum: ['DRAFT', 'REVIEW', 'APPROVED', 'ARCHIVED'],
              description: 'Current status in lifecycle',
            },
            authors: { bsonType: 'array', items: { bsonType: 'string' } },
            geographicScope: { bsonType: 'array', items: { bsonType: 'string' } },
            industryVertical: { bsonType: 'string' },
            knowledgeDocumentIds: { bsonType: 'array', items: { bsonType: 'string' } },
            tags: { bsonType: 'array', items: { bsonType: 'string' } },
          },
        },
        metadata: {
          bsonType: 'object',
          required: ['createdAt', 'createdBy'],
          properties: {
            createdAt: { bsonType: 'date' },
            createdBy: { bsonType: 'string' },
            updatedAt: { bsonType: 'date' },
            updatedBy: { bsonType: 'string' },
            locked: { bsonType: 'bool' },
            lockedBy: { bsonType: 'string' },
            lockedAt: { bsonType: 'date' },
          },
        },
      },
    },
  },
});

print("✅ Created 'dossiers' collection with schema validation");

// Create indexes for dossiers collection
db.dossiers.createIndex({ dossierId: 1 }, { unique: true });
db.dossiers.createIndex({ organizationId: 1, dossierId: 1 });
db.dossiers.createIndex({ organizationId: 1, 'header.dossierStatus': 1 });
db.dossiers.createIndex({ 'header.tags': 1 });
db.dossiers.createIndex({ 'header.industryVertical': 1 });
db.dossiers.createIndex({ 'header.dossierType': 1 });
db.dossiers.createIndex({ searchableText: 'text' });
db.dossiers.createIndex({ 'metadata.createdAt': -1 });
db.dossiers.createIndex({ 'metadata.updatedAt': -1 });
db.dossiers.createIndex({ version: 1 });

print("✅ Created indexes on 'dossiers' collection");

// ============================================
// Collection: dossier_versions
// ============================================
// Immutable version history for dossiers

db.createCollection('dossier_versions', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['dossierId', 'version', 'snapshotDate', 'dossierSnapshot'],
      properties: {
        dossierId: {
          bsonType: 'string',
          description: 'Reference to parent dossier',
        },
        version: {
          bsonType: 'string',
          pattern: '^[0-9]+\\.[0-9]+\\.[0-9]+$',
          description: 'Semantic version',
        },
        snapshotDate: {
          bsonType: 'date',
          description: 'When version was created',
        },
        dossierSnapshot: {
          bsonType: 'object',
          description: 'Complete dossier at this version',
        },
        changeManagement: {
          bsonType: 'object',
          properties: {
            changeType: {
              bsonType: 'string',
              enum: ['MAJOR', 'MINOR', 'PATCH'],
            },
            changeDescription: { bsonType: 'string' },
            changedBy: { bsonType: 'string' },
            approvedBy: { bsonType: 'string' },
            approvalDate: { bsonType: 'date' },
          },
        },
        tags: {
          bsonType: 'array',
          items: { bsonType: 'string' },
        },
      },
    },
  },
});

print("✅ Created 'dossier_versions' collection");

// Create indexes for versions
db.dossier_versions.createIndex({ dossierId: 1, version: 1 }, { unique: true });
db.dossier_versions.createIndex({ dossierId: 1, snapshotDate: -1 });
db.dossier_versions.createIndex({ snapshotDate: -1 });

print("✅ Created indexes on 'dossier_versions' collection");

// ============================================
// Collection: dossier_operations
// ============================================
// Audit log for all dossier operations (agent and user)

db.createCollection('dossier_operations', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['operationId', 'dossierId', 'operationType', 'timestamp', 'status'],
      properties: {
        operationId: {
          bsonType: 'string',
          description: 'Unique operation identifier',
        },
        dossierId: {
          bsonType: 'string',
          description: 'Dossier being operated on',
        },
        agentId: {
          bsonType: 'string',
          description: 'Agent performing operation (if applicable)',
        },
        operationType: {
          bsonType: 'string',
          enum: [
            'READ',
            'CREATE',
            'UPDATE',
            'DELETE',
            'VALIDATE',
            'TRANSFORM',
            'QUERY',
            'EXPORT',
            'IMPORT',
          ],
          description: 'Type of operation',
        },
        timestamp: {
          bsonType: 'date',
          description: 'When operation occurred',
        },
        userId: {
          bsonType: 'string',
          description: 'User who initiated operation',
        },
        status: {
          bsonType: 'string',
          enum: ['SUCCESS', 'FAILURE', 'PARTIAL'],
          description: 'Operation result',
        },
        duration: {
          bsonType: 'number',
          description: 'Operation duration in milliseconds',
        },
        errors: {
          bsonType: 'array',
          description: 'Error details if status is FAILURE or PARTIAL',
        },
      },
    },
  },
});

print("✅ Created 'dossier_operations' collection");

// Create indexes for operations (audit log)
db.dossier_operations.createIndex({ dossierId: 1, timestamp: -1 });
db.dossier_operations.createIndex({ agentId: 1, timestamp: -1 });
db.dossier_operations.createIndex({ userId: 1, timestamp: -1 });
db.dossier_operations.createIndex({ operationType: 1 });
db.dossier_operations.createIndex({ timestamp: -1 });
db.dossier_operations.createIndex({ status: 1, timestamp: -1 });

print("✅ Created indexes on 'dossier_operations' collection");

// ============================================
// Collection: dossier_locks
// ============================================
// Concurrent editing lock management

db.createCollection('dossier_locks', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['dossierId', 'lockedBy', 'lockedAt'],
      properties: {
        dossierId: {
          bsonType: 'string',
          description: 'Dossier being locked',
        },
        lockedBy: {
          bsonType: 'string',
          description: 'User ID who holds the lock',
        },
        lockedAt: {
          bsonType: 'date',
          description: 'When lock was acquired',
        },
        expiresAt: {
          bsonType: 'date',
          description: 'When lock expires (auto-release)',
        },
        sessionId: {
          bsonType: 'string',
          description: 'Session ID for lock validation',
        },
      },
    },
  },
});

print("✅ Created 'dossier_locks' collection");

// Create indexes for locks
db.dossier_locks.createIndex({ dossierId: 1 }, { unique: true });
db.dossier_locks.createIndex({ expiresAt: 1 }, { expireAfterSeconds: 0 }); // TTL index for auto-cleanup
db.dossier_locks.createIndex({ lockedBy: 1 });

print("✅ Created indexes on 'dossier_locks' collection");

// ============================================
// Insert Sample Dossier (for testing)
// ============================================

const sampleDossier = {
  dossierId: 'sample-banking-domain-v1',
  version: '1.0.0',
  organizationId: 'default-org',

  header: {
    dossierId: 'sample-banking-domain-v1',
    domainName: 'Sample Consumer Banking Domain',
    description: 'Sample DIS 1.6.0 compliant dossier for consumer banking operations',
    version: '1.0.0',
    versionDate: new Date(),
    disSpecificationRef: '1.6.0',
    dossierType: 'DESIGN',
    dossierStatus: 'DRAFT',
    authors: ['Agent Foundry System'],
    geographicScope: ['Global'],
    industryVertical: 'FINANCIAL_SERVICES',
    knowledgeDocumentIds: [],
    tags: ['sample', 'banking', 'consumer', 'cards'],
  },

  dossierSpecificDefinitions: {
    commonEnums: [
      {
        enumId: 'account-status',
        enumName: 'AccountStatus',
        enumValues: ['ACTIVE', 'SUSPENDED', 'CLOSED', 'PENDING'],
        description: 'Possible account status values',
      },
    ],
    entities: [
      {
        entityId: 'client-account',
        entityName: 'ClientAccount',
        entityType: 'DATA',
        description: 'Customer banking account entity',
        keys: [
          {
            keyName: 'accountId',
            keyType: 'PRIMARY',
            dataType: 'uuid',
          },
        ],
        attributes: [
          {
            attributeName: 'accountNumber',
            dataType: 'string',
            required: true,
            sensitive: true,
          },
          {
            attributeName: 'accountType',
            dataType: 'enum:AccountStatus',
            required: true,
            sensitive: false,
          },
          {
            attributeName: 'balance',
            dataType: 'decimal',
            required: true,
            sensitive: false,
          },
        ],
        relationships: [],
        tags: ['core', 'account'],
      },
    ],
    capabilities: [
      {
        capabilityId: 'account-management',
        capabilityName: 'Account Management',
        description: 'Capability to manage customer accounts',
        category: 'CORE',
        prerequisites: [],
        tags: ['account'],
      },
    ],
  },

  tripletFunctionMatrix: [
    {
      tripletId: 'view-account-balance',
      subject: 'Customer',
      verb: 'view',
      object: 'ClientAccount',
      modeOfInteraction: 'READ',
      functionBinding: {
        functionId: 'get-account-balance',
        functionName: 'getAccountBalance',
        implementation: 'api',
        parameters: [
          {
            name: 'accountId',
            type: 'uuid',
            required: true,
          },
        ],
      },
      governanceRules: [],
      accessGates: [],
    },
  ],

  workflows: [],
  accessGateMatrix: [],
  validationRules: [],

  privacyManifest: {
    sensitiveEntities: ['ClientAccount'],
    retentionPolicies: [],
    encryptionRequirements: [],
    gdprCompliance: {},
  },

  metadata: {
    createdAt: new Date(),
    createdBy: 'system',
    updatedAt: new Date(),
    updatedBy: 'system',
    locked: false,
  },

  encryption: {
    encrypted: false,
    encryptedFields: [],
    keyId: '',
  },

  searchableText: 'Sample Consumer Banking Domain banking consumer cards account',
  versionHistory: [
    {
      version: '1.0.0',
      versionDate: new Date(),
      changes: 'Initial version',
      changedBy: 'system',
    },
  ],
};

db.dossiers.insertOne(sampleDossier);

print('✅ Inserted sample dossier');

// ============================================
// Database Statistics
// ============================================

print('\n📊 Database Statistics:');
print('======================');
print('Database: ' + db.getName());
print('Collections created: ' + db.getCollectionNames().length);
print('  - dossiers');
print('  - dossier_versions');
print('  - dossier_operations');
print('  - dossier_locks');
print('\n✅ MongoDB Dossier Database Initialized Successfully!');
print('🔐 Authentication enabled - use foundry_dossier user for application access');
print('📋 Sample dossier created: sample-banking-domain-v1');
print('\nConnection string for application:');
print('  mongodb://foundry_dossier:foundry@mongodb:27017/dossiers?authSource=dossiers');
