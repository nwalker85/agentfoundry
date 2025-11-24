"""
Quick test script to verify agent deployment pipeline works.

Run this to test the full flow:
1. Generate Python from graph
2. Deploy agent (save files)
3. Verify files created
4. Invoke agent via Supervisor

Usage:
    python test_deployment.py
"""

import asyncio
from pathlib import Path

import httpx

# Test graph data (simple 3-node agent)
TEST_GRAPH = {
    "nodes": [
        {"id": "entry-1", "type": "entryPoint", "data": {"label": "Start"}, "position": {"x": 100, "y": 100}},
        {
            "id": "process-1",
            "type": "process",
            "data": {
                "label": "CIBC Greeter",
                "description": "Greet CIBC customers",
                "model": "gpt-4o-mini",
                "temperature": 0.7,
            },
            "position": {"x": 300, "y": 100},
        },
        {"id": "end-1", "type": "end", "data": {"label": "End"}, "position": {"x": 500, "y": 100}},
    ],
    "edges": [
        {"id": "e1", "source": "entry-1", "target": "process-1", "animated": True},
        {"id": "e2", "source": "process-1", "target": "end-1", "animated": True},
    ],
}


async def test_deployment():
    """Test the deployment pipeline."""

    print("🧪 Testing Agent Deployment Pipeline\n")
    print("=" * 60)

    # 1. Create test graph in database
    print("\n1️⃣  Creating test graph in database...")

    async with httpx.AsyncClient() as client:
        graph_data = {
            "metadata": {
                "id": "cibc-test-agent",
                "name": "CIBC Test Agent",
                "type": "user",
                "description": "Test agent for CIBC demo",
                "tags": ["test", "cibc", "demo"],
                "organization_id": "cibc",
                "domain_id": "card-services",
            },
            "spec": {"graph": TEST_GRAPH},
        }

        try:
            response = await client.post("http://localhost:8000/api/graphs", json=graph_data)

            if response.status_code == 200:
                print("   ✅ Graph created successfully")
                graph_id = response.json().get("id") or "cibc-test-agent"
            else:
                print(f"   ❌ Failed to create graph: {response.status_code}")
                print(f"      {response.text}")
                return

        except Exception as e:
            print(f"   ❌ Error creating graph: {e}")
            return

    # 2. Deploy the agent
    print(f"\n2️⃣  Deploying agent: {graph_id}...")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"http://localhost:8000/api/graphs/{graph_id}/deploy")

            if response.status_code == 200:
                result = response.json()
                print("   ✅ Agent deployed successfully!")
                print(f"      Python file: {result.get('files', {}).get('python')}")
                print(f"      YAML file: {result.get('files', {}).get('yaml')}")
            else:
                print(f"   ❌ Deployment failed: {response.status_code}")
                print(f"      {response.text}")
                return

        except Exception as e:
            print(f"   ❌ Error deploying agent: {e}")
            return

    # 3. Verify files exist
    print("\n3️⃣  Verifying files created...")

    agents_dir = Path(__file__).parent / "agents"
    python_file = agents_dir / "cibc-test-agent.py"
    yaml_file = agents_dir / "cibc-test-agent.agent.yaml"

    if python_file.exists():
        print(f"   ✅ Python file exists: {python_file}")
        print(f"      Size: {python_file.stat().st_size} bytes")
    else:
        print(f"   ❌ Python file not found: {python_file}")

    if yaml_file.exists():
        print(f"   ✅ YAML file exists: {yaml_file}")
        print(f"      Size: {yaml_file.stat().st_size} bytes")
    else:
        print(f"   ❌ YAML file not found: {yaml_file}")

    # 4. Wait for backend to restart (Watchfiles triggers uvicorn reload)
    print("\n4️⃣  Waiting for backend to restart after file change...")

    # Wait up to 30 seconds for backend to be healthy
    for i in range(30):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:8000/health", timeout=2.0)
                if response.status_code == 200:
                    print(f"   ✅ Backend healthy after {i + 1} seconds")
                    break
        except:
            pass
        await asyncio.sleep(1)
    else:
        print("   ⚠️  Backend may still be restarting, but continuing...")

    # 5. Invoke the agent via Supervisor
    print("\n5️⃣  Invoking agent via Supervisor...")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://localhost:8000/api/agent/invoke",
                json={
                    "agent_id": "cibc-test-agent",
                    "input": "Hello! I need help with my CIBC card.",
                    "session_id": "test-session-123",
                    "route_via_supervisor": True,
                },
            )

            if response.status_code == 200:
                result = response.json()
                print("   ✅ Agent invoked successfully!")
                print(f"      Agent: {result.get('agent_id')}")
                print(f"      Response: {result.get('output')[:200]}...")
            else:
                print(f"   ❌ Invocation failed: {response.status_code}")
                print(f"      {response.text}")

        except Exception as e:
            print(f"   ❌ Error invoking agent: {e}")

    print("\n" + "=" * 60)
    print("🎉 Test complete!")
    print("\nNext steps:")
    print("  1. Check Docker logs: docker-compose logs -f foundry-backend")
    print("  2. Open Forge UI: http://localhost:3000/app/forge")
    print("  3. Deploy agents from UI and test voice sessions")
    print("\n💤 Now go sleep for 2-3 hours before your demo!")


if __name__ == "__main__":
    asyncio.run(test_deployment())
