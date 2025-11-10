"""
MCP Server for Engineering Department
A FastAPI-based server implementing Model Context Protocol.
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import uvicorn

# Load environment variables
load_dotenv('.env.local')


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    print("🚀 Starting Engineering Department MCP Server...")
    print(f"📊 Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"🏢 Tenant ID: {os.getenv('TENANT_ID', 'unknown')}")
    yield
    print("🛑 Shutting down MCP Server...")


# Initialize FastAPI app
app = FastAPI(
    title="Engineering Department MCP Server",
    description="Model Context Protocol server for engineering workflows",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint for health check."""
    return {
        "service": "Engineering Department MCP Server",
        "version": "0.1.0",
        "status": "healthy",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "tenant_id": os.getenv("TENANT_ID", "unknown"),
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "mcp-server"}


@app.get("/api/status")
async def api_status():
    """API status endpoint."""
    return {
        "api_version": "v1",
        "status": "operational",
        "integrations": {
            "notion": bool(os.getenv("NOTION_API_TOKEN")),
            "openai": bool(os.getenv("OPENAI_API_KEY")),
            "github": bool(os.getenv("GITHUB_TOKEN")),
        }
    }


if __name__ == "__main__":
    port = int(os.getenv("MCP_SERVER_PORT", 8001))
    uvicorn.run(
        "mcp_server:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )