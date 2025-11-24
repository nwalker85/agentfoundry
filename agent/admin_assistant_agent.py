"""Admin Assistant Agent for Agent Foundry.

Helps Forge / platform designers by:
- Answering questions about organizations/domains/instances/deployments
- Explaining what agents are available and their status
- Answering questions about deployment, architecture, and platform docs

Implements a LangGraph ReAct-style agent with a DataAgent-backed tool.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from agent.data_agent import DataAgent

# Docs directory relative to the project root
DOCS_DIR = Path(__file__).parent.parent / "docs"


class AdminAssistantAgent:
    """LangGraph-based admin assistant for the Agent Foundry control plane."""

    def __init__(self) -> None:
        # LLM used for reasoning and responses
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
        )

        # DataAgent for structured DB access
        self.data_agent = DataAgent()

        # Tools exposed to the agent
        self.tools = [
            self._control_plane_query_tool(),
            self._list_docs_tool(),
            self._read_doc_tool(),
            self._search_docs_tool(),
        ]

        self.graph = self._build_agent()

    # ------------------------------------------------------------------ Tools
    def _control_plane_query_tool(self):
        """Tool for querying control-plane data via DataAgent."""

        @tool
        async def control_plane_query(question: str) -> dict[str, Any]:
            """Query control-plane data (organizations, domains, instances, deployments).

            Args:
                question: Natural language question about orgs/domains/instances/deployments.

            Returns:
                JSON with `sql`, `rows`, and optional `error`.
            """

            state = await self.data_agent.query(question)
            return {
                "sql": state.get("sql"),
                "rows": state.get("rows", []),
                "error": state.get("error"),
            }

        return control_plane_query

    def _list_docs_tool(self):
        """Tool for listing available documentation files."""

        @tool
        def list_docs(subdirectory: str = "") -> dict[str, Any]:
            """List available documentation files in the docs folder.

            Args:
                subdirectory: Optional subdirectory to list (e.g., 'architecture', 'reference').
                             Leave empty for root docs folder.

            Returns:
                JSON with `files` list and `directories` list.
            """
            target_dir = DOCS_DIR / subdirectory if subdirectory else DOCS_DIR

            if not target_dir.exists():
                return {"error": f"Directory not found: {subdirectory}", "files": [], "directories": []}

            files = []
            directories = []

            for item in sorted(target_dir.iterdir()):
                if item.is_dir() and not item.name.startswith('.'):
                    directories.append(item.name)
                elif item.is_file() and item.suffix == '.md':
                    files.append(item.name)

            return {"files": files, "directories": directories, "path": str(subdirectory or "/")}

        return list_docs

    def _read_doc_tool(self):
        """Tool for reading a specific documentation file."""

        @tool
        def read_doc(filename: str) -> dict[str, Any]:
            """Read the contents of a documentation file.

            Args:
                filename: The filename to read (e.g., 'DEPLOYMENT.md' or 'architecture/PLATFORM_DEEPDIVE.md').

            Returns:
                JSON with `content` string or `error` message.
            """
            # Security: prevent path traversal
            clean_path = filename.replace('..', '').lstrip('/')
            target_file = DOCS_DIR / clean_path

            if not target_file.exists():
                return {"error": f"File not found: {filename}"}

            if not target_file.suffix == '.md':
                return {"error": "Only .md files can be read"}

            try:
                content = target_file.read_text(encoding='utf-8')
                # Truncate very large files
                if len(content) > 50000:
                    content = content[:50000] + "\n\n... [truncated - file too large]"
                return {"content": content, "filename": filename}
            except Exception as e:
                return {"error": f"Failed to read file: {e}"}

        return read_doc

    def _search_docs_tool(self):
        """Tool for searching across all documentation files."""

        @tool
        def search_docs(query: str) -> dict[str, Any]:
            """Search for a term across all documentation files.

            Args:
                query: The search term (case-insensitive).

            Returns:
                JSON with `results` list of matching files and snippets.
            """
            query_lower = query.lower()
            results = []

            def search_dir(directory: Path, prefix: str = ""):
                for item in directory.iterdir():
                    if item.is_dir() and not item.name.startswith('.'):
                        search_dir(item, f"{prefix}{item.name}/")
                    elif item.is_file() and item.suffix == '.md':
                        try:
                            content = item.read_text(encoding='utf-8')
                            if query_lower in content.lower():
                                # Find a snippet around the match
                                idx = content.lower().find(query_lower)
                                start = max(0, idx - 100)
                                end = min(len(content), idx + len(query) + 100)
                                snippet = content[start:end].replace('\n', ' ').strip()
                                if start > 0:
                                    snippet = "..." + snippet
                                if end < len(content):
                                    snippet = snippet + "..."

                                results.append({
                                    "file": f"{prefix}{item.name}",
                                    "snippet": snippet
                                })
                        except Exception:
                            pass

            search_dir(DOCS_DIR)

            return {
                "query": query,
                "results": results[:20],  # Limit results
                "total_matches": len(results)
            }

        return search_docs

    # ----------------------------------------------------------- Agent graph
    def _build_agent(self):
        """Build the ReAct agent using LangGraph 1.0."""

        system_prompt = """You are the Admin Assistant for Agent Foundry.

You help Forge and platform designers understand and operate the system.

You can:
- Answer questions about organizations, domains, instances, deployments and users
- Explain what agents exist and their capabilities (when provided)
- Help the user understand how to use Forge and the control plane
- Answer questions about deployment, architecture, and platform documentation

Available tools:
1. `control_plane_query` - Query the control-plane database for info about
   organizations, domains, instances, deployments, and users.

2. `list_docs` - List documentation files. Use subdirectory param to explore
   folders like 'architecture', 'reference', 'livekit', 'rbac', etc.

3. `read_doc` - Read a specific documentation file by filename
   (e.g., 'DEPLOYMENT.md' or 'architecture/PLATFORM_DEEPDIVE.md').

4. `search_docs` - Search across all documentation for a keyword or phrase.

Guidelines:
- Use control_plane_query for questions about orgs/domains/instances/deployments/users.
- Use the docs tools (list_docs, read_doc, search_docs) for questions about:
  - How to deploy Agent Foundry
  - Architecture and design decisions
  - Configuration and setup guides
  - LiveKit/voice integration
  - RBAC and permissions
  - Docker and development workflow
- When you call a tool, carefully read its JSON response and summarize it for the user.
- Prefer concise, actionable answers tailored to Forge / platform designers.
- If you don't know something or it's not implemented yet, say so clearly.
"""

        graph = create_react_agent(
            model=self.llm,
            tools=self.tools,
            prompt=system_prompt,
            name="admin_assistant",
        )

        return graph

    # -------------------------------------------------------------- Public API
    async def chat(self, message: str) -> dict[str, Any]:
        """Process a user message through the admin assistant agent."""

        try:
            result = await self.graph.ainvoke({"messages": [HumanMessage(content=message)]})
            messages: list[Any] = result.get("messages", [])

            reply = "I'm here to help with Agent Foundry. What would you like to know?"
            for msg in reversed(messages):
                if isinstance(msg, AIMessage):
                    reply = msg.content
                    break

            # If the tool returned structured rows, they will already be summarized in reply;
            # we keep the raw result in case a caller wants to inspect it later.
            return {
                "reply": reply,
                "raw_state": result,
            }
        except Exception as e:
            return {
                "reply": f"I ran into an error answering that: {e}",
                "error": str(e),
            }
