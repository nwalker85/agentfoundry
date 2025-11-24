"""
Hierarchy API Routes

Provides API endpoints for organizations, projects, and domains.
Supports cascading dropdowns in the UI for configuration scoping.
"""

import logging
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Pydantic Models
# ============================================================================


class OrganizationBase(BaseModel):
    name: str
    tier: str = "standard"


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationResponse(OrganizationBase):
    id: str
    created_at: str
    updated_at: str


class ProjectBase(BaseModel):
    name: str
    display_name: str
    description: str | None = None
    organization_id: str


class ProjectCreate(ProjectBase):
    pass


class ProjectResponse(ProjectBase):
    id: str
    created_at: str
    updated_at: str


class DomainBase(BaseModel):
    name: str
    display_name: str
    organization_id: str
    project_id: str | None = None
    version: str = "0.1.0"


class DomainCreate(DomainBase):
    pass


class DomainResponse(DomainBase):
    id: str
    created_at: str
    updated_at: str


# ============================================================================
# Database Operations
# ============================================================================


class HierarchyDB:
    """Database operations for hierarchy (orgs/projects/domains)"""

    def __init__(self, db_conn):
        self.conn = db_conn

    # Organizations
    def list_organizations(self) -> list[OrganizationResponse]:
        """List all organizations"""
        cursor = self.conn.execute("SELECT id, name, tier, created_at, updated_at FROM organizations ORDER BY name")
        rows = cursor.fetchall()

        orgs = []
        for row in rows:
            orgs.append(
                OrganizationResponse(
                    id=row["id"],
                    name=row["name"],
                    tier=row["tier"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
            )
        return orgs

    def get_organization(self, org_id: str) -> OrganizationResponse | None:
        """Get a single organization by ID"""
        cursor = self.conn.execute(
            "SELECT id, name, tier, created_at, updated_at FROM organizations WHERE id = ?",
            (org_id,),
        )
        row = cursor.fetchone()

        if not row:
            return None

        return OrganizationResponse(
            id=row["id"],
            name=row["name"],
            tier=row["tier"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def create_organization(self, data: OrganizationCreate) -> OrganizationResponse:
        """Create a new organization"""
        org_id = str(uuid.uuid4())

        self.conn.execute(
            "INSERT INTO organizations (id, name, tier) VALUES (?, ?, ?)",
            (org_id, data.name, data.tier),
        )
        self.conn.commit()

        return self.get_organization(org_id)

    # Projects
    def list_projects(self, organization_id: str | None = None) -> list[ProjectResponse]:
        """List all projects, optionally filtered by organization"""
        query = "SELECT id, organization_id, name, display_name, description, created_at, updated_at FROM projects"
        params = []

        if organization_id:
            query += " WHERE organization_id = ?"
            params.append(organization_id)

        query += " ORDER BY name"

        cursor = self.conn.execute(query, params)
        rows = cursor.fetchall()

        projects = []
        for row in rows:
            projects.append(
                ProjectResponse(
                    id=row["id"],
                    organization_id=row["organization_id"],
                    name=row["name"],
                    display_name=row["display_name"],
                    description=row["description"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
            )
        return projects

    def get_project(self, project_id: str) -> ProjectResponse | None:
        """Get a single project by ID"""
        cursor = self.conn.execute(
            "SELECT id, organization_id, name, display_name, description, created_at, updated_at FROM projects WHERE id = ?",
            (project_id,),
        )
        row = cursor.fetchone()

        if not row:
            return None

        return ProjectResponse(
            id=row["id"],
            organization_id=row["organization_id"],
            name=row["name"],
            display_name=row["display_name"],
            description=row["description"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def create_project(self, data: ProjectCreate) -> ProjectResponse:
        """Create a new project"""
        project_id = str(uuid.uuid4())

        self.conn.execute(
            """
            INSERT INTO projects (id, organization_id, name, display_name, description)
            VALUES (?, ?, ?, ?, ?)
            """,
            (project_id, data.organization_id, data.name, data.display_name, data.description),
        )
        self.conn.commit()

        return self.get_project(project_id)

    # Domains
    def list_domains(
        self,
        organization_id: str | None = None,
        project_id: str | None = None,
    ) -> list[DomainResponse]:
        """List all domains, optionally filtered by organization or project"""
        query = "SELECT id, organization_id, project_id, name, display_name, version, created_at, updated_at FROM domains WHERE 1=1"
        params = []

        if organization_id:
            query += " AND organization_id = ?"
            params.append(organization_id)
        if project_id:
            query += " AND project_id = ?"
            params.append(project_id)

        query += " ORDER BY name"

        cursor = self.conn.execute(query, params)
        rows = cursor.fetchall()

        domains = []
        for row in rows:
            domains.append(
                DomainResponse(
                    id=row["id"],
                    organization_id=row["organization_id"],
                    project_id=row["project_id"],
                    name=row["name"],
                    display_name=row["display_name"],
                    version=row["version"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
            )
        return domains

    def get_domain(self, domain_id: str) -> DomainResponse | None:
        """Get a single domain by ID"""
        cursor = self.conn.execute(
            "SELECT id, organization_id, project_id, name, display_name, version, created_at, updated_at FROM domains WHERE id = ?",
            (domain_id,),
        )
        row = cursor.fetchone()

        if not row:
            return None

        return DomainResponse(
            id=row["id"],
            organization_id=row["organization_id"],
            project_id=row["project_id"],
            name=row["name"],
            display_name=row["display_name"],
            version=row["version"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def create_domain(self, data: DomainCreate) -> DomainResponse:
        """Create a new domain"""
        domain_id = str(uuid.uuid4())

        self.conn.execute(
            """
            INSERT INTO domains (id, organization_id, project_id, name, display_name, version)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                domain_id,
                data.organization_id,
                data.project_id,
                data.name,
                data.display_name,
                data.version,
            ),
        )
        self.conn.commit()

        return self.get_domain(domain_id)


# ============================================================================
# API Endpoints
# ============================================================================


def get_hierarchy_routes(db_conn):
    """Factory function to create routes with db connection"""

    # Organizations
    @router.get("/api/organizations", response_model=list[OrganizationResponse])
    async def list_organizations():
        """List all organizations"""
        try:
            db = HierarchyDB(db_conn)
            return db.list_organizations()
        except Exception as exc:
            logger.error("Failed to list organizations: %s", exc, exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to list organizations")

    @router.get("/api/organizations/{org_id}", response_model=OrganizationResponse)
    async def get_organization(org_id: str):
        """Get a single organization"""
        try:
            db = HierarchyDB(db_conn)
            org = db.get_organization(org_id)
            if not org:
                raise HTTPException(status_code=404, detail="Organization not found")
            return org
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("Failed to get organization: %s", exc, exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to get organization")

    @router.post("/api/organizations", response_model=OrganizationResponse)
    async def create_organization(data: OrganizationCreate):
        """Create a new organization"""
        try:
            db = HierarchyDB(db_conn)
            return db.create_organization(data)
        except Exception as exc:
            logger.error("Failed to create organization: %s", exc, exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to create organization")

    # Projects
    @router.get("/api/projects", response_model=list[ProjectResponse])
    async def list_projects(organization_id: str | None = None):
        """List all projects, optionally filtered by organization"""
        try:
            db = HierarchyDB(db_conn)
            return db.list_projects(organization_id=organization_id)
        except Exception as exc:
            logger.error("Failed to list projects: %s", exc, exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to list projects")

    @router.get("/api/projects/{project_id}", response_model=ProjectResponse)
    async def get_project(project_id: str):
        """Get a single project"""
        try:
            db = HierarchyDB(db_conn)
            project = db.get_project(project_id)
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")
            return project
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("Failed to get project: %s", exc, exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to get project")

    @router.post("/api/projects", response_model=ProjectResponse)
    async def create_project(data: ProjectCreate):
        """Create a new project"""
        try:
            db = HierarchyDB(db_conn)
            return db.create_project(data)
        except Exception as exc:
            logger.error("Failed to create project: %s", exc, exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to create project")

    # Domains
    @router.get("/api/domains", response_model=list[DomainResponse])
    async def list_domains(
        organization_id: str | None = None,
        project_id: str | None = None,
    ):
        """List all domains, optionally filtered by organization or project"""
        try:
            db = HierarchyDB(db_conn)
            return db.list_domains(organization_id=organization_id, project_id=project_id)
        except Exception as exc:
            logger.error("Failed to list domains: %s", exc, exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to list domains")

    @router.get("/api/domains/{domain_id}", response_model=DomainResponse)
    async def get_domain(domain_id: str):
        """Get a single domain"""
        try:
            db = HierarchyDB(db_conn)
            domain = db.get_domain(domain_id)
            if not domain:
                raise HTTPException(status_code=404, detail="Domain not found")
            return domain
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("Failed to get domain: %s", exc, exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to get domain")

    @router.post("/api/domains", response_model=DomainResponse)
    async def create_domain(data: DomainCreate):
        """Create a new domain"""
        try:
            db = HierarchyDB(db_conn)
            return db.create_domain(data)
        except Exception as exc:
            logger.error("Failed to create domain: %s", exc, exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to create domain")

    return router
