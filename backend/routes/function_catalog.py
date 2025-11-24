"""
Function Catalog API Routes

Provides CRUD operations for the function catalog and agent-tool bindings.
"""

import json
import logging
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Pydantic Models
# ============================================================================


class FunctionCatalogBase(BaseModel):
    name: str = Field(..., description="Unique function name (e.g., slack.postMessage)")
    display_name: str = Field(..., description="Human-readable name")
    description: str | None = None
    category: str = Field(..., description="Category (ITSM, Messaging, etc.)")
    type: str = Field(..., description="Type: integration | custom | builtin")
    integration_tool_name: str | None = Field(None, description="Link to n8n integration tool")
    input_schema: dict = Field(default_factory=dict, description="JSON Schema for inputs")
    output_schema: dict = Field(default_factory=dict, description="JSON Schema for outputs")
    handler_code: str | None = None
    handler_type: str | None = Field(None, description="python | javascript | external")
    tags: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    is_active: bool = True
    required_permissions: list[str] = Field(default_factory=list)


class FunctionCatalogCreate(FunctionCatalogBase):
    created_by: str | None = None


class FunctionCatalogUpdate(BaseModel):
    display_name: str | None = None
    description: str | None = None
    category: str | None = None
    input_schema: dict | None = None
    output_schema: dict | None = None
    handler_code: str | None = None
    handler_type: str | None = None
    tags: list[str] | None = None
    metadata: dict | None = None
    is_active: bool | None = None
    required_permissions: list[str] | None = None
    updated_by: str | None = None


class FunctionCatalogResponse(FunctionCatalogBase):
    id: str
    created_by: str | None = None
    updated_by: str | None = None
    created_at: str
    updated_at: str


class AgentToolBinding(BaseModel):
    id: str
    agent_id: str
    function_id: str
    is_enabled: bool
    config: dict
    created_by: str | None = None
    updated_by: str | None = None
    created_at: str
    updated_at: str


class AgentToolBindingCreate(BaseModel):
    function_id: str
    is_enabled: bool = True
    config: dict = Field(default_factory=dict)
    created_by: str | None = None


# ============================================================================
# Database Operations
# ============================================================================


class FunctionCatalogDB:
    """Database operations for function catalog"""

    def __init__(self, db_conn):
        self.conn = db_conn

    def list_functions(
        self,
        category: str | None = None,
        type: str | None = None,
        is_active: bool | None = None,
    ) -> list[FunctionCatalogResponse]:
        """List all functions with optional filters"""
        query = "SELECT * FROM function_catalog WHERE 1=1"
        params = []

        if category:
            query += " AND category = ?"
            params.append(category)
        if type:
            query += " AND type = ?"
            params.append(type)
        if is_active is not None:
            query += " AND is_active = ?"
            params.append(1 if is_active else 0)

        query += " ORDER BY category, name"

        cursor = self.conn.execute(query, params)
        rows = cursor.fetchall()

        functions = []
        for row in rows:
            functions.append(
                FunctionCatalogResponse(
                    id=row[0],
                    name=row[1],
                    display_name=row[2],
                    description=row[3],
                    category=row[4],
                    type=row[5],
                    integration_tool_name=row[6],
                    input_schema=json.loads(row[7]) if row[7] else {},
                    output_schema=json.loads(row[8]) if row[8] else {},
                    handler_code=row[9],
                    handler_type=row[10],
                    tags=json.loads(row[11]) if row[11] else [],
                    metadata=json.loads(row[12]) if row[12] else {},
                    is_active=bool(row[13]),
                    required_permissions=json.loads(row[14]) if row[14] else [],
                    created_by=row[15],
                    updated_by=row[16],
                    created_at=row[17],
                    updated_at=row[18],
                )
            )

        return functions

    def get_function(self, function_id: str) -> FunctionCatalogResponse | None:
        """Get a single function by ID"""
        cursor = self.conn.execute("SELECT * FROM function_catalog WHERE id = ?", (function_id,))
        row = cursor.fetchone()

        if not row:
            return None

        return FunctionCatalogResponse(
            id=row[0],
            name=row[1],
            display_name=row[2],
            description=row[3],
            category=row[4],
            type=row[5],
            integration_tool_name=row[6],
            input_schema=json.loads(row[7]) if row[7] else {},
            output_schema=json.loads(row[8]) if row[8] else {},
            handler_code=row[9],
            handler_type=row[10],
            tags=json.loads(row[11]) if row[11] else [],
            metadata=json.loads(row[12]) if row[12] else {},
            is_active=bool(row[13]),
            required_permissions=json.loads(row[14]) if row[14] else [],
            created_by=row[15],
            updated_by=row[16],
            created_at=row[17],
            updated_at=row[18],
        )

    def create_function(self, data: FunctionCatalogCreate) -> FunctionCatalogResponse:
        """Create a new function"""
        function_id = str(uuid.uuid4())

        self.conn.execute(
            """
            INSERT INTO function_catalog (
                id, name, display_name, description, category, type,
                integration_tool_name, input_schema, output_schema,
                handler_code, handler_type, tags, metadata, is_active,
                required_permissions, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                function_id,
                data.name,
                data.display_name,
                data.description,
                data.category,
                data.type,
                data.integration_tool_name,
                json.dumps(data.input_schema),
                json.dumps(data.output_schema),
                data.handler_code,
                data.handler_type,
                json.dumps(data.tags),
                json.dumps(data.metadata),
                1 if data.is_active else 0,
                json.dumps(data.required_permissions),
                data.created_by,
            ),
        )
        self.conn.commit()

        return self.get_function(function_id)

    def update_function(self, function_id: str, data: FunctionCatalogUpdate) -> FunctionCatalogResponse | None:
        """Update an existing function"""
        # Build dynamic UPDATE query
        updates = []
        params = []

        if data.display_name is not None:
            updates.append("display_name = ?")
            params.append(data.display_name)
        if data.description is not None:
            updates.append("description = ?")
            params.append(data.description)
        if data.category is not None:
            updates.append("category = ?")
            params.append(data.category)
        if data.input_schema is not None:
            updates.append("input_schema = ?")
            params.append(json.dumps(data.input_schema))
        if data.output_schema is not None:
            updates.append("output_schema = ?")
            params.append(json.dumps(data.output_schema))
        if data.handler_code is not None:
            updates.append("handler_code = ?")
            params.append(data.handler_code)
        if data.handler_type is not None:
            updates.append("handler_type = ?")
            params.append(data.handler_type)
        if data.tags is not None:
            updates.append("tags = ?")
            params.append(json.dumps(data.tags))
        if data.metadata is not None:
            updates.append("metadata = ?")
            params.append(json.dumps(data.metadata))
        if data.is_active is not None:
            updates.append("is_active = ?")
            params.append(1 if data.is_active else 0)
        if data.required_permissions is not None:
            updates.append("required_permissions = ?")
            params.append(json.dumps(data.required_permissions))
        if data.updated_by is not None:
            updates.append("updated_by = ?")
            params.append(data.updated_by)

        if not updates:
            return self.get_function(function_id)

        updates.append("updated_at = datetime('now', 'utc')")
        params.append(function_id)

        query = f"UPDATE function_catalog SET {', '.join(updates)} WHERE id = ?"
        self.conn.execute(query, params)
        self.conn.commit()

        return self.get_function(function_id)

    def delete_function(self, function_id: str) -> bool:
        """Delete a function"""
        cursor = self.conn.execute("DELETE FROM function_catalog WHERE id = ?", (function_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    def list_agent_tools(self, agent_id: str) -> list[AgentToolBinding]:
        """List all tools bound to an agent"""
        cursor = self.conn.execute(
            "SELECT * FROM agent_tools WHERE agent_id = ? ORDER BY created_at",
            (agent_id,),
        )
        rows = cursor.fetchall()

        bindings = []
        for row in rows:
            bindings.append(
                AgentToolBinding(
                    id=row[0],
                    agent_id=row[1],
                    function_id=row[2],
                    is_enabled=bool(row[3]),
                    config=json.loads(row[4]) if row[4] else {},
                    created_by=row[5],
                    updated_by=row[6],
                    created_at=row[7],
                    updated_at=row[8],
                )
            )

        return bindings

    def create_agent_tool_binding(self, agent_id: str, data: AgentToolBindingCreate) -> AgentToolBinding:
        """Bind a tool to an agent"""
        binding_id = str(uuid.uuid4())

        self.conn.execute(
            """
            INSERT INTO agent_tools (
                id, agent_id, function_id, is_enabled, config, created_by
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                binding_id,
                agent_id,
                data.function_id,
                1 if data.is_enabled else 0,
                json.dumps(data.config),
                data.created_by,
            ),
        )
        self.conn.commit()

        cursor = self.conn.execute("SELECT * FROM agent_tools WHERE id = ?", (binding_id,))
        row = cursor.fetchone()

        return AgentToolBinding(
            id=row[0],
            agent_id=row[1],
            function_id=row[2],
            is_enabled=bool(row[3]),
            config=json.loads(row[4]) if row[4] else {},
            created_by=row[5],
            updated_by=row[6],
            created_at=row[7],
            updated_at=row[8],
        )

    def delete_agent_tool_binding(self, agent_id: str, function_id: str) -> bool:
        """Unbind a tool from an agent"""
        cursor = self.conn.execute(
            "DELETE FROM agent_tools WHERE agent_id = ? AND function_id = ?",
            (agent_id, function_id),
        )
        self.conn.commit()
        return cursor.rowcount > 0


# ============================================================================
# API Endpoints
# ============================================================================

# Note: These will be registered in main.py with db dependency injection


def get_function_catalog_routes(db_conn):
    """Factory function to create routes with db connection"""

    @router.get("/api/function-catalog", response_model=list[FunctionCatalogResponse])
    async def list_functions(
        category: str | None = None,
        type: str | None = None,
        is_active: bool | None = None,
    ):
        """List all functions in the catalog"""
        try:
            db = FunctionCatalogDB(db_conn)
            return db.list_functions(category=category, type=type, is_active=is_active)
        except Exception as exc:
            logger.error("Failed to list functions: %s", exc, exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to list functions")

    @router.get("/api/function-catalog/{function_id}", response_model=FunctionCatalogResponse)
    async def get_function(function_id: str):
        """Get a single function by ID"""
        try:
            db = FunctionCatalogDB(db_conn)
            function = db.get_function(function_id)
            if not function:
                raise HTTPException(status_code=404, detail="Function not found")
            return function
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("Failed to get function: %s", exc, exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to get function")

    @router.post("/api/function-catalog", response_model=FunctionCatalogResponse)
    async def create_function(data: FunctionCatalogCreate):
        """Create a new function"""
        try:
            db = FunctionCatalogDB(db_conn)
            return db.create_function(data)
        except Exception as exc:
            logger.error("Failed to create function: %s", exc, exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to create function")

    @router.put("/api/function-catalog/{function_id}", response_model=FunctionCatalogResponse)
    async def update_function(function_id: str, data: FunctionCatalogUpdate):
        """Update an existing function"""
        try:
            db = FunctionCatalogDB(db_conn)
            function = db.update_function(function_id, data)
            if not function:
                raise HTTPException(status_code=404, detail="Function not found")
            return function
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("Failed to update function: %s", exc, exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to update function")

    @router.delete("/api/function-catalog/{function_id}")
    async def delete_function(function_id: str):
        """Delete a function"""
        try:
            db = FunctionCatalogDB(db_conn)
            deleted = db.delete_function(function_id)
            if not deleted:
                raise HTTPException(status_code=404, detail="Function not found")
            return {"message": "Function deleted successfully"}
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("Failed to delete function: %s", exc, exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to delete function")

    @router.get("/api/agents/{agent_id}/tools", response_model=list[AgentToolBinding])
    async def list_agent_tools(agent_id: str):
        """List all tools bound to an agent"""
        try:
            db = FunctionCatalogDB(db_conn)
            return db.list_agent_tools(agent_id)
        except Exception as exc:
            logger.error("Failed to list agent tools: %s", exc, exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to list agent tools")

    @router.post("/api/agents/{agent_id}/tools", response_model=AgentToolBinding)
    async def create_agent_tool_binding(agent_id: str, data: AgentToolBindingCreate):
        """Bind a tool to an agent"""
        try:
            db = FunctionCatalogDB(db_conn)
            return db.create_agent_tool_binding(agent_id, data)
        except Exception as exc:
            logger.error("Failed to bind tool to agent: %s", exc, exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to bind tool to agent")

    @router.delete("/api/agents/{agent_id}/tools/{function_id}")
    async def delete_agent_tool_binding(agent_id: str, function_id: str):
        """Unbind a tool from an agent"""
        try:
            db = FunctionCatalogDB(db_conn)
            deleted = db.delete_agent_tool_binding(agent_id, function_id)
            if not deleted:
                raise HTTPException(status_code=404, detail="Tool binding not found")
            return {"message": "Tool unbound successfully"}
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("Failed to unbind tool from agent: %s", exc, exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to unbind tool")

    return router
