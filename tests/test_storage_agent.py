"""
Test Storage Agent
Verifies storage operations work correctly.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.storage_agent import invoke_storage_agent


async def test_storage_workflow():
    """Test complete storage workflow"""

    print("=" * 80)
    print("TESTING STORAGE AGENT")
    print("=" * 80)

    # Test 1: Save draft
    print("\n[TEST 1] Saving draft...")
    result = await invoke_storage_agent(
        action="save_draft",
        agent_id="test-workflow-agent",
        user_id="test-user",
        graph_data={
            "nodes": [
                {"id": "n1", "type": "entry", "data": {"label": "Start", "function": "start_node"}},
                {"id": "n2", "type": "process", "data": {"label": "Process", "function": "process_node"}},
                {"id": "n3", "type": "end", "data": {"label": "End", "function": "end_node"}},
            ],
            "edges": [
                {"id": "e1", "source": "n1", "target": "n2", "type": "default"},
                {"id": "e2", "source": "n2", "target": "n3", "type": "default"},
            ],
            "metadata": {"created": "2025-11-17"}
        }
    )
    print(f"✅ Save draft: {result}")

    # Test 2: Get draft back
    print("\n[TEST 2] Retrieving draft...")
    result = await invoke_storage_agent(
        action="get_draft",
        agent_id="test-workflow-agent"
    )
    print(f"✅ Get draft: {result['result'] is not None}")

    # Test 3: Commit version
    print("\n[TEST 3] Committing version...")
    result = await invoke_storage_agent(
        action="commit_version",
        agent_id="test-workflow-agent",
        user_id="test-user",
        graph_data={
            "nodes": [
                {"id": "n1", "type": "entry", "data": {"label": "Start"}},
                {"id": "n2", "type": "process", "data": {"label": "Updated Process"}},
                {"id": "n3", "type": "end", "data": {"label": "End"}},
            ],
            "edges": [
                {"id": "e1", "source": "n1", "target": "n2"},
                {"id": "e2", "source": "n2", "target": "n3"},
            ]
        },
        commit_message="Initial commit - basic workflow"
    )
    print(f"✅ Commit version: {result}")

    # Test 4: Commit another version
    print("\n[TEST 4] Committing second version...")
    result = await invoke_storage_agent(
        action="commit_version",
        agent_id="test-workflow-agent",
        user_id="test-user",
        graph_data={
            "nodes": [
                {"id": "n1", "type": "entry", "data": {"label": "Start"}},
                {"id": "n2", "type": "process", "data": {"label": "Updated Process"}},
                {"id": "n3", "type": "decision", "data": {"label": "Decision"}},
                {"id": "n4", "type": "end", "data": {"label": "End"}},
            ],
            "edges": [
                {"id": "e1", "source": "n1", "target": "n2"},
                {"id": "e2", "source": "n2", "target": "n3"},
                {"id": "e3", "source": "n3", "target": "n4", "type": "conditional", "data": {"condition": "success"}},
            ]
        },
        commit_message="Added decision node"
    )
    print(f"✅ Commit second version: {result}")

    # Test 5: Get history
    print("\n[TEST 5] Getting version history...")
    result = await invoke_storage_agent(
        action="get_history",
        agent_id="test-workflow-agent"
    )
    print(f"✅ Version history ({len(result['result'])} versions):")
    for version in result['result']:
        print(f"   - v{version['version']}: {version['commit_message']} ({version['commit_hash']})")

    # Test 6: Restore to version 1
    print("\n[TEST 6] Restoring to version 1...")
    result = await invoke_storage_agent(
        action="restore_version",
        agent_id="test-workflow-agent",
        version=1
    )
    if result['success']:
        restored = result['result']
        print(f"✅ Restored to version {restored['version']} (hash: {restored['commit_hash']})")
        print(f"   Nodes count: {len(restored['graph_data']['nodes'])}")
    else:
        print(f"❌ Restore failed: {result['error']}")

    # Test 7: Export to Python
    print("\n[TEST 7] Exporting to Python...")
    result = await invoke_storage_agent(
        action="export_python",
        graph_data={
            "nodes": [
                {"id": "n1", "type": "entry", "data": {"label": "start", "function": "start_node"}},
                {"id": "n2", "type": "process", "data": {"label": "process", "function": "process_data"}},
                {"id": "n3", "type": "end", "data": {"label": "end", "function": "finish"}},
            ],
            "edges": [
                {"id": "e1", "source": "n1", "target": "n2"},
                {"id": "e2", "source": "n2", "target": "n3"},
            ]
        },
        agent_name="test_agent"
    )
    print(f"✅ Python code generated:")
    print("-" * 80)
    print(result['result'][:500] + "..." if len(result['result']) > 500 else result['result'])
    print("-" * 80)

    # Test 8: Import Python code
    print("\n[TEST 8] Importing Python code...")
    python_code = """
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class MyState(TypedDict):
    input: str
    output: str

def node_a(state):
    return state

def node_b(state):
    return state

builder = StateGraph(MyState)
builder.add_node("start", node_a)
builder.add_node("process", node_b)
builder.add_edge(START, "start")
builder.add_edge("start", "process")
builder.add_edge("process", END)
graph = builder.compile()
"""
    result = await invoke_storage_agent(
        action="import_python",
        python_code=python_code
    )
    if result['success']:
        imported = result['result']
        print(f"✅ Imported graph:")
        print(f"   Nodes: {len(imported.get('nodes', []))}")
        print(f"   Edges: {len(imported.get('edges', []))}")
    else:
        print(f"❌ Import failed: {result['error']}")

    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_storage_workflow())
