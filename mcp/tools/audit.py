"""Audit MCP Tool Implementation."""

import asyncio
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import aiofiles

from mcp.schemas import AuditEntry


class AuditTool:
    """Audit logging tool for MCP operations."""

    def __init__(self, audit_dir: str | None = None):
        self.audit_dir = Path(audit_dir or os.getenv("AUDIT_DIR", "./audit"))
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        self.tenant_id = os.getenv("TENANT_ID", "local-dev")
        self.environment = os.getenv("ENVIRONMENT", "development")

        # Create today's audit file
        today = datetime.utcnow().strftime("%Y%m%d")
        self.audit_file = self.audit_dir / f"actions_{today}.jsonl"

        # Lock for concurrent writes
        self.write_lock = asyncio.Lock()

    async def log_action(
        self,
        actor: str,
        tool: str,
        action: str,
        input_data: dict[str, Any],
        output_data: dict[str, Any] | None = None,
        result: str = "success",
        error: str | None = None,
        request_id: str | None = None,
        duration_ms: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditEntry:
        """Log an action to the audit trail."""

        # Generate hashes for input/output
        input_hash = self._generate_hash(input_data)
        output_hash = self._generate_hash(output_data) if output_data else None

        # Create audit entry
        entry = AuditEntry(
            timestamp=datetime.utcnow(),
            request_id=request_id or self._generate_request_id(),
            actor=actor,
            tenant_id=self.tenant_id,
            tool=tool,
            action=action,
            input_hash=input_hash,
            output_hash=output_hash,
            result=result,
            error=error,
            duration_ms=duration_ms,
            metadata={
                **(metadata or {}),
                "environment": self.environment,
                "input_summary": self._summarize_data(input_data),
                "output_summary": self._summarize_data(output_data) if output_data else None,
            },
        )

        # Write to file
        await self._write_entry(entry)

        return entry

    async def log_tool_call(
        self,
        tool_name: str,
        method: str,
        request: Any,
        response: Any = None,
        error: Exception = None,
        start_time: datetime = None,
    ) -> AuditEntry:
        """Convenience method to log a tool call."""

        # Calculate duration
        duration_ms = None
        if start_time:
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        # Determine result
        if error:
            result = "failure"
            error_str = f"{type(error).__name__}: {error!s}"
        elif response and hasattr(response, "success") and not response.success:
            result = "partial"
            error_str = getattr(response, "error", None)
        else:
            result = "success"
            error_str = None

        # Extract actor from context (would come from auth in production)
        actor = os.getenv("CURRENT_USER", "system")

        # Convert request/response to dicts
        request_dict = request.dict() if hasattr(request, "dict") else {"data": str(request)}
        response_dict = response.dict() if hasattr(response, "dict") else {"data": str(response)}

        return await self.log_action(
            actor=actor,
            tool=tool_name,
            action=method,
            input_data=request_dict,
            output_data=response_dict if not error else None,
            result=result,
            error=error_str,
            duration_ms=duration_ms,
        )

    async def _write_entry(self, entry: AuditEntry):
        """Write an entry to the audit file."""
        async with self.write_lock, aiofiles.open(self.audit_file, mode="a") as f:
            await f.write(entry.to_jsonl() + "\n")

    def _generate_hash(self, data: Any) -> str:
        """Generate a hash for data."""
        if data is None:
            return "null"

        # Convert to JSON string for consistent hashing
        if hasattr(data, "dict"):
            data = data.dict()

        json_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode()).hexdigest()[:16]

    def _generate_request_id(self) -> str:
        """Generate a unique request ID."""
        timestamp = datetime.utcnow().isoformat()
        random_part = hashlib.sha256(os.urandom(32)).hexdigest()[:8]
        return f"{timestamp}-{random_part}"

    def _summarize_data(self, data: Any) -> dict[str, Any]:
        """Create a summary of data for metadata."""
        if data is None:
            return {}

        if hasattr(data, "dict"):
            data = data.dict()

        if not isinstance(data, dict):
            return {"type": type(data).__name__}

        # Extract key fields for summary
        summary = {}

        # Common fields to extract
        for field in ["title", "name", "id", "story_title", "epic_title", "priority", "status"]:
            if field in data:
                summary[field] = data[field]

        # Add counts for lists
        for key, value in data.items():
            if isinstance(value, list):
                summary[f"{key}_count"] = len(value)

        return summary

    async def query_audit_log(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        actor: str | None = None,
        tool: str | None = None,
        action: str | None = None,
        result: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Query the audit log with filters."""

        entries = []

        # Determine which files to read
        if start_date and end_date:
            # Get all files in date range
            current = start_date
            files = []
            while current <= end_date:
                date_str = current.strftime("%Y%m%d")
                file_path = self.audit_dir / f"actions_{date_str}.jsonl"
                if file_path.exists():
                    files.append(file_path)
                current = current.replace(day=current.day + 1)
        else:
            # Just read today's file
            files = [self.audit_file] if self.audit_file.exists() else []

        # Read and filter entries
        for file_path in files:
            async with aiofiles.open(file_path) as f:
                async for line in f:
                    if not line.strip():
                        continue

                    entry = json.loads(line)

                    # Apply filters
                    if actor and entry.get("actor") != actor:
                        continue
                    if tool and entry.get("tool") != tool:
                        continue
                    if action and entry.get("action") != action:
                        continue
                    if result and entry.get("result") != result:
                        continue

                    entries.append(entry)

                    if len(entries) >= limit:
                        return entries

        return entries
