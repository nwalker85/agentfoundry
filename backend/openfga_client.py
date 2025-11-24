"""
OpenFGA Client for Agent Foundry
---------------------------------
Provides relationship-based access control (ReBAC) using OpenFGA.

This replaces the traditional RBAC system with a flexible, hierarchical
authorization model based on Google's Zanzibar.

Usage:
    from backend.openfga_client import fga_client

    # Check permission
    allowed = await fga_client.check(
        user="user:alice",
        relation="can_execute",
        object="agent:my-agent"
    )

    # Write relationships
    await fga_client.write([
        {
            "user": "user:alice",
            "relation": "owner",
            "object": "agent:my-agent"
        }
    ])

    # List accessible resources
    agents = await fga_client.list_objects(
        user="user:alice",
        relation="can_execute",
        type="agent"
    )
"""

import logging
import os
from datetime import datetime, timedelta

import httpx

from backend.config.services import SERVICES

logger = logging.getLogger(__name__)


class OpenFGAClient:
    """
    Client for OpenFGA authorization service.

    Provides high-level methods for authorization checks and relationship management.
    """

    def __init__(self):
        self.base_url = SERVICES.get_service_url("OPENFGA")

        # Configuration retrieved from LocalStack (not .env!)
        self.store_id = None
        self.auth_model_id = None
        self._initialized = False

        # Cache for authorization checks
        self._cache: dict[str, tuple[bool, datetime]] = {}
        self._cache_ttl = timedelta(seconds=int(os.getenv("OPENFGA_CACHE_TTL", "60")))

        logger.info(f"OpenFGA client initialized: {self.base_url}")

    async def initialize(self):
        """
        Initialize OpenFGA client by retrieving config from LocalStack.

        Retrieves:
        - openfga_store_id: Which OpenFGA store to use
        - openfga_model_id: Which authorization model version

        These are stored in LocalStack, not .env!
        """
        if self._initialized:
            return

        from backend.config.secrets import secrets_manager

        # Get OpenFGA config from LocalStack
        # Stored as platform-level secrets (no org_id)
        try:
            import json

            # Retrieve OpenFGA configuration
            config_json = await secrets_manager.get_secret(
                organization_id="platform", secret_name="openfga_config", domain_id=None
            )

            if config_json:
                config = json.loads(config_json)
                self.store_id = config.get("store_id")
                self.auth_model_id = config.get("model_id")
                logger.info(f"OpenFGA config loaded from LocalStack: store={self.store_id}")
            else:
                # Fallback to environment variables for initial setup
                self.store_id = os.getenv("OPENFGA_STORE_ID")
                self.auth_model_id = os.getenv("OPENFGA_AUTH_MODEL_ID")
                logger.warning("OpenFGA config not in LocalStack, using env vars as fallback")
        except Exception as e:
            logger.warning(f"Failed to load OpenFGA config from LocalStack: {e}")
            # Fallback to environment variables
            self.store_id = os.getenv("OPENFGA_STORE_ID")
            self.auth_model_id = os.getenv("OPENFGA_AUTH_MODEL_ID")

        if not self.store_id or not self.auth_model_id:
            logger.error("OpenFGA configuration missing! Run: python scripts/openfga_init.py")

        self._initialized = True

    def _get_cache_key(self, user: str, relation: str, obj: str) -> str:
        """Generate cache key for authorization check."""
        return f"{user}:{relation}:{obj}"

    def _is_cache_valid(self, timestamp: datetime) -> bool:
        """Check if cached result is still valid."""
        return datetime.now() - timestamp < self._cache_ttl

    async def _request(self, method: str, endpoint: str, data: dict | None = None) -> dict:
        """Make HTTP request to OpenFGA."""
        url = f"{self.base_url}/stores/{self.store_id}{endpoint}"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(method=method, url=url, json=data, timeout=5.0)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"OpenFGA request failed: {e}")
                logger.error(f"Response body: {e.response.text}")
                raise
            except httpx.HTTPError as e:
                logger.error(f"OpenFGA request failed: {e}")
                raise

    # ========================================================================
    # AUTHORIZATION CHECKS
    # ========================================================================

    async def check(
        self, user: str, relation: str, object: str, contextual_tuples: list[dict] | None = None, use_cache: bool = True
    ) -> bool:
        # Lazy initialization from LocalStack
        await self.initialize()
        """
        Check if user has permission on object.
        
        Args:
            user: User identifier (e.g., "user:alice")
            relation: Permission to check (e.g., "can_execute")
            object: Object identifier (e.g., "agent:my-agent")
            contextual_tuples: Additional temporary relationships for this check
            use_cache: Whether to use cached results
        
        Returns:
            True if user has permission, False otherwise
        
        Examples:
            >>> await fga_client.check("user:alice", "can_execute", "agent:my-agent")
            True
            
            >>> await fga_client.check("user:bob", "can_update", "secret:openai_key")
            False
        """
        cache_key = self._get_cache_key(user, relation, object)

        # Check cache
        if use_cache and cache_key in self._cache:
            result, timestamp = self._cache[cache_key]
            if self._is_cache_valid(timestamp):
                return result

        # Make check request
        request_data = {
            "authorization_model_id": self.auth_model_id,
            "tuple_key": {"user": user, "relation": relation, "object": object},
        }

        if contextual_tuples:
            request_data["contextual_tuples"] = {"tuple_keys": contextual_tuples}

        try:
            response = await self._request("POST", "/check", request_data)
            allowed = response.get("allowed", False)

            # Cache result
            self._cache[cache_key] = (allowed, datetime.now())

            logger.debug(f"OpenFGA check: {user} {relation} {object} = {allowed}")

            return allowed
        except Exception as e:
            logger.error(f"OpenFGA check failed: {e}")
            # Fail closed (deny by default)
            return False

    async def batch_check(self, checks: list[dict[str, str]]) -> list[bool]:
        """
        Check multiple permissions at once.

        Args:
            checks: List of {user, relation, object} dicts

        Returns:
            List of boolean results in same order

        Example:
            >>> results = await fga_client.batch_check([
            ...     {"user": "user:alice", "relation": "can_read", "object": "agent:1"},
            ...     {"user": "user:alice", "relation": "can_read", "object": "agent:2"}
            ... ])
            [True, False]
        """
        # OpenFGA doesn't have native batch check, so we parallelize
        import asyncio

        tasks = [self.check(c["user"], c["relation"], c["object"]) for c in checks]
        return await asyncio.gather(*tasks)

    async def list_objects(
        self, user: str, relation: str, type: str, contextual_tuples: list[dict] | None = None
    ) -> list[str]:
        """
        List all objects of a type that user has permission on.

        Args:
            user: User identifier (e.g., "user:alice")
            relation: Permission to check (e.g., "can_execute")
            type: Object type (e.g., "agent")
            contextual_tuples: Additional temporary relationships

        Returns:
            List of object IDs

        Example:
            >>> agents = await fga_client.list_objects(
            ...     user="user:alice",
            ...     relation="can_execute",
            ...     type="agent"
            ... )
            ["agent:my-agent", "agent:shared-agent"]
        """
        request_data = {"authorization_model_id": self.auth_model_id, "user": user, "relation": relation, "type": type}

        if contextual_tuples:
            request_data["contextual_tuples"] = {"tuple_keys": contextual_tuples}

        try:
            response = await self._request("POST", "/list-objects", request_data)
            objects = response.get("objects", [])

            logger.debug(f"OpenFGA list_objects: {user} {relation} {type} = {len(objects)} objects")

            return objects
        except Exception as e:
            logger.error(f"OpenFGA list_objects failed: {e}")
            return []

    # ========================================================================
    # RELATIONSHIP MANAGEMENT
    # ========================================================================

    async def write(self, writes: list[dict[str, str]], deletes: list[dict[str, str]] | None = None) -> bool:
        """
        Write relationships (tuples) to OpenFGA.

        Args:
            writes: List of tuples to add
            deletes: List of tuples to remove

        Returns:
            True if successful

        Example:
            >>> await fga_client.write([
            ...     {
            ...         "user": "user:alice",
            ...         "relation": "owner",
            ...         "object": "agent:my-agent"
            ...     },
            ...     {
            ...         "user": "domain:my-domain",
            ...         "relation": "parent_domain",
            ...         "object": "agent:my-agent"
            ...     }
            ... ])
        """
        request_data = {"authorization_model_id": self.auth_model_id}

        if writes:
            request_data["writes"] = {"tuple_keys": writes}

        if deletes:
            request_data["deletes"] = {"tuple_keys": deletes}

        try:
            result = await self._request("POST", "/write", request_data)

            # Invalidate affected cache entries
            self._invalidate_cache_for_writes(writes, deletes)

            logger.info(f"OpenFGA write: {len(writes or [])} writes, {len(deletes or [])} deletes")
            return True
        except Exception as e:
            logger.error(f"OpenFGA write failed: {e}")
            logger.error(f"Request data: {request_data}")
            return False

    async def read(
        self, user: str | None = None, relation: str | None = None, object: str | None = None, page_size: int = 100
    ) -> list[dict]:
        """
        Read existing relationship tuples.

        Args:
            user: Filter by user (optional)
            relation: Filter by relation (optional)
            object: Filter by object (optional)
            page_size: Max results to return

        Returns:
            List of tuple dicts

        Example:
            >>> tuples = await fga_client.read(
            ...     user="user:alice",
            ...     relation="owner"
            ... )
            [{"user": "user:alice", "relation": "owner", "object": "agent:1"}, ...]
        """
        request_data = {"authorization_model_id": self.auth_model_id, "page_size": page_size}

        tuple_key = {}
        if user:
            tuple_key["user"] = user
        if relation:
            tuple_key["relation"] = relation
        if object:
            tuple_key["object"] = object

        if tuple_key:
            request_data["tuple_key"] = tuple_key

        try:
            response = await self._request("POST", "/read", request_data)
            tuples = response.get("tuples", [])

            logger.debug(f"OpenFGA read: {len(tuples)} tuples")
            return [t.get("key", {}) for t in tuples]
        except Exception as e:
            logger.error(f"OpenFGA read failed: {e}")
            return []

    def _invalidate_cache_for_writes(self, writes: list[dict] | None = None, deletes: list[dict] | None = None):
        """Invalidate cache entries affected by relationship changes."""
        # For simplicity, clear entire cache on writes
        # In production, could be more selective
        self._cache.clear()

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    async def grant_access(self, user_id: str, resource_type: str, resource_id: str, relation: str) -> bool:
        """
        Grant a user access to a resource.

        Args:
            user_id: User ID (e.g., "alice")
            resource_type: Type (e.g., "agent", "secret")
            resource_id: Resource ID
            relation: Relation to grant (e.g., "viewer", "editor", "owner")

        Example:
            >>> await fga_client.grant_access("alice", "agent", "my-agent", "viewer")
        """
        return await self.write(
            [{"user": f"user:{user_id}", "relation": relation, "object": f"{resource_type}:{resource_id}"}]
        )

    async def revoke_access(self, user_id: str, resource_type: str, resource_id: str, relation: str) -> bool:
        """
        Revoke a user's access to a resource.

        Example:
            >>> await fga_client.revoke_access("alice", "agent", "my-agent", "viewer")
        """
        return await self.write(
            writes=[],
            deletes=[{"user": f"user:{user_id}", "relation": relation, "object": f"{resource_type}:{resource_id}"}],
        )

    async def setup_organization(self, org_id: str, owner_id: str) -> bool:
        """
        Set up initial relationships for a new organization.

        Args:
            org_id: Organization ID
            owner_id: User ID of org owner

        Returns:
            True if successful
        """
        return await self.write([{"user": f"user:{owner_id}", "relation": "owner", "object": f"organization:{org_id}"}])

    async def setup_domain(self, domain_id: str, org_id: str, owner_id: str) -> bool:
        """
        Set up initial relationships for a new domain.
        """
        return await self.write(
            [
                # Link domain to org
                {"user": f"organization:{org_id}", "relation": "parent_org", "object": f"domain:{domain_id}"},
                # Set owner
                {"user": f"user:{owner_id}", "relation": "owner", "object": f"domain:{domain_id}"},
            ]
        )

    async def setup_agent(self, agent_id: str, domain_id: str, owner_id: str) -> bool:
        """
        Set up initial relationships for a new agent.
        """
        return await self.write(
            [
                # Link agent to domain
                {"user": f"domain:{domain_id}", "relation": "parent_domain", "object": f"agent:{agent_id}"},
                # Set owner
                {"user": f"user:{owner_id}", "relation": "owner", "object": f"agent:{agent_id}"},
            ]
        )


# Singleton instance
fga_client = OpenFGAClient()
