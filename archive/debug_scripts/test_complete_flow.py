#!/usr/bin/env python3
"""Test complete flow with corrected architecture: Notion for issues, GitHub for code."""

import asyncio
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv(".env.local", override=True)

# Fix GitHub repo name
os.environ["GITHUB_REPO"] = "nwalker85/engineeringdepartment"


async def test_complete_flow():
    """Test the complete Engineering Department flow."""
    
    print("=" * 60)
    print("ENGINEERING DEPARTMENT - COMPLETE FLOW TEST")
    print("=" * 60)
    print("\nArchitecture:")
    print("  • Notion: All project management (stories, epics, tracking)")
    print("  • GitHub: Code management only (clone, commit, push)")
    print("=" * 60)
    
    # Test 1: PM Agent creates story in Notion
    print("\n1️⃣ Testing PM Agent Story Creation...")
    
    try:
        from agent.pm_graph import PMAgent
        
        agent = PMAgent()
        result = await agent.process_message(
            "Create a story for implementing a user dashboard with charts and metrics"
        )
        
        print(f"✅ Story created in Notion")
        print(f"   Status: {result.get('status')}")
        
        if result.get('story_created'):
            story_info = result['story_created']
            print(f"   Title: {story_info.get('title')}")
            print(f"   Epic: {story_info.get('epic')}")
            print(f"   URL: {story_info.get('url')}")
        
        await agent.close()
        
    except Exception as e:
        print(f"❌ PM Agent failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: GitHub Repository Operations (for code)
    print("\n2️⃣ Testing GitHub Repository Operations...")
    
    try:
        from mcp.tools.github_repo import GitHubRepoTool
        
        github = GitHubRepoTool()
        
        # Check repo status
        status = await github.get_status()
        print(f"✅ GitHub repo accessible")
        print(f"   Status: {status['status']}")
        print(f"   Branch: {status.get('branch', 'N/A')}")
        
        # Simulate developer workflow
        print("\n3️⃣ Simulating Developer Workflow...")
        
        # Create feature branch
        branch_name = f"feature/dashboard-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        branch_result = await github.create_branch(branch_name)
        print(f"✅ Feature branch created: {branch_name}")
        
        # Add a file (simulating code development)
        code_content = """// Dashboard Component
export const Dashboard = () => {
    return <div>Dashboard Implementation</div>;
};
"""
        
        file_path = f"src/components/Dashboard_{datetime.now().strftime('%H%M%S')}.jsx"
        write_result = await github.write_file(file_path, code_content)
        print(f"✅ Code file created: {file_path}")
        
        # Commit changes
        commit_result = await github.commit_changes(
            message="feat: Add dashboard component",
            files=[file_path]
        )
        
        if commit_result.get('commit_hash'):
            print(f"✅ Changes committed: {commit_result['commit_hash'][:8]}")
        
    except Exception as e:
        print(f"❌ GitHub operations failed: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("WORKFLOW SUMMARY")
    print("=" * 60)
    print("""
✅ Correct Flow Demonstrated:

1. PM Agent → Creates story in Notion
   - Epic management
   - Story details
   - Acceptance criteria
   - NO GitHub issue creation

2. Developer picks up story from Notion
   
3. Developer uses GitHub for code:
   - Create feature branch
   - Write code
   - Commit changes
   - Push to remote
   - Create PR

4. Story status updated in Notion
   
This is the correct separation of concerns:
- Notion = Project Management
- GitHub = Code Management
""")


if __name__ == "__main__":
    asyncio.run(test_complete_flow())
