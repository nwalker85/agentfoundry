#!/usr/bin/env python3
"""Test creating a GitHub issue with detailed error capture."""

import asyncio
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv(".env.local")

from mcp.tools.github import GitHubTool
from mcp.schemas import CreateIssueRequest


async def test_github_issue_creation():
    """Test creating a GitHub issue."""
    
    print("=" * 60)
    print("TESTING GITHUB ISSUE CREATION")
    print("=" * 60)
    
    try:
        github = GitHubTool()
        
        print(f"\n📝 Configuration:")
        print(f"   Repository: {github.owner}/{github.repo_name}")
        print(f"   Default Branch: {github.default_branch}")
        
        # Create a test issue
        print("\n🐛 Creating test issue...")
        
        request = CreateIssueRequest(
            title=f"[TEST] Debug Issue - {datetime.now().strftime('%H%M%S')}",
            body="This is a test issue created to debug GitHub integration.\n\n## Test Details\n- Created by: test_github_issue.py\n- Purpose: Verify GitHub API access\n- Can be deleted",
            labels=["test", "debug"],
            assignees=[],
            milestone=None,
            story_url="https://notion.so/test-story"
        )
        
        print(f"   Title: {request.title}")
        print(f"   Labels: {request.labels}")
        
        response = await github.create_issue(request)
        
        print(f"\n✅ Issue created successfully!")
        print(f"   Issue Number: #{response.issue_number}")
        print(f"   Issue URL: {response.issue_url}")
        print(f"   Issue ID: {response.issue_id}")
        
    except Exception as e:
        print(f"\n❌ Failed to create issue: {type(e).__name__}")
        print(f"   Error: {str(e)}")
        
        if hasattr(e, 'response'):
            print(f"\n   Response Status: {e.response.status_code}")
            print(f"   Response URL: {e.response.url}")
            
            try:
                error_detail = e.response.json()
                print(f"   Error Details:")
                if isinstance(error_detail, dict):
                    for key, value in error_detail.items():
                        print(f"     {key}: {value}")
                else:
                    print(f"     {error_detail}")
            except:
                print(f"   Response Text: {e.response.text}")
        
        # Additional debugging
        print(f"\n🔍 Debugging Information:")
        print(f"   GITHUB_TOKEN set: {bool(os.getenv('GITHUB_TOKEN'))}")
        print(f"   GITHUB_REPO: {os.getenv('GITHUB_REPO')}")
        
        if "404" in str(e):
            print(f"\n⚠️  404 Error - Possible causes:")
            print(f"   1. Repository doesn't exist")
            print(f"   2. Repository is private and token lacks 'repo' scope")
            print(f"   3. Repository name/owner is incorrect")
            print(f"   4. Issues are disabled for this repository")
    
    finally:
        if 'github' in locals():
            await github.close()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_github_issue_creation())
