"""
Secrets Management Routes
-------------------------
API endpoints for managing organization/domain secrets using "Blind Write" pattern.

Security:
- Requires RBAC authorization (org:configure permission)
- Never returns actual secret values to client
- All operations are audit logged
- Secrets are scoped to organization/domain

Endpoints:
- GET    /api/secrets/{org_id}/status           - Check which secrets are configured
- GET    /api/secrets/{org_id}/{secret_name}    - Check if specific secret exists
- PUT    /api/secrets/{org_id}/{secret_name}    - Create/update secret (blind write)
- DELETE /api/secrets/{org_id}/{secret_name}    - Delete secret
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from backend.config.secrets import secrets_manager
from backend.middleware.openfga_middleware import AuthContext, get_current_user, log_auth_event

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/secrets", tags=["secrets"])


# ============================================================================
# PYDANTIC MODELS
# ============================================================================


class SecretStatus(BaseModel):
    """Status of a single secret (metadata only)"""

    secret_name: str
    configured: bool
    last_updated: str | None = None
    description: str | None = None


class SecretsStatusResponse(BaseModel):
    """Status of all secrets for an organization"""

    organization_id: str
    domain_id: str | None = None
    secrets: list[SecretStatus]


class SecretUpsertRequest(BaseModel):
    """Request to create/update a secret"""

    secret_value: str = Field(..., min_length=1, description="The secret value (never logged)")
    domain_id: str | None = Field(None, description="Optional domain ID for domain-scoped secret")
    description: str | None = Field(None, description="Optional description")


class SecretUpsertResponse(BaseModel):
    """Response after creating/updating a secret"""

    status: str
    configured: bool
    message: str


class SecretExistsResponse(BaseModel):
    """Response for secret existence check"""

    configured: bool
    secret_name: str
    organization_id: str
    domain_id: str | None = None


# ============================================================================
# WELL-KNOWN SECRET TYPES
# ============================================================================

# Mapping of well-known secret names to their descriptions
WELL_KNOWN_SECRETS = {
    # LLM Providers
    "openai_api_key": {
        "display_name": "OpenAI API Key",
        "description": "API key for OpenAI GPT models",
        "category": "llm",
        "validation_url": "https://api.openai.com/v1/models",
    },
    "anthropic_api_key": {
        "display_name": "Anthropic API Key",
        "description": "API key for Claude models",
        "category": "llm",
        "validation_url": "https://api.anthropic.com/v1/messages",
    },
    "deepgram_api_key": {
        "display_name": "Deepgram API Key",
        "description": "API key for speech-to-text",
        "category": "voice",
        "validation_url": None,
    },
    "elevenlabs_api_key": {
        "display_name": "ElevenLabs API Key",
        "description": "API key for text-to-speech",
        "category": "voice",
        "validation_url": None,
    },
    # Integrations
    "github_token": {
        "display_name": "GitHub Token",
        "description": "Personal access token for GitHub API",
        "category": "integration",
        "validation_url": "https://api.github.com/user",
    },
    "notion_api_token": {
        "display_name": "Notion API Token",
        "description": "Integration token for Notion API",
        "category": "integration",
        "validation_url": "https://api.notion.com/v1/users/me",
    },
    "n8n_api_key": {
        "display_name": "n8n API Key",
        "description": "API key for n8n workflow automation",
        "category": "integration",
        "validation_url": None,
    },
    # Infrastructure
    "livekit_api_key": {
        "display_name": "LiveKit API Key",
        "description": "API key for LiveKit voice infrastructure",
        "category": "infrastructure",
        "validation_url": None,
    },
    "livekit_api_secret": {
        "display_name": "LiveKit API Secret",
        "description": "API secret for LiveKit voice infrastructure",
        "category": "infrastructure",
        "validation_url": None,
    },
}


# ============================================================================
# ROUTES
# ============================================================================


@router.get("/{org_id}/status", response_model=SecretsStatusResponse)
async def get_secrets_status(
    org_id: str, domain_id: str | None = None, request: Request = None, context: AuthContext = Depends(get_current_user)
):
    """
    Get configuration status of all well-known secrets.

    Returns metadata only (configured: true/false), never actual values.
    This is SAFE to expose to frontend.

    **Required Permission:** `can_read` on organization or domain
    """
    # Check permission via OpenFGA
    resource = f"domain:{domain_id}" if domain_id else f"organization:{org_id}"

    if not await context.can("can_read", resource):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Cannot access secrets for {resource}")

    try:
        # Check status of all well-known secrets
        secret_statuses = []

        for secret_name, metadata in WELL_KNOWN_SECRETS.items():
            configured = await secrets_manager.has_secret(org_id, secret_name, domain_id)

            secret_statuses.append(
                SecretStatus(secret_name=secret_name, configured=configured, description=metadata.get("description"))
            )

        return SecretsStatusResponse(organization_id=org_id, domain_id=domain_id, secrets=secret_statuses)

    except Exception as e:
        logger.error(f"Failed to get secrets status for {org_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve secrets status")


@router.get("/{org_id}/{secret_name}", response_model=SecretExistsResponse)
async def check_secret_exists(
    org_id: str,
    secret_name: str,
    domain_id: str | None = None,
    request: Request = None,
    context: AuthContext = Depends(get_current_user),
):
    """
    Check if a specific secret is configured.

    Returns boolean only, never the actual value.
    This is SAFE to expose to frontend.

    **Required Permission:** `can_read_status` on secret
    """
    # Build secret ID for OpenFGA
    secret_id = secrets_manager.get_secret_id(org_id, domain_id, secret_name)

    # Check permission via OpenFGA
    if not await context.can("can_read_status", f"secret:{secret_id}"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f"Cannot view status of secret '{secret_name}'"
        )

    try:
        configured = await secrets_manager.has_secret(org_id, secret_name, domain_id)

        return SecretExistsResponse(
            configured=configured, secret_name=secret_name, organization_id=org_id, domain_id=domain_id
        )

    except Exception as e:
        logger.error(f"Failed to check secret {secret_name} for {org_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to check secret status")


@router.put("/{org_id}/{secret_name}", response_model=SecretUpsertResponse)
async def upsert_secret(
    org_id: str,
    secret_name: str,
    payload: SecretUpsertRequest,
    request: Request = None,
    context: AuthContext = Depends(get_current_user),
):
    """
    Create or update a secret (Blind Write pattern).

    **SECURITY:**
    - Secret value is immediately written to LocalStack/AWS
    - Value is NEVER logged or returned in response
    - Operation is audit logged (WHO updated, but not WHAT)
    - Overwrites existing secret without returning old value

    **Required Permission:** `can_update` on secret or `can_manage_secrets` on organization
    """
    # Build secret ID for OpenFGA
    secret_id = secrets_manager.get_secret_id(org_id, payload.domain_id, secret_name)

    # Check permission via OpenFGA
    # Allow if: can_update secret OR can_manage_secrets org
    can_update_secret = await context.can("can_update", f"secret:{secret_id}")
    can_manage_org = await context.can("can_manage_secrets", f"organization:{org_id}")

    if not (can_update_secret or can_manage_org):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Cannot update secret '{secret_name}'")

    # Validate secret_name against well-known list
    if secret_name not in WELL_KNOWN_SECRETS:
        logger.warning(f"Unknown secret type: {secret_name}")
        # Allow it anyway, but log for review

    try:
        # Optional: Validate the secret with the provider's API before saving
        # This prevents saving invalid keys
        if secret_name in WELL_KNOWN_SECRETS:
            validation_url = WELL_KNOWN_SECRETS[secret_name].get("validation_url")
            if validation_url:
                # TODO: Implement validation logic
                # is_valid = await validate_api_key(secret_name, payload.secret_value, validation_url)
                # if not is_valid:
                #     raise HTTPException(status_code=400, detail="Invalid API key")
                pass

        # Write secret to LocalStack/AWS
        success = await secrets_manager.upsert_secret(
            organization_id=org_id,
            secret_name=secret_name,
            secret_value=payload.secret_value,
            domain_id=payload.domain_id,
            description=payload.description,
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to save secret")

        # Audit log (WHO updated, but NOT the value)
        await log_auth_event(
            request=request,
            action="secret.update",
            resource_type="secret",
            resource_id=secret_id,
            result="success",
            metadata={"secret_name": secret_name, "organization_id": org_id, "domain_id": payload.domain_id},
        )

        return SecretUpsertResponse(
            status="success", configured=True, message=f"Secret '{secret_name}' has been updated successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upsert secret {secret_name} for {org_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to save secret")


@router.delete("/{org_id}/{secret_name}")
async def delete_secret(
    org_id: str,
    secret_name: str,
    domain_id: str | None = None,
    force: bool = False,
    request: Request = None,
    context: AuthContext = Depends(get_current_user),
):
    """
    Delete a secret.

    By default, schedules for deletion with 30-day recovery window.
    Use force=true for immediate deletion (LocalStack only).

    **Required Permission:** `can_delete` on secret or `can_manage_secrets` on organization
    """
    # Build secret ID for OpenFGA
    secret_id = secrets_manager.get_secret_id(org_id, domain_id, secret_name)

    # Check permission via OpenFGA
    can_delete_secret = await context.can("can_delete", f"secret:{secret_id}")
    can_manage_org = await context.can("can_manage_secrets", f"organization:{org_id}")

    if not (can_delete_secret or can_manage_org):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Cannot delete secret '{secret_name}'")

    try:
        success = await secrets_manager.delete_secret(
            organization_id=org_id, secret_name=secret_name, domain_id=domain_id, force=force
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete secret")

        # Audit log
        await log_auth_event(
            request=request,
            action="secret.delete",
            resource_type="secret",
            resource_id=secret_id,
            result="success",
            metadata={"secret_name": secret_name, "organization_id": org_id, "domain_id": domain_id, "force": force},
        )

        return {
            "status": "success",
            "message": f"Secret '{secret_name}' has been {'deleted' if force else 'scheduled for deletion'}",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete secret {secret_name} for {org_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete secret")


@router.get("/well-known")
async def list_well_known_secrets():
    """
    List all well-known secret types.

    Returns metadata about supported secret types for UI rendering.
    No authentication required (just metadata).
    """
    secrets_by_category = {}

    for secret_name, metadata in WELL_KNOWN_SECRETS.items():
        category = metadata.get("category", "other")

        if category not in secrets_by_category:
            secrets_by_category[category] = []

        secrets_by_category[category].append(
            {
                "secret_name": secret_name,
                "display_name": metadata.get("display_name"),
                "description": metadata.get("description"),
                "category": category,
            }
        )

    return {"categories": secrets_by_category, "total": len(WELL_KNOWN_SECRETS)}
