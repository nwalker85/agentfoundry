"""GitHub Repository Operations Tool - For code management, not issues."""

import os
import asyncio
import subprocess
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime
import httpx
from pydantic import BaseModel

from mcp.schemas import AuditEntry


class GitHubRepoTool:
    """GitHub integration for repository operations - clone, pull, commit, push."""
    
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        self.repo = os.getenv("GITHUB_REPO")
        self.default_branch = os.getenv("GITHUB_DEFAULT_BRANCH", "main")
        self.workspace_dir = os.getenv("GITHUB_WORKSPACE_DIR", "/tmp/github_workspace")
        
        if not self.token:
            raise ValueError("GITHUB_TOKEN not configured")
        if not self.repo:
            raise ValueError("GITHUB_REPO not configured")
        
        # Parse owner and repo name
        parts = self.repo.split("/")
        if len(parts) != 2:
            raise ValueError(f"GITHUB_REPO must be in format 'owner/repo', got: {self.repo}")
        self.owner, self.repo_name = parts
        
        # Create workspace directory if it doesn't exist
        Path(self.workspace_dir).mkdir(parents=True, exist_ok=True)
        
        # Build authenticated repo URL
        self.repo_url = f"https://{self.token}@github.com/{self.owner}/{self.repo_name}.git"
        
        # Local repo path
        self.local_repo_path = Path(self.workspace_dir) / self.repo_name
    
    async def clone_repo(self, branch: Optional[str] = None) -> Dict[str, Any]:
        """Clone the repository to local workspace."""
        
        if self.local_repo_path.exists():
            return {
                "status": "already_exists",
                "path": str(self.local_repo_path),
                "message": f"Repository already exists at {self.local_repo_path}"
            }
        
        branch = branch or self.default_branch
        
        cmd = [
            "git", "clone",
            "--branch", branch,
            "--single-branch",
            self.repo_url,
            str(self.local_repo_path)
        ]
        
        result = await self._run_command(cmd, cwd=self.workspace_dir)
        
        if result["success"]:
            # Configure git user for commits
            await self._run_command(
                ["git", "config", "user.email", "engineering-dept@agent.local"],
                cwd=self.local_repo_path
            )
            await self._run_command(
                ["git", "config", "user.name", "Engineering Department Agent"],
                cwd=self.local_repo_path
            )
        
        return {
            "status": "cloned",
            "path": str(self.local_repo_path),
            "branch": branch,
            **result
        }
    
    async def pull_latest(self, branch: Optional[str] = None) -> Dict[str, Any]:
        """Pull latest changes from remote."""
        
        if not self.local_repo_path.exists():
            return await self.clone_repo(branch)
        
        branch = branch or await self.get_current_branch()
        
        # Fetch latest
        fetch_result = await self._run_command(
            ["git", "fetch", "origin"],
            cwd=self.local_repo_path
        )
        
        if not fetch_result["success"]:
            return fetch_result
        
        # Pull changes
        pull_result = await self._run_command(
            ["git", "pull", "origin", branch],
            cwd=self.local_repo_path
        )
        
        return {
            "status": "pulled",
            "branch": branch,
            **pull_result
        }
    
    async def create_branch(self, branch_name: str, from_branch: Optional[str] = None) -> Dict[str, Any]:
        """Create a new branch."""
        
        if not self.local_repo_path.exists():
            await self.clone_repo()
        
        from_branch = from_branch or self.default_branch
        
        # Checkout base branch first
        await self._run_command(
            ["git", "checkout", from_branch],
            cwd=self.local_repo_path
        )
        
        # Create and checkout new branch
        result = await self._run_command(
            ["git", "checkout", "-b", branch_name],
            cwd=self.local_repo_path
        )
        
        return {
            "status": "branch_created",
            "branch": branch_name,
            "from_branch": from_branch,
            **result
        }
    
    async def commit_changes(
        self,
        message: str,
        files: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Commit changes to the repository."""
        
        if not self.local_repo_path.exists():
            return {
                "success": False,
                "error": "Repository not cloned"
            }
        
        # Add files
        if files:
            for file in files:
                await self._run_command(
                    ["git", "add", file],
                    cwd=self.local_repo_path
                )
        else:
            # Add all changes
            await self._run_command(
                ["git", "add", "-A"],
                cwd=self.local_repo_path
            )
        
        # Check if there are changes to commit
        status_result = await self._run_command(
            ["git", "status", "--porcelain"],
            cwd=self.local_repo_path
        )
        
        if not status_result.get("stdout", "").strip():
            return {
                "success": True,
                "status": "no_changes",
                "message": "No changes to commit"
            }
        
        # Commit
        commit_result = await self._run_command(
            ["git", "commit", "-m", message],
            cwd=self.local_repo_path
        )
        
        # Get commit hash
        if commit_result["success"]:
            hash_result = await self._run_command(
                ["git", "rev-parse", "HEAD"],
                cwd=self.local_repo_path
            )
            commit_hash = hash_result.get("stdout", "").strip()
        else:
            commit_hash = None
        
        return {
            "status": "committed",
            "commit_hash": commit_hash,
            **commit_result
        }
    
    async def push_changes(self, branch: Optional[str] = None) -> Dict[str, Any]:
        """Push changes to remote repository."""
        
        if not self.local_repo_path.exists():
            return {
                "success": False,
                "error": "Repository not cloned"
            }
        
        branch = branch or await self.get_current_branch()
        
        # Push to remote
        result = await self._run_command(
            ["git", "push", "origin", branch],
            cwd=self.local_repo_path
        )
        
        return {
            "status": "pushed",
            "branch": branch,
            **result
        }
    
    async def create_pull_request(
        self,
        title: str,
        body: str,
        head_branch: str,
        base_branch: Optional[str] = None,
        draft: bool = True
    ) -> Dict[str, Any]:
        """Create a pull request via GitHub API."""
        
        base_branch = base_branch or self.default_branch
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.github.com/repos/{self.owner}/{self.repo_name}/pulls",
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Accept": "application/vnd.github.v3+json"
                },
                json={
                    "title": title,
                    "body": body,
                    "head": head_branch,
                    "base": base_branch,
                    "draft": draft
                }
            )
            
            if response.status_code == 201:
                data = response.json()
                return {
                    "success": True,
                    "pr_number": data["number"],
                    "pr_url": data["html_url"],
                    "status": "pr_created"
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to create PR: {response.status_code}",
                    "details": response.text
                }
    
    async def get_current_branch(self) -> str:
        """Get the current branch name."""
        
        result = await self._run_command(
            ["git", "branch", "--show-current"],
            cwd=self.local_repo_path
        )
        
        return result.get("stdout", "").strip() or self.default_branch
    
    async def get_status(self) -> Dict[str, Any]:
        """Get repository status."""
        
        if not self.local_repo_path.exists():
            return {
                "status": "not_cloned",
                "message": "Repository not yet cloned"
            }
        
        # Get branch
        branch = await self.get_current_branch()
        
        # Get status
        status_result = await self._run_command(
            ["git", "status", "--porcelain"],
            cwd=self.local_repo_path
        )
        
        # Get last commit
        log_result = await self._run_command(
            ["git", "log", "-1", "--oneline"],
            cwd=self.local_repo_path
        )
        
        # Parse modified files
        modified_files = []
        if status_result["success"]:
            for line in status_result.get("stdout", "").split("\n"):
                if line.strip():
                    modified_files.append(line.strip())
        
        return {
            "status": "ready",
            "branch": branch,
            "modified_files": modified_files,
            "has_changes": len(modified_files) > 0,
            "last_commit": log_result.get("stdout", "").strip(),
            "repo_path": str(self.local_repo_path)
        }
    
    async def _run_command(self, cmd: List[str], cwd: Optional[Path] = None) -> Dict[str, Any]:
        """Run a git command."""
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )
            
            stdout, stderr = await process.communicate()
            
            return {
                "success": process.returncode == 0,
                "stdout": stdout.decode("utf-8"),
                "stderr": stderr.decode("utf-8"),
                "return_code": process.returncode
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "stdout": "",
                "stderr": ""
            }
    
    async def write_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """Write content to a file in the repository."""
        
        if not self.local_repo_path.exists():
            await self.clone_repo()
        
        full_path = self.local_repo_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            full_path.write_text(content)
            return {
                "success": True,
                "path": str(full_path),
                "status": "file_written"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def read_file(self, file_path: str) -> Dict[str, Any]:
        """Read a file from the repository."""
        
        if not self.local_repo_path.exists():
            await self.clone_repo()
        
        full_path = self.local_repo_path / file_path
        
        try:
            content = full_path.read_text()
            return {
                "success": True,
                "content": content,
                "path": str(full_path)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
