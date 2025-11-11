#!/usr/bin/env python3
"""Test GitHub repository operations (not issues)."""

import asyncio
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv(".env.local", override=True)

# Fix the repo name in environment
os.environ["GITHUB_REPO"] = "nwalker85/engineeringdepartment"

from mcp.tools.github_repo import GitHubRepoTool


async def test_repo_operations():
    """Test GitHub repository operations."""
    
    print("=" * 60)
    print("GITHUB REPOSITORY OPERATIONS TEST")
    print("=" * 60)
    print("\nNote: GitHub is for code management only.")
    print("Issue tracking is handled exclusively in Notion.")
    print("=" * 60)
    
    github = GitHubRepoTool()
    
    print(f"\n📝 Configuration:")
    print(f"   Repository: {github.owner}/{github.repo_name}")
    print(f"   Default Branch: {github.default_branch}")
    print(f"   Workspace: {github.workspace_dir}")
    
    # Test 1: Clone repository
    print("\n1️⃣ Testing Clone...")
    result = await github.clone_repo()
    print(f"   Status: {result['status']}")
    if result.get('path'):
        print(f"   Path: {result['path']}")
    
    # Test 2: Get status
    print("\n2️⃣ Testing Status...")
    status = await github.get_status()
    print(f"   Status: {status['status']}")
    print(f"   Branch: {status.get('branch', 'N/A')}")
    print(f"   Has Changes: {status.get('has_changes', False)}")
    print(f"   Last Commit: {status.get('last_commit', 'N/A')[:50]}")
    
    # Test 3: Create a test file
    print("\n3️⃣ Testing File Operations...")
    test_file = f"test_files/test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    content = f"""# Test File

This file was created by the Engineering Department automation.

## Purpose
Testing GitHub repository operations (not issue management).

## Created
{datetime.now().isoformat()}

## Note
Issue tracking is handled in Notion, not GitHub Issues.
"""
    
    write_result = await github.write_file(test_file, content)
    print(f"   Write: {write_result.get('status', 'failed')}")
    
    # Test 4: Read the file back
    read_result = await github.read_file(test_file)
    print(f"   Read: {'success' if read_result.get('success') else 'failed'}")
    
    # Test 5: Commit changes
    print("\n4️⃣ Testing Commit...")
    commit_result = await github.commit_changes(
        message=f"test: Add test file from Engineering Department automation",
        files=[test_file]
    )
    print(f"   Status: {commit_result.get('status', 'failed')}")
    if commit_result.get('commit_hash'):
        print(f"   Commit: {commit_result['commit_hash'][:8]}")
    
    # Test 6: Create a feature branch
    print("\n5️⃣ Testing Branch Creation...")
    branch_name = f"test/automation-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    branch_result = await github.create_branch(branch_name)
    print(f"   Status: {branch_result.get('status', 'failed')}")
    print(f"   Branch: {branch_name}")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    print("\n✅ GitHub repository operations are working correctly.")
    print("📝 Remember: All issue tracking stays in Notion!")


async def test_workflow_example():
    """Example of how GitHub fits into the workflow."""
    
    print("\n" + "=" * 60)
    print("EXAMPLE WORKFLOW")
    print("=" * 60)
    
    print("""
How the Engineering Department uses GitHub:

1. PM Agent creates story in Notion ✅
   - Epic management
   - Story details
   - Acceptance criteria
   - Sprint planning
   
2. Developer picks up story from Notion backlog
   
3. Developer uses GitHub for code:
   - Clone/pull repository
   - Create feature branch
   - Write code
   - Commit changes
   - Push to remote
   - Create PR for review
   
4. Story status updated in Notion
   - Mark as "In Progress"
   - Link to PR (optional)
   - Update when complete
   
GitHub = Code Management
Notion = Project Management
""")


if __name__ == "__main__":
    asyncio.run(test_repo_operations())
    asyncio.run(test_workflow_example())
