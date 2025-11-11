#!/usr/bin/env python3
"""Quick manual test with full details."""

import asyncio
import httpx

async def test_with_full_details():
    async with httpx.AsyncClient(timeout=90.0) as client:
        message = """Create a story for the Platform Hardening epic.

Story title: Add Health Check Endpoint to API

Description:
Implement a /health endpoint that returns service status, version, and dependency health checks.

Priority: P1

Acceptance Criteria:
- Endpoint returns 200 OK when all dependencies are healthy
- Returns 503 Service Unavailable if any critical dependency is down
- Response includes service version from package.json
- Response includes timestamp and uptime
- Includes health status for database, Redis, and external APIs

Definition of Done:
- Code reviewed and approved by team
- Unit tests with 95% coverage
- Integration tests verify all health check scenarios
- Documentation updated in API docs
- Deployed to staging and verified
"""
        
        print("📝 Sending detailed message to agent...")
        print(f"\nMessage:\n{message}\n")
        
        response = await client.post(
            "http://localhost:8001/api/agent/chat",
            json={"message": message, "session_id": "manual-test"},
            headers={"Authorization": "Bearer dev-token"}
        )
        
        data = response.json()
        
        print("📊 Response:")
        print(f"Status: {data.get('status')}")
        print(f"Error: {data.get('error')}")
        
        if data.get('story_url'):
            print(f"\n🎯 Story: {data['story_url']}")
        if data.get('issue_url'):
            print(f"🎯 Issue: {data['issue_url']}")
        
        print(f"\n💬 Conversation:")
        for i, msg in enumerate(data.get('messages', []), 1):
            msg_type = msg.get('type', 'unknown')
            content = msg.get('content', '')[:200]
            print(f"{i}. {msg_type}: {content}...")

if __name__ == "__main__":
    asyncio.run(test_with_full_details())
