"""
LocalStack Secrets Manager Configuration
-----------------------------------------
Infrastructure-as-Registry pattern for secret management.

Development: Uses LocalStack (localhost:4566)
Production: Uses AWS Secrets Manager

Philosophy:
- "Blind Write" pattern - UI never sees actual secrets
- Org-scoped secrets with deterministic naming
- Zero-trust: Secrets are never returned to frontend
- Audit logging for all secret operations
"""

import logging
import os

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class SecretsConfig:
    """
    Centralized secrets manager configuration.

    Automatically detects environment and routes to LocalStack or AWS.
    """

    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.region = os.getenv("AWS_REGION", "us-east-1")

        # Initialize AWS Secrets Manager client
        self.client = self._create_client()

        logger.info(f"Secrets Manager initialized for environment: {self.environment}")

    def _create_client(self):
        """Create boto3 Secrets Manager client (LocalStack or AWS)"""

        if self.environment in ("development", "dev", "local"):
            # Development: Use LocalStack via service discovery
            from backend.config.services import SERVICES

            endpoint_url = SERVICES.get_service_url("LOCALSTACK")

            client = boto3.client(
                "secretsmanager",
                endpoint_url=endpoint_url,
                region_name=self.region,
                aws_access_key_id="test",  # LocalStack accepts any credentials
                aws_secret_access_key="test",
                aws_session_token=None,
                verify=False,  # Skip SSL verification for LocalStack
            )

            logger.info(f"Using LocalStack Secrets Manager at {endpoint_url}")
            return client
        else:
            # Production: Use AWS Secrets Manager
            # Credentials from IAM role or environment variables
            client = boto3.client("secretsmanager", region_name=self.region)

            logger.info(f"Using AWS Secrets Manager in region {self.region}")
            return client

    def get_secret_id(self, organization_id: str, domain_id: str | None, secret_name: str) -> str:
        """
        Generate deterministic secret ID for organization-scoped secrets.

        Format: agentfoundry/[env]/[org_id]/[domain_id]/[secret_name]

        Examples:
            - agentfoundry/dev/acme-corp/card-services/openai_api_key
            - agentfoundry/prod/acme-corp/shared/anthropic_api_key

        Args:
            organization_id: Organization ID (e.g., "acme-corp")
            domain_id: Domain ID (e.g., "card-services") or None for org-level
            secret_name: Secret key name (e.g., "openai_api_key")

        Returns:
            Full secret ID for AWS Secrets Manager
        """
        parts = ["agentfoundry", self.environment, organization_id]

        if domain_id:
            parts.append(domain_id)
        else:
            parts.append("shared")  # Org-level secrets

        parts.append(secret_name)

        return "/".join(parts)

    async def upsert_secret(
        self,
        organization_id: str,
        secret_name: str,
        secret_value: str,
        domain_id: str | None = None,
        description: str | None = None,
    ) -> bool:
        """
        Create or update a secret (Blind Write pattern).

        This is the ONLY method that accepts secret values.
        Never log or expose the secret_value.

        Args:
            organization_id: Organization ID
            secret_name: Secret key name (e.g., "openai_api_key")
            secret_value: The actual secret value (NEVER LOGGED)
            domain_id: Optional domain ID for domain-scoped secrets
            description: Optional description

        Returns:
            True if successful
        """
        secret_id = self.get_secret_id(organization_id, domain_id, secret_name)

        try:
            # Try to update existing secret (most common case)
            self.client.put_secret_value(SecretId=secret_id, SecretString=secret_value)

            logger.info(
                f"Secret updated: {secret_id}",
                extra={
                    "organization_id": organization_id,
                    "domain_id": domain_id,
                    "secret_name": secret_name,
                    "action": "UPDATE_SECRET",
                },
            )

            return True

        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                # Secret doesn't exist, create it
                try:
                    self.client.create_secret(
                        Name=secret_id,
                        Description=description or f"Secret for {organization_id}",
                        SecretString=secret_value,
                    )

                    logger.info(
                        f"Secret created: {secret_id}",
                        extra={
                            "organization_id": organization_id,
                            "domain_id": domain_id,
                            "secret_name": secret_name,
                            "action": "CREATE_SECRET",
                        },
                    )

                    return True

                except ClientError as create_error:
                    logger.error(
                        f"Failed to create secret {secret_id}: {create_error}",
                        extra={
                            "organization_id": organization_id,
                            "domain_id": domain_id,
                            "secret_name": secret_name,
                            "action": "CREATE_SECRET_FAILED",
                        },
                    )
                    return False
            else:
                logger.error(
                    f"Failed to update secret {secret_id}: {e}",
                    extra={
                        "organization_id": organization_id,
                        "domain_id": domain_id,
                        "secret_name": secret_name,
                        "action": "UPDATE_SECRET_FAILED",
                    },
                )
                return False

    async def has_secret(self, organization_id: str, secret_name: str, domain_id: str | None = None) -> bool:
        """
        Check if a secret exists (WITHOUT retrieving the value).

        This is safe to expose to the frontend - only returns boolean.

        Args:
            organization_id: Organization ID
            secret_name: Secret key name
            domain_id: Optional domain ID

        Returns:
            True if secret exists, False otherwise
        """
        secret_id = self.get_secret_id(organization_id, domain_id, secret_name)

        try:
            # Describe only gets metadata, NOT the secret value
            self.client.describe_secret(SecretId=secret_id)
            return True

        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                return False
            else:
                logger.error(f"Error checking secret {secret_id}: {e}")
                return False

    async def get_secret(self, organization_id: str, secret_name: str, domain_id: str | None = None) -> str | None:
        """
        Retrieve secret value (BACKEND USE ONLY).

        ⚠️ SECURITY WARNING:
        This method should NEVER be exposed via API endpoints.
        Only use internally for agent execution.

        Args:
            organization_id: Organization ID
            secret_name: Secret key name
            domain_id: Optional domain ID

        Returns:
            Secret value or None if not found
        """
        secret_id = self.get_secret_id(organization_id, domain_id, secret_name)

        try:
            response = self.client.get_secret_value(SecretId=secret_id)

            # Log access for audit (but NOT the value)
            logger.info(
                f"Secret retrieved: {secret_id}",
                extra={
                    "organization_id": organization_id,
                    "domain_id": domain_id,
                    "secret_name": secret_name,
                    "action": "GET_SECRET",
                },
            )

            return response["SecretString"]

        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                logger.warning(f"Secret not found: {secret_id}")
                return None
            else:
                logger.error(f"Error retrieving secret {secret_id}: {e}")
                return None

    async def delete_secret(
        self, organization_id: str, secret_name: str, domain_id: str | None = None, force: bool = False
    ) -> bool:
        """
        Delete a secret.

        Args:
            organization_id: Organization ID
            secret_name: Secret key name
            domain_id: Optional domain ID
            force: If True, delete immediately. Otherwise, schedule for deletion

        Returns:
            True if successful
        """
        secret_id = self.get_secret_id(organization_id, domain_id, secret_name)

        try:
            if force:
                # Immediate deletion (LocalStack only, not supported in AWS)
                self.client.delete_secret(SecretId=secret_id, ForceDeleteWithoutRecovery=True)
            else:
                # Schedule for deletion (30 days recovery window)
                self.client.delete_secret(SecretId=secret_id, RecoveryWindowInDays=30)

            logger.info(
                f"Secret deleted: {secret_id}",
                extra={
                    "organization_id": organization_id,
                    "domain_id": domain_id,
                    "secret_name": secret_name,
                    "action": "DELETE_SECRET",
                    "force": force,
                },
            )

            return True

        except ClientError as e:
            logger.error(f"Failed to delete secret {secret_id}: {e}")
            return False

    async def list_secrets(self, organization_id: str, domain_id: str | None = None) -> list[dict]:
        """
        List all secrets for an organization (metadata only).

        Returns list of secret metadata WITHOUT values.
        Safe to expose to frontend.

        Args:
            organization_id: Organization ID
            domain_id: Optional domain ID to filter by

        Returns:
            List of secret metadata dicts
        """
        prefix = self.get_secret_id(organization_id, domain_id, "")

        try:
            response = self.client.list_secrets()

            secrets = []
            for secret in response.get("SecretList", []):
                secret_name = secret.get("Name", "")

                # Filter by organization/domain prefix
                if secret_name.startswith(prefix):
                    # Extract just the key name
                    key_name = secret_name.split("/")[-1]

                    secrets.append(
                        {
                            "secret_name": key_name,
                            "secret_id": secret_name,
                            "description": secret.get("Description"),
                            "created_date": secret.get("CreatedDate"),
                            "last_changed_date": secret.get("LastChangedDate"),
                            "last_accessed_date": secret.get("LastAccessedDate"),
                        }
                    )

            return secrets

        except ClientError as e:
            logger.error(f"Failed to list secrets for {organization_id}: {e}")
            return []


# Singleton instance
secrets_manager = SecretsConfig()


# ============================================================================
# HELPER FUNCTIONS FOR COMMON SECRET TYPES
# ============================================================================


async def get_llm_api_key(organization_id: str, provider: str, domain_id: str | None = None) -> str | None:
    """
    Get LLM provider API key for organization.

    Args:
        organization_id: Organization ID
        provider: Provider name ("openai", "anthropic", "deepgram", etc.)
        domain_id: Optional domain ID

    Returns:
        API key or None
    """
    secret_name = f"{provider}_api_key"
    return await secrets_manager.get_secret(organization_id, secret_name, domain_id)


async def get_integration_credentials(
    organization_id: str, integration: str, domain_id: str | None = None
) -> dict | None:
    """
    Get integration credentials (may include multiple fields).

    For integrations that need multiple credentials (e.g., OAuth),
    store as JSON in secret value.

    Args:
        organization_id: Organization ID
        integration: Integration name ("github", "notion", "n8n", etc.)
        domain_id: Optional domain ID

    Returns:
        Credentials dict or None
    """
    import json

    secret_name = f"{integration}_credentials"
    secret_value = await secrets_manager.get_secret(organization_id, secret_name, domain_id)

    if secret_value:
        try:
            return json.loads(secret_value)
        except json.JSONDecodeError:
            # Assume it's a simple API key
            return {"api_key": secret_value}

    return None
