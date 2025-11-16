"""
Agent Foundry Compiler API
FastAPI service for DIS → Agent YAML compilation
"""

import os
import json
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from compiler.dis_compiler import DISCompiler, CompilerResult


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class CompileRequest(BaseModel):
    """Request to compile DIS JSON to Agent YAML"""
    dossier_json: dict


class CompileResponse(BaseModel):
    """Compilation result"""
    agent_id: str
    agent_yaml: str
    success: bool
    warnings: list[str] = []
    errors: list[str] = []


# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="Agent Foundry Compiler",
    description="DIS 1.6.0 to LangGraph Agent YAML compiler",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# COMPILER ENDPOINTS
# ============================================================================

@app.post("/api/compile", response_model=CompileResponse)
async def compile_dossier(request: CompileRequest):
    """
    Compile a DIS dossier JSON to Agent YAML.
    
    Expects full DIS 1.6.0 dossier structure with:
    - header
    - dossierSpecificDefinitions
        - agenticTriplets
        - functionCatalogEntries
        - tripletFunctionMatrixEntries
        - etc.
    """
    compiler = DISCompiler()
    result = compiler.compile_dossier(request.dossier_json)
    
    return CompileResponse(
        agent_id=result.agent_id,
        agent_yaml=result.agent_yaml,
        success=result.success,
        warnings=result.warnings,
        errors=result.errors
    )


@app.post("/api/compile/upload")
async def compile_upload(file: UploadFile = File(...)):
    """
    Upload a DIS JSON file and compile it.
    Returns the generated Agent YAML.
    """
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="File must be JSON")
    
    try:
        # Read uploaded file
        content = await file.read()
        dossier_json = json.loads(content)
        
        # Compile
        compiler = DISCompiler()
        result = compiler.compile_dossier(dossier_json)
        
        if not result.success:
            raise HTTPException(
                status_code=400,
                detail=f"Compilation failed: {', '.join(result.errors)}"
            )
        
        return CompileResponse(
            agent_id=result.agent_id,
            agent_yaml=result.agent_yaml,
            success=result.success,
            warnings=result.warnings,
            errors=result.errors
        )
        
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/compile/save/{agent_id}")
async def compile_and_save(
    agent_id: str,
    request: CompileRequest
):
    """
    Compile DIS and save the resulting Agent YAML to the agent registry.
    This triggers hot-reload in the platform.
    """
    compiler = DISCompiler()
    result = compiler.compile_dossier(request.dossier_json)
    
    if not result.success:
        raise HTTPException(
            status_code=400,
            detail=f"Compilation failed: {', '.join(result.errors)}"
        )
    
    # Save to agents directory
    agents_dir = Path("/app/agents")
    agents_dir.mkdir(exist_ok=True)
    
    yaml_path = agents_dir / f"{agent_id}.agent.yaml"
    yaml_path.write_text(result.agent_yaml)
    
    return {
        "status": "saved",
        "agent_id": agent_id,
        "yaml_path": str(yaml_path),
        "warnings": result.warnings
    }


# ============================================================================
# STATUS ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Health check"""
    return {
        "service": "agent-foundry-compiler",
        "status": "operational",
        "version": "1.0.0",
        "dis_version": "1.6.0"
    }


@app.get("/health")
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "compiler": "operational",
        "dis_schema_url": os.getenv(
            "DIS_SCHEMA_URL",
            "https://schemas.domainintelligenceschema.org/dis/1.6.0"
        )
    }


# ============================================================================
# STARTUP
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8002")),
        reload=True
    )
