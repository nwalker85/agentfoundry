"""
Zitadel OIDC Client Configuration
---------------------------------
Retrieves Zitadel configuration from LocalStack Secrets Manager
and provides JWKS-based RS256 token validation.

Development: Uses LocalStack for secrets, Docker DNS for Zitadel
Production: Uses AWS Secrets Manager, external Zitadel instance
"""

import json
import logging
import time
from dataclasses import dataclass
from typing import Any

import httpx
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError

from backend.config.secrets import secrets_manager

logger = logging.getLogger(__name__)


@dataclass
class ZitadelConfig:
    """Zitadel OIDC configuration loaded from LocalStack"""

    client_id: str
    client_secret: str
    issuer_url: str
    jwks_url: str
    token_endpoint: str
    authorization_endpoint: str
    userinfo_endpoint: str


class JWKSCache:
    """
    Cached JWKS (JSON Web Key Set) for RS256 token validation.

    Caches the public keys from Zitadel's JWKS endpoint to avoid
    fetching on every request. Refreshes every 5 minutes or on error.
    """

    def __init__(self, jwks_url: str, cache_ttl: int = 300):
        """
        Initialize JWKS cache.

        Args:
            jwks_url: Zitadel JWKS endpoint URL
            cache_ttl: Cache time-to-live in seconds (default 5 minutes)
        """
        self.jwks_url = jwks_url
        self.cache_ttl = cache_ttl
        self._jwks: dict[str, Any] | None = None
        self._last_refresh: float = 0

    def _should_refresh(self) -> bool:
        """Check if cache needs refresh"""
        if self._jwks is None:
            return True
        return time.time() - self._last_refresh > self.cache_ttl

    async def get_jwks(self) -> dict[str, Any]:
        """
        Get JWKS, refreshing from Zitadel if needed.

        Returns:
            JWKS dict with 'keys' array
        """
        if self._should_refresh():
            await self._refresh_jwks()

        if self._jwks is None:
            raise RuntimeError("Failed to fetch JWKS from Zitadel")

        return self._jwks

    async def _refresh_jwks(self) -> None:
        """Fetch fresh JWKS from Zitadel"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.jwks_url, timeout=10.0)
                response.raise_for_status()

                self._jwks = response.json()
                self._last_refresh = time.time()

                logger.info(
                    f"JWKS refreshed from {self.jwks_url}",
                    extra={
                        "key_count": len(self._jwks.get("keys", [])),
                        "action": "JWKS_REFRESH",
                    },
                )

        except httpx.HTTPError as e:
            logger.error(
                f"Failed to fetch JWKS from {self.jwks_url}: {e}",
                extra={"action": "JWKS_REFRESH_FAILED"},
            )
            # Don't clear existing cache on error - use stale keys

    def clear(self) -> None:
        """Clear the cache (force refresh on next request)"""
        self._jwks = None
        self._last_refresh = 0


class ZitadelClient:
    """
    Zitadel OIDC client for Agent Foundry.

    Handles:
    - Loading configuration from LocalStack Secrets Manager
    - JWKS-based RS256 token validation
    - Token introspection (optional)
    """

    def __init__(self):
        self._config: ZitadelConfig | None = None
        self._jwks_cache: JWKSCache | None = None
        self._initialized = False

    async def initialize(self) -> bool:
        """
        Load Zitadel configuration from LocalStack.

        Returns:
            True if configuration loaded successfully
        """
        if self._initialized:
            return True

        try:
            # Fetch config from LocalStack (platform-level secret)
            config_json = await secrets_manager.get_secret(
                organization_id="platform",
                secret_name="zitadel_config",
                domain_id=None,
            )

            if not config_json:
                logger.warning(
                    "Zitadel configuration not found in LocalStack. "
                    "Run: python scripts/zitadel_setup_localstack.py <client_id> <secret>"
                )
                return False

            config_data = json.loads(config_json)

            self._config = ZitadelConfig(
                client_id=config_data["client_id"],
                client_secret=config_data["client_secret"],
                issuer_url=config_data["issuer_url"],
                jwks_url=config_data["jwks_url"],
                token_endpoint=config_data.get(
                    "token_endpoint", f"{config_data['issuer_url']}/oauth/v2/token"
                ),
                authorization_endpoint=config_data.get(
                    "authorization_endpoint", f"{config_data['issuer_url']}/oauth/v2/authorize"
                ),
                userinfo_endpoint=config_data.get(
                    "userinfo_endpoint", f"{config_data['issuer_url']}/oidc/v1/userinfo"
                ),
            )

            # Initialize JWKS cache
            self._jwks_cache = JWKSCache(self._config.jwks_url)

            self._initialized = True

            logger.info(
                f"Zitadel client initialized: issuer={self._config.issuer_url}",
                extra={"action": "ZITADEL_INIT"},
            )

            return True

        except json.JSONDecodeError as e:
            logger.error(f"Invalid Zitadel config JSON: {e}")
            return False
        except KeyError as e:
            logger.error(f"Missing required Zitadel config field: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize Zitadel client: {e}")
            return False

    @property
    def config(self) -> ZitadelConfig | None:
        """Get loaded configuration (None if not initialized)"""
        return self._config

    @property
    def is_available(self) -> bool:
        """Check if Zitadel client is initialized and ready"""
        return self._initialized and self._config is not None

    async def validate_token(self, token: str) -> dict[str, Any] | None:
        """
        Validate a Zitadel-issued JWT using RS256 and JWKS.

        Args:
            token: JWT access token from Zitadel

        Returns:
            Decoded token payload if valid, None otherwise
        """
        if not self._initialized:
            if not await self.initialize():
                logger.error("Cannot validate token: Zitadel not initialized")
                return None

        if not self._config or not self._jwks_cache:
            return None

        try:
            # Fetch JWKS (cached)
            jwks = await self._jwks_cache.get_jwks()

            # Decode and validate JWT
            payload = jwt.decode(
                token,
                jwks,
                algorithms=["RS256"],
                audience=self._config.client_id,
                issuer=self._config.issuer_url,
                options={
                    "verify_signature": True,
                    "verify_aud": True,
                    "verify_iss": True,
                    "verify_exp": True,
                },
            )

            logger.debug(
                f"Zitadel token validated: sub={payload.get('sub')}",
                extra={
                    "subject": payload.get("sub"),
                    "action": "ZITADEL_TOKEN_VALID",
                },
            )

            return payload

        except ExpiredSignatureError:
            logger.warning("Zitadel token expired", extra={"action": "ZITADEL_TOKEN_EXPIRED"})
            return None

        except JWTError as e:
            # Try refreshing JWKS and retry once (key rotation scenario)
            logger.warning(f"JWT validation failed, refreshing JWKS: {e}")
            self._jwks_cache.clear()

            try:
                jwks = await self._jwks_cache.get_jwks()
                payload = jwt.decode(
                    token,
                    jwks,
                    algorithms=["RS256"],
                    audience=self._config.client_id,
                    issuer=self._config.issuer_url,
                )
                return payload
            except JWTError as retry_error:
                logger.error(
                    f"Zitadel token validation failed after JWKS refresh: {retry_error}",
                    extra={"action": "ZITADEL_TOKEN_INVALID"},
                )
                return None

        except Exception as e:
            logger.error(f"Unexpected error validating Zitadel token: {e}")
            return None

    async def get_userinfo(self, access_token: str) -> dict[str, Any] | None:
        """
        Fetch user info from Zitadel userinfo endpoint.

        Args:
            access_token: Valid Zitadel access token

        Returns:
            User info dict or None on error
        """
        if not self._config:
            return None

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self._config.userinfo_endpoint,
                    headers={"Authorization": f"Bearer {access_token}"},
                    timeout=10.0,
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch userinfo: {e}")
            return None


# Singleton instance
zitadel_client = ZitadelClient()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


async def validate_zitadel_token(token: str) -> dict[str, Any] | None:
    """
    Convenience function to validate a Zitadel token.

    Args:
        token: JWT access token

    Returns:
        Decoded payload or None if invalid
    """
    return await zitadel_client.validate_token(token)


async def is_zitadel_available() -> bool:
    """
    Check if Zitadel is configured and available.

    Returns:
        True if Zitadel client can be initialized
    """
    if zitadel_client.is_available:
        return True
    return await zitadel_client.initialize()
