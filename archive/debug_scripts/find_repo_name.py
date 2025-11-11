#!/usr/bin/env python3
"""Find the correct repository name with proper casing."""

import asyncio
import os
import httpx
from dotenv import load_dotenv

load_dotenv(".env.local")


async def find_correct_repo_name():
    """Find the correct repository name with proper casing."""
    
    print("=" * 60)
    print("FINDING CORRECT REPOSITORY NAME")
    print("=" * 60)
    
    token = os.getenv("GITHUB_TOKEN")
    configured_repo = os.getenv("GITHUB_REPO", "")
    
    if not token:
        print("❌ GITHUB_TOKEN not configured")
        return
    
    client = httpx.AsyncClient(
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
        },
        timeout=30.0
    )
    
    # Get authenticated user
    response = await client.get("https://api.github.com/user")
    if response.status_code != 200:
        print("❌ Failed to authenticate")
        await client.aclose()
        return
    
    user_data = response.json()
    username = user_data.get('login')
    print(f"\n✅ Authenticated as: {username}")
    
    # List all repositories (including private)
    print(f"\n📋 Searching for 'engineering' related repositories...")
    
    all_repos = []
    page = 1
    while page <= 5:  # Limit to 5 pages
        response = await client.get(
            "https://api.github.com/user/repos",
            params={
                "type": "all",
                "per_page": 100,
                "page": page,
                "sort": "updated"
            }
        )
        
        if response.status_code != 200:
            break
            
        repos = response.json()
        if not repos:
            break
            
        all_repos.extend(repos)
        page += 1
    
    print(f"Found {len(all_repos)} total repositories")
    
    # Search for engineering department related repos
    engineering_repos = []
    for repo in all_repos:
        name_lower = repo['name'].lower()
        if any(term in name_lower for term in ['engineer', 'eng', 'dept', 'department']):
            engineering_repos.append(repo)
    
    if engineering_repos:
        print(f"\n🎯 Found {len(engineering_repos)} potentially matching repositories:")
        for repo in engineering_repos:
            print(f"\n   Repository: {repo['full_name']}")
            print(f"   - Private: {repo['private']}")
            print(f"   - Has Issues: {repo['has_issues']}")
            print(f"   - Created: {repo['created_at'][:10]}")
            print(f"   - Updated: {repo['updated_at'][:10]}")
            print(f"   - Default Branch: {repo.get('default_branch', 'main')}")
            
            # Check if this matches the configured repo (case-insensitive)
            if configured_repo.lower() == repo['full_name'].lower():
                print(f"   ⚠️  CASE MISMATCH DETECTED!")
                print(f"      Configured: {configured_repo}")
                print(f"      Actual: {repo['full_name']}")
                print(f"\n   📝 Update .env.local:")
                print(f"      GITHUB_REPO={repo['full_name']}")
    else:
        print(f"\n⚠️  No repositories found containing 'engineer' or 'department'")
        print(f"\nShowing all private repositories:")
        private_repos = [r for r in all_repos if r['private']]
        for repo in private_repos[:10]:
            print(f"   - {repo['full_name']}")
    
    # Test the exact configured repo name
    if configured_repo:
        print(f"\n🔍 Testing configured repository: {configured_repo}")
        owner, repo_name = configured_repo.split("/") if "/" in configured_repo else ("", "")
        
        if owner and repo_name:
            # Try different case variations
            variations = [
                f"{owner}/{repo_name}",
                f"{owner.lower()}/{repo_name.lower()}",
                f"{owner}/{repo_name.lower()}",
                f"{owner.lower()}/{repo_name}",
                f"{owner}/{repo_name.capitalize()}",
                f"{owner}/EngineeringDepartment",
                f"{owner}/engineering-department",
                f"{owner}/Engineering-Department"
            ]
            
            for variant in variations:
                response = await client.get(f"https://api.github.com/repos/{variant}")
                if response.status_code == 200:
                    print(f"\n✅ Found working variant: {variant}")
                    repo_data = response.json()
                    print(f"   Correct name: {repo_data['full_name']}")
                    print(f"\n📝 Update .env.local:")
                    print(f"   GITHUB_REPO={repo_data['full_name']}")
                    break
    
    await client.aclose()
    
    print("\n" + "=" * 60)
    print("SEARCH COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(find_correct_repo_name())
