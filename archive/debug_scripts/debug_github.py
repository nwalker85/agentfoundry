#!/usr/bin/env python3
"""Debug GitHub API access and configuration."""

import asyncio
import os
import httpx
from dotenv import load_dotenv

load_dotenv(".env.local")


async def test_github_access():
    """Test GitHub API access and configuration."""
    
    print("=" * 60)
    print("GITHUB API DIAGNOSTIC")
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
    print(f"   Token: {token[:20]}...")
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
        }
    )
    
    # Test 1: Check token validity
    print("\n🔐 Testing Token...")
    response = await client.get("https://api.github.com/user")
    if response.status_code == 200:
        user_data = response.json()
        print(f"✅ Token valid - Authenticated as: {user_data.get('login')}")
    else:
        print(f"❌ Token invalid: {response.status_code}")
        print(f"   Response: {response.text}")
        await client.aclose()
        return
    
    # Test 2: Check repository access
    print(f"\n📚 Testing Repository Access...")
    response = await client.get(f"https://api.github.com/repos/{owner}/{repo_name}")
    if response.status_code == 200:
        repo_data = response.json()
        print(f"✅ Repository found!")
        print(f"   Name: {repo_data.get('full_name')}")
        print(f"   Private: {repo_data.get('private')}")
        print(f"   Default Branch: {repo_data.get('default_branch')}")
        print(f"   Issues Enabled: {repo_data.get('has_issues')}")
    elif response.status_code == 404:
        print(f"❌ Repository not found or no access: {owner}/{repo_name}")
        print("\nPossible issues:")
        print("1. Repository doesn't exist")
        print("2. Repository is private and token doesn't have access")
        print("3. Repository name is misspelled")
        
        # Try to list user's repos
        print(f"\n📋 Listing repositories for {owner}...")
        response = await client.get(f"https://api.github.com/users/{owner}/repos")
        if response.status_code == 200:
            repos = response.json()
            print(f"Found {len(repos)} public repositories:")
            for r in repos[:5]:
                print(f"   - {r['name']}")
            
            # Also check authenticated user's repos
            print(f"\n📋 Listing your accessible repositories...")
            response = await client.get("https://api.github.com/user/repos", params={"per_page": 100})
            if response.status_code == 200:
                my_repos = response.json()
                matching = [r for r in my_repos if repo_name.lower() in r['name'].lower()]
                if matching:
                    print(f"Found similar repositories you have access to:")
                    for r in matching:
                        print(f"   - {r['full_name']} (private: {r['private']})")
                else:
                    print(f"No repositories matching '{repo_name}' found in your accessible repos")
    else:
        print(f"❌ Unexpected error: {response.status_code}")
        print(f"   Response: {response.text}")
    
    # Test 3: Check issues API
    print(f"\n🐛 Testing Issues API...")
    response = await client.get(f"https://api.github.com/repos/{owner}/{repo_name}/issues")
    if response.status_code == 200:
        issues = response.json()
        print(f"✅ Issues API accessible - Found {len(issues)} issues")
    elif response.status_code == 404:
        print(f"❌ Issues API not accessible (404)")
    else:
        print(f"❌ Issues API error: {response.status_code}")
        print(f"   Response: {response.text}")
    
    # Test 4: Test creating an issue (dry run)
    print(f"\n📝 Testing Issue Creation (dry run)...")
    test_issue = {
        "title": "[TEST] Debug Issue - Can be deleted",
        "body": "This is a test issue created by the Engineering Department debug script.\n\nPlease delete this issue.",
        "labels": ["test", "debug"]
    }
    
    print(f"Would create issue with:")
    print(f"   Title: {test_issue['title']}")
    print(f"   Labels: {test_issue['labels']}")
    print(f"   URL: https://api.github.com/repos/{owner}/{repo_name}/issues")
    
    await client.aclose()
    
    print("\n" + "=" * 60)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 60)


async def suggest_fixes():
    """Suggest fixes based on the diagnostic."""
    
    print("\n💡 SUGGESTED FIXES:")
    print("-" * 40)
    
    repo = os.getenv("GITHUB_REPO", "")
    
    print("\n1. Check if the repository exists:")
    print(f"   https://github.com/{repo}")
    
    print("\n2. If the repo is private, ensure the token has 'repo' scope:")
    print("   Go to: https://github.com/settings/tokens")
    print("   Check that your token has the 'repo' checkbox checked")
    
    print("\n3. Common repository names to try:")
    if "/" in repo:
        owner, name = repo.split("/")
        suggestions = [
            f"{owner}/engineering-department",
            f"{owner}/Engineering-Department", 
            f"{owner}/engineeringdept",
            f"{owner}/eng-dept"
        ]
        for s in suggestions:
            print(f"   - {s}")
    
    print("\n4. Create the repository if it doesn't exist:")
    print("   gh repo create nwalker/engineeringdepartment --private")


if __name__ == "__main__":
    asyncio.run(test_github_access())
    asyncio.run(suggest_fixes())
