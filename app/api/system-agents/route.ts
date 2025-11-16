import { NextResponse } from 'next/server';
import fs from 'fs/promises';
import path from 'path';
import yaml from 'js-yaml';
import type { AgentManifest } from '@/types';

const AGENTS_DIR = path.join(process.cwd(), 'agents');
const MANIFEST_DIR = path.join(AGENTS_DIR, 'manifests');

function getEnvFromSearchParams(searchParams: URLSearchParams): 'dev' | 'staging' | 'prod' {
  const env = searchParams.get('env') as 'dev' | 'staging' | 'prod' | null;
  if (env === 'staging' || env === 'prod') return env;
  return 'dev';
}

async function loadEnvironmentManifest(env: 'dev' | 'staging' | 'prod'): Promise<AgentManifest | null> {
  const manifestPath = path.join(MANIFEST_DIR, `manifest.${env}.yaml`);
  try {
    const content = await fs.readFile(manifestPath, 'utf-8');
    const manifest = yaml.load(content) as AgentManifest;
    return manifest;
  } catch (error) {
    console.error(`Error loading manifest for env=${env} from ${manifestPath}:`, error);
    return null;
  }
}

// GET /api/system-agents - Get environment-scoped system agent configurations
export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const agentId = searchParams.get('id');
    const orgId = searchParams.get('orgId');
    const domainId = searchParams.get('domainId');
    const instanceId = searchParams.get('instanceId');
    const env = getEnvFromSearchParams(searchParams);

    const manifest = await loadEnvironmentManifest(env);
    if (!manifest) {
      return NextResponse.json(
        { error: `Environment manifest not found for env=${env}` },
        { status: 500 }
      );
    }

    const entries = manifest.spec.entries.filter((entry) => {
      if (agentId && entry.agent_id !== agentId) return false;
      if (orgId && entry.organization_id !== orgId) return false;
      if (domainId && entry.domain_id !== domainId) return false;
      if (instanceId && entry.instance_id !== instanceId) return false;
      return true;
    });

    if (agentId && entries.length === 0) {
      return NextResponse.json(
        { error: `Agent ${agentId} not found in env=${env}` },
        { status: 404 }
      );
    }

    const result: Record<string, any> = {};

    for (const entry of entries) {
      try {
        const filePath = path.join(AGENTS_DIR, entry.yaml_path);
        const fileContent = await fs.readFile(filePath, 'utf-8');
        const agentConfig = yaml.load(fileContent);

        // Attach binding metadata so the UI / backend knows org/domain/instance context
        result[entry.agent_id] = {
          ...agentConfig,
          __binding: entry,
        };
      } catch (error) {
        console.error(`Error loading agent ${entry.agent_id} from ${entry.yaml_path}:`, error);
      }
    }

    return NextResponse.json(result);
  } catch (error) {
    console.error('Error loading system agents:', error);
    return NextResponse.json(
      { error: 'Failed to load system agents' },
      { status: 500 }
    );
  }
}

// PUT /api/system-agents - Update system agent configuration
export async function PUT(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const agentId = searchParams.get('id');

    if (!agentId) {
      return NextResponse.json(
        { error: 'Agent ID is required' },
        { status: 400 }
      );
    }

    // For now, assume dev env for writes; in the future this should be scoped
    // via env/org/domain/instance or use a dedicated config service.
    const env: 'dev' | 'staging' | 'prod' = 'dev';
    const manifest = await loadEnvironmentManifest(env);
    if (!manifest) {
      return NextResponse.json(
        { error: `Environment manifest not found for env=${env}` },
        { status: 500 }
      );
    }

    const entry = manifest.spec.entries.find((e) => e.agent_id === agentId);
    if (!entry) {
      return NextResponse.json(
        { error: `Agent ${agentId} not found in env=${env}` },
        { status: 404 }
      );
    }

    const filename = entry.yaml_path;
    const agentConfig = await request.json();

    // Convert to YAML
    const yamlContent = yaml.dump(agentConfig, {
      indent: 2,
      lineWidth: 100,
      noRefs: true,
    });

    // Write to file
    const filePath = path.join(AGENTS_DIR, filename);
    await fs.writeFile(filePath, yamlContent, 'utf-8');

    return NextResponse.json({
      success: true,
      message: `Agent ${agentId} configuration updated successfully`,
    });
  } catch (error) {
    console.error('Error updating system agent:', error);
    return NextResponse.json(
      { error: 'Failed to update system agent configuration' },
      { status: 500 }
    );
  }
}

// POST /api/system-agents/health - Check health of system agents
export async function POST(request: Request) {
  try {
    const { agentId } = await request.json();

    // TODO: Implement actual health check by calling the agent's health endpoint
    // For now, return mock health status

    const healthStatus = {
      agent_id: agentId,
      status: 'healthy',
      timestamp: new Date().toISOString(),
      checks: {
        connectivity: true,
        resource_usage: {
          memory_mb: Math.floor(Math.random() * 512),
          cpu_percent: Math.floor(Math.random() * 100),
        },
        integrations: {
          redis: true,
          postgresql: true,
          livekit: true,
        },
      },
    };

    return NextResponse.json(healthStatus);
  } catch (error) {
    console.error('Error checking agent health:', error);
    return NextResponse.json(
      { error: 'Failed to check agent health' },
      { status: 500 }
    );
  }
}

