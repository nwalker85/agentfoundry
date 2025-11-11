#!/usr/bin/env python3
"""Test GitHub API access for private repository."""

import asyncio
import os
import httpx
from dotenv import load_dotenv

load_dotenv(".env.local")


async def test_private_repo_access():
    """Test access to private GitHub repository."""
    
    print("=" * 60)
    print("GITHUB PRIVATE REPOSITORY DIAGNOSTIC")
    print("=" * 60)
    
    token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPO")
    
    if not token:
        print("❌ GITHUB_TOKEN not configured")
        return
    
    if not repo:
        print("❌ GITHUB_REPO not configured")
        return
    
    print(f"\n📝 Configuration:")
    print(f"   Token: {token[:20]}...{token[-4:]}")
    print(f"   Repo: {repo}")
    
    # Parse owner and repo
    parts = repo.split("/")
    if len(parts) != 2:
        print(f"❌ Invalid repo format: {repo}")
        return
    
    owner, repo_name = parts
    print(f"   Owner: {owner}")
    print(f"   Repo Name: {repo_name}")
    
    client = httpx.AsyncClient(
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        },
        timeout=30.0
    )
    
    # Test 1: Check token validity and scopes
    print("\n🔐 Testing Token Permissions...")
    response = await client.get("https://api.github.com/user")
    if response.status_code == 200:
        user_data = response.json()
        print(f"✅ Token valid - Authenticated as: {user_data.get('login')}")
        
        # Check token scopes
        scopes = response.headers.get("X-OAuth-Scopes", "")
        print(f"   Token scopes: {scopes}")
        
        if "repo" not in scopes:
            print("⚠️  WARNING: Token doesn't have 'repo' scope - needed for private repos!")
            print("   To fix: Create a new token with 'repo' scope at:")
            print("   https://github.com/settings/tokens")
    else:
        print(f"❌ Token invalid: {response.status_code}")
        print(f"   Response: {response.text}")
        await client.aclose()
        return
    
    # Test 2: Check repository access (including private)
    print(f"\n📚 Testing Private Repository Access...")
    response = await client.get(f"https://api.github.com/repos/{owner}/{repo_name}")
    
    if response.status_code == 200:
        repo_data = response.json()
        print(f"✅ Repository accessible!")
        print(f"   Full Name: {repo_data.get('full_name')}")
        print(f"   Private: {repo_data.get('private')}")
        print(f"   Default Branch: {repo_data.get('default_branch')}")
        print(f"   Has Issues: {repo_data.get('has_issues')}")
        print(f"   Has Projects: {repo_data.get('has_projects')}")
        print(f"   Created: {repo_data.get('created_at')}")
        
        # Check permissions
        permissions = repo_data.get('permissions', {})
        print(f"   Your Permissions:")
        print(f"     - Admin: {permissions.get('admin', False)}")
        print(f"     - Push: {permissions.get('push', False)}")
        print(f"     - Pull: {permissions.get('pull', False)}")
        
    elif response.status_code == 404:
        print(f"❌ Repository not found or no access: {owner}/{repo_name}")
        print("\nDiagnosing the issue...")
        
        # Check if we can list user's private repos
        print(f"\n📋 Checking your private repositories...")
        response = await client.get(
            "https://api.github.com/user/repos",
            params={"type": "all", "per_page": 100}
        )
        
        if response.status_code == 200:
            my_repos = response.json()
            private_repos = [r for r in my_repos if r['private']]
            print(f"Found {len(private_repos)} private repositories you have access to:")
            
            # Look for exact match or similar names
            exact_match = None
            similar = []
            for r in private_repos:
                if r['name'].lower() == repo_name.lower():
                    exact_match = r
                elif repo_name.lower() in r['name'].lower() or r['name'].lower() in repo_name.lower():
                    similar.append(r)
            
            if exact_match:
                print(f"\n✅ Found exact match with different owner!")
                print(f"   Repository: {exact_match['full_name']}")
                print(f"   Update .env.local with:")
                print(f"   GITHUB_REPO={exact_match['full_name']}")
            elif similar:
                print(f"\nFound similar private repositories:")
                for r in similar[:5]:
                    print(f"   - {r['full_name']}")
                print(f"\nUpdate .env.local with the correct repository name")
            else:
                print(f"\nNo repository named '{repo_name}' found")
                print(f"Showing first 5 private repos:")
                for r in private_repos[:5]:
                    print(f"   - {r['full_name']}")
    else:
        print(f"❌ Unexpected error: {response.status_code}")
        print(f"   Response: {response.text}")
    
    # Test 3: Check issues API access
    print(f"\n🐛 Testing Issues API...")
    response = await client.get(
        f"https://api.github.com/repos/{owner}/{repo_name}/issues",
        params={"state": "all", "per_page": 5}
    )
    
    if response.status_code == 200:
        issues = response.json()
        print(f"✅ Issues API accessible")
        print(f"   Found {len(issues)} recent issues")
        if issues:
            print(f"   Latest issue: {issues[0].get('title', 'No title')}")
    elif response.status_code == 404:
        print(f"❌ Issues API not accessible (404)")
        print("   This means either:")
        print("   1. The repository doesn't exist")
        print("   2. The repository exists but you don't have access")
        print("   3. Issues are disabled for this repository")
    elif response.status_code == 401:
        print(f"❌ Authentication failed - token may be expired or invalid")
    else:
        print(f"❌ Issues API error: {response.status_code}")
    
    await client.aclose()
    
    print("\n" + "=" * 60)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 60)
    
    # Provide recommendations
    print("\n💡 RECOMMENDATIONS:")
    print("-" * 40)
    
    if response.status_code == 404:
        print("\nTo fix the 404 error:")
        print("1. Verify the repository name in your GitHub account")
        print("2. Ensure your token has 'repo' scope for private repository access")
        print("3. Check if the repository owner is correct")
        print("4. Update GITHUB_REPO in .env.local with the correct value")


if __name__ == "__main__":
    asyncio.run(test_private_repo_access())
