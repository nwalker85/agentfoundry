#!/usr/bin/env python3
"""Test GitHub integration with corrected repository name."""

import asyncio
import os
from dotenv import load_dotenv
from datetime import datetime

# Reload environment with updated repo name
load_dotenv(".env.local", override=True)

from mcp.tools.github import GitHubTool
from mcp.schemas import CreateIssueRequest


async def test_corrected_github():
    """Test GitHub with the corrected repository name."""
    
    print("=" * 60)
    print("TESTING GITHUB WITH CORRECTED REPOSITORY")
    print("=" * 60)
    
    # Verify configuration
    repo = os.getenv("GITHUB_REPO")
    print(f"\n📝 Configuration:")
    print(f"   GITHUB_REPO: {repo}")
    
    if repo != "nwalker85/engineeringdepartment":
        print("⚠️  Warning: Repository not updated yet!")
        print("   Expected: nwalker85/engineeringdepartment")
        print(f"   Current: {repo}")
    
    try:
        github = GitHubTool()
        
        print(f"\n✅ GitHub tool initialized")
        print(f"   Owner: {github.owner}")
        print(f"   Repo: {github.repo_name}")
        print(f"   Default Branch: {github.default_branch}")
        
        # Create a test issue
        print("\n🐛 Creating test issue...")
        
        request = CreateIssueRequest(
            title=f"[TEST] Verify GitHub Integration - {datetime.now().strftime('%Y%m%d-%H%M%S')}",
            body="""## Test Issue

This issue was created to verify the GitHub integration is working correctly.

### Configuration Verified
- ✅ Repository: nwalker85/engineeringdepartment
- ✅ API Token: Working
- ✅ Issue Creation: Successful

### Test Details
- Created by: Engineering Department MCP Server
- Purpose: Integration test
- Can be deleted after verification

---
*This is an automated test issue*""",
            labels=["test", "integration"],
            assignees=[],
            milestone=None,
            story_url=None
        )
        
        response = await github.create_issue(request)
        
        print(f"\n✅ SUCCESS! Issue created:")
        print(f"   Issue Number: #{response.issue_number}")
        print(f"   Issue URL: {response.issue_url}")
        print(f"   Issue ID: {response.issue_id}")
        print(f"   Created At: {response.created_at}")
        
        print("\n🎉 GitHub integration is working!")
        print(f"   You can view the issue at:")
        print(f"   {response.issue_url}")
        
    except Exception as e:
        print(f"\n❌ Failed: {type(e).__name__}")
        print(f"   Error: {str(e)}")
        
        if hasattr(e, 'response'):
            print(f"\n   Response Status: {e.response.status_code}")
            print(f"   Response URL: {e.response.url}")
            
            try:
                error_detail = e.response.json()
                print(f"   Error Details: {error_detail}")
            except:
                print(f"   Response Text: {e.response.text}")
    
    finally:
        if 'github' in locals():
            await github.close()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)


async def test_full_flow():
    """Test the complete Notion -> GitHub flow."""
    
    print("\n" + "=" * 60)
    print("TESTING FULL NOTION -> GITHUB FLOW")
    print("=" * 60)
    
    from mcp.tools.notion import NotionTool
    from mcp.schemas import CreateStoryRequest, Priority
    
    notion = NotionTool()
    github = GitHubTool()
    
    try:
        # Step 1: Create story in Notion
        print("\n1️⃣ Creating story in Notion...")
        
        story_request = CreateStoryRequest(
            epic_title="GitHub Integration Testing",
            story_title=f"Test Story-to-Issue Flow - {datetime.now().strftime('%H%M%S')}",
            priority=Priority.P2,
            description="Testing the complete flow from Notion story to GitHub issue",
            acceptance_criteria=[
                "Story created in Notion",
                "Issue created in GitHub",
                "Links properly connected"
            ]
        )
        
        story_response = await notion.create_story(story_request)
        print(f"   ✅ Story created: {story_response.story_url}")
        
        # Step 2: Create corresponding GitHub issue
        print("\n2️⃣ Creating GitHub issue...")
        
        issue_request = CreateIssueRequest(
            title=f"[{story_request.priority.value}] {story_request.story_title}",
            body=f"""## Story Details

**Notion Story:** {story_response.story_url}
**Epic:** {story_request.epic_title}
**Priority:** {story_request.priority.value}

## Description
{story_request.description}

## Acceptance Criteria
{chr(10).join(f"- [ ] {ac}" for ac in story_request.acceptance_criteria)}

---
Created by Engineering Department automation""",
            labels=[f"priority/{story_request.priority.value}", "source/agent-pm"],
            story_url=story_response.story_url
        )
        
        issue_response = await github.create_issue(issue_request)
        print(f"   ✅ Issue created: {issue_response.issue_url}")
        
        # Step 3: Update Notion story with GitHub URL
        print("\n3️⃣ Updating Notion with GitHub link...")
        
        await notion.update_story_github_url(
            story_response.story_id,
            issue_response.issue_url
        )
        print(f"   ✅ Notion updated with GitHub link")
        
        print("\n🎉 FULL FLOW SUCCESSFUL!")
        print(f"   Notion Story: {story_response.story_url}")
        print(f"   GitHub Issue: {issue_response.issue_url}")
        
    except Exception as e:
        print(f"\n❌ Flow failed: {e}")
    
    finally:
        await notion.close()
        await github.close()


if __name__ == "__main__":
    # Test basic GitHub connection first
    asyncio.run(test_corrected_github())
    
    # Then test full flow
    print("\n" + "=" * 60)
    response = input("Test full Notion->GitHub flow? (y/n): ")
    if response.lower() == 'y':
        asyncio.run(test_full_flow())
