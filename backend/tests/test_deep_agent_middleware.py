"""
Tests for Deep Agent Middleware

Tests TodoList, Filesystem, SubAgent, and Summarization middleware.
"""

import shutil

# Import middleware components
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from middleware.deep_agent_middleware import (
    FilesystemMiddleware,
    SubAgentMiddleware,
    SummarizationMiddleware,
    TodoListMiddleware,
    create_deep_agent_config,
)


class TestTodoListMiddleware:
    """Test TodoList middleware for task planning"""

    def test_write_todos(self):
        """Test writing todos"""
        middleware = TodoListMiddleware()
        tasks = [
            {"id": "task-1", "description": "Research topic", "status": "pending"},
            {"id": "task-2", "description": "Write report", "status": "pending"},
        ]

        result = middleware.write_todos(tasks)

        assert "Created 2 todos" in result
        assert len(middleware.todos) == 2
        assert middleware.todos[0]["id"] == "task-1"

    def test_read_todos(self):
        """Test reading todos"""
        middleware = TodoListMiddleware()
        tasks = [
            {"id": "task-1", "description": "Test task", "status": "pending"},
        ]

        middleware.write_todos(tasks)
        todos = middleware.read_todos()

        assert len(todos) == 1
        assert todos[0]["description"] == "Test task"

    def test_get_tools(self):
        """Test tool registration"""
        middleware = TodoListMiddleware()
        tools = middleware.get_tools()

        assert len(tools) == 2
        tool_names = [t["name"] for t in tools]
        assert "write_todos" in tool_names
        assert "read_todos" in tool_names


class TestFilesystemMiddleware:
    """Test Filesystem middleware for file operations"""

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_write_and_read_file(self, temp_workspace):
        """Test writing and reading files"""
        middleware = FilesystemMiddleware(base_path=temp_workspace)

        # Write file
        content = "Hello, Deep Agents!"
        result = middleware.write_file("test.txt", content)
        assert "Wrote" in result
        assert "test.txt" in result

        # Read file
        read_content = middleware.read_file("test.txt")
        assert read_content == content

    def test_ls(self, temp_workspace):
        """Test listing directory"""
        middleware = FilesystemMiddleware(base_path=temp_workspace)

        # Create some files
        middleware.write_file("file1.txt", "content1")
        middleware.write_file("file2.txt", "content2")

        # List directory
        listing = middleware.ls(".")
        assert "file1.txt" in listing
        assert "file2.txt" in listing

    def test_edit_file(self, temp_workspace):
        """Test editing file content"""
        middleware = FilesystemMiddleware(base_path=temp_workspace)

        # Create file
        middleware.write_file("edit_test.txt", "Hello World")

        # Edit file
        result = middleware.edit_file("edit_test.txt", "World", "Deep Agents")
        assert "Wrote" in result

        # Verify edit
        content = middleware.read_file("edit_test.txt")
        assert content == "Hello Deep Agents"

    def test_glob(self, temp_workspace):
        """Test glob pattern matching"""
        middleware = FilesystemMiddleware(base_path=temp_workspace)

        # Create files
        middleware.write_file("test1.py", "# Python file 1")
        middleware.write_file("test2.py", "# Python file 2")
        middleware.write_file("readme.md", "# Readme")

        # Glob for Python files
        matches = middleware.glob("*.py")
        assert "test1.py" in matches
        assert "test2.py" in matches
        assert "readme.md" not in matches

    def test_grep(self, temp_workspace):
        """Test pattern searching"""
        middleware = FilesystemMiddleware(base_path=temp_workspace)

        # Create file with multiple lines
        content = "line 1: Hello\nline 2: World\nline 3: Hello again"
        middleware.write_file("search.txt", content)

        # Search for pattern
        matches = middleware.grep("Hello", "search.txt")
        assert "line 1" in matches
        assert "line 3" in matches
        assert "line 2" not in matches

    def test_get_tools(self, temp_workspace):
        """Test tool registration"""
        middleware = FilesystemMiddleware(base_path=temp_workspace)
        tools = middleware.get_tools()

        assert len(tools) == 6
        tool_names = [t["name"] for t in tools]
        expected_tools = ["ls", "read_file", "write_file", "edit_file", "glob", "grep"]
        for expected in expected_tools:
            assert expected in tool_names


class TestSubAgentMiddleware:
    """Test SubAgent middleware for delegation"""

    def test_spawn_subagent(self):
        """Test spawning sub-agent"""
        parent_state = {"messages": []}
        middleware = SubAgentMiddleware(parent_state)

        result = middleware.spawn_subagent(
            name="researcher",
            description="Research specialist",
            task="Research deep learning",
            tools=["web_search", "summarize"],
        )

        assert "spawned" in result.lower()
        assert "researcher" in middleware.subagents
        assert middleware.subagents["researcher"]["task"] == "Research deep learning"

    def test_get_subagent_result(self):
        """Test retrieving sub-agent result"""
        parent_state = {"messages": []}
        middleware = SubAgentMiddleware(parent_state)

        middleware.spawn_subagent(name="analyzer", description="Data analyst", task="Analyze dataset", tools=["pandas"])

        result = middleware.get_subagent_result("analyzer")
        assert result is not None
        assert result["description"] == "Data analyst"
        assert result["status"] == "pending"

    def test_get_tools(self):
        """Test tool registration"""
        parent_state = {"messages": []}
        middleware = SubAgentMiddleware(parent_state)
        tools = middleware.get_tools()

        assert len(tools) == 2
        tool_names = [t["name"] for t in tools]
        assert "spawn_subagent" in tool_names
        assert "get_subagent_result" in tool_names


class TestSummarizationMiddleware:
    """Test Summarization middleware for context management"""

    def test_small_content_not_summarized(self):
        """Test that small content is not summarized"""
        middleware = SummarizationMiddleware(size_threshold=1000)

        content = "This is a short message."
        result = middleware.maybe_summarize(content, "key1")

        assert result == content
        assert "key1" not in middleware.offloaded_content

    def test_large_content_summarized(self):
        """Test that large content is summarized"""
        middleware = SummarizationMiddleware(size_threshold=100)

        content = "x" * 500  # Large content
        result = middleware.maybe_summarize(content, "key1")

        # Result should be truncated content plus summary message
        assert "truncated" in result
        assert "key1" in result
        assert "key1" in middleware.offloaded_content
        assert middleware.offloaded_content["key1"] == content

    def test_retrieve_content(self):
        """Test retrieving offloaded content"""
        middleware = SummarizationMiddleware(size_threshold=100)

        content = "x" * 500
        middleware.maybe_summarize(content, "key1")

        retrieved = middleware.retrieve_content("key1")
        assert retrieved == content


class TestCreateDeepAgentConfig:
    """Test deep agent configuration factory"""

    def test_default_config(self):
        """Test creating default config"""
        config = create_deep_agent_config()

        assert config["model"] == "claude-sonnet-4-5-20250929"
        assert len(config["middleware"]) > 0
        assert len(config["tools"]) > 0

    def test_custom_config(self):
        """Test creating custom config"""
        config = create_deep_agent_config(
            model="gpt-4o",
            enable_todos=True,
            enable_filesystem=False,
            enable_subagents=False,
            enable_summarization=False,
        )

        assert config["model"] == "gpt-4o"
        # Should only have TodoList middleware
        assert len(config["middleware"]) == 1
        assert isinstance(config["middleware"][0], TodoListMiddleware)

    def test_all_middleware_enabled(self):
        """Test config with all middleware enabled"""
        config = create_deep_agent_config(
            enable_todos=True,
            enable_filesystem=True,
            enable_subagents=False,  # SubAgent needs runtime state
            enable_summarization=True,
        )

        # Should have TodoList, Filesystem, and Summarization
        assert len(config["middleware"]) == 3

    def test_system_prompt(self):
        """Test custom system prompt"""
        prompt = "You are a research assistant."
        config = create_deep_agent_config(system_prompt=prompt)

        assert config["system_prompt"] == prompt


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
