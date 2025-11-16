"use client"

import { Node, Edge } from "reactflow"
import { graphToYAML } from "./graph-to-yaml"

const MCP_BASE_URL = process.env.NEXT_PUBLIC_MCP_SERVER_URL || "http://localhost:8001"

export interface RegisterAgentPayload {
  agentId: string
  nodes: Node[]
  edges: Edge[]
  yamlPath?: string

  organizationId: string
  organizationName: string
  domainId: string
  domainName: string
  environment: "dev" | "staging" | "prod"
  instanceId: string

  author: string
  lastEditor?: string
  tags?: string[]
  isSystemAgent?: boolean
  systemTier?: 0 | 1
}

export async function registerAgentInManifest(payload: RegisterAgentPayload) {
  const {
    agentId,
    nodes,
    edges,
    yamlPath,
    organizationId,
    organizationName,
    domainId,
    domainName,
    environment,
    instanceId,
    author,
    lastEditor,
    tags,
    isSystemAgent,
    systemTier,
  } = payload

  const agentYaml = graphToYAML(nodes, edges, agentId)

  const body = {
    agent_id: agentId,
    agent_yaml: agentYaml,
    yaml_path: yamlPath,
    organization_id: organizationId,
    organization_name: organizationName,
    domain_id: domainId,
    domain_name: domainName,
    environment,
    instance_id: instanceId,
    author,
    last_editor: lastEditor ?? author,
    tags: tags ?? [],
    is_system_agent: isSystemAgent ?? false,
    system_tier: systemTier,
  }

  const response = await fetch(`${MCP_BASE_URL}/api/tools/manifest/register-agent`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  })

  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || err.error || `Manifest register failed (${response.status})`)
  }

  return response.json()
}


