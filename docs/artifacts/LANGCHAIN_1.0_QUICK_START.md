# LangChain 1.0 Migration - Quick Start Guide

**Version:** 0.9.0  
**Duration:** 2 weeks (Nov 18 - Dec 2, 2025)  
**Status:** 🔴 Not Started

---

## Week 1: Core Migration (Nov 18-22)

### Day 1-2: Setup (4-6 hours)

**Owner:** Senior Engineer

#### Morning: Dependencies

```bash
# 1. Create backup branch
git checkout -b migration/langchain-1.0-backup
git push origin migration/langchain-1.0-backup

# 2. Create migration branch
git checkout -b feat/langchain-1.0-migration
```

**Update requirements.txt:**

```python
langchain==1.0.0
langgraph==1.0.0
langchain-core==1.0.0
langchain-openai>=0.2.10
langchain-anthropic>=0.3.4
```

**Test install:**

```bash
pip install -r requirements.txt
python -c "import langchain; print(langchain.__version__)"  # Should print 1.0.0
```

#### Afternoon: Version Config

**Create files:**

1. `backend/config/agent_versions.py`
2. `backend/config/platform_config.py`
3. `docs/VERSION_MANAGEMENT.md` (stub)

**Validate:**

```bash
python -c "from backend.config import AgentVersionConfig; print(AgentVersionConfig.default())"
```

**Deliverable:** ✅ Dependencies updated, version config in place

---

### Day 3-4: PM Agent Refactor (8-10 hours)

#### Task 1: Extract Prompts

**Create:** `agent/constants/prompts.py`

```python
UNDERSTANDING_PROMPT = """..."""
CLARIFICATION_PROMPT = """..."""
VALIDATION_PROMPT = """..."""
PLANNING_PROMPT = """..."""
```

#### Task 2: Refactor pm_graph.py

**Pattern:**

```python
from langchain.agents import create_agent

class PMAgent:
    def __init__(self):
        # Create sub-agents
        self.understanding_agent = create_agent(
            model="openai:gpt-4",
            system_prompt=UNDERSTANDING_PROMPT,
            tools=[]
        )

        self.clarification_agent = create_agent(
            model="openai:gpt-4",
            system_prompt=CLARIFICATION_PROMPT,
            tools=[]
        )

        # Keep LangGraph orchestration (mandatory)
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(AgentState)

        # Nodes invoke create_agent instances
        workflow.add_node("understand", self._understand_wrapper)
        workflow.add_node("clarify", self._clarify_wrapper)
        # ... etc

        return workflow.compile()

    async def _understand_wrapper(self, state: AgentState):
        result = await self.understanding_agent.ainvoke({
            "messages": state["messages"]
        })

        # Parse content_blocks (new in 1.0)
        # Update state
        return state
```

**Steps:**

1. Create agent instances in `__init__`
2. Convert node functions to wrapper methods
3. Update to use `content_blocks` interface
4. Test each node independently

**Validate:**

```bash
pytest tests/integration/test_langgraph_agent.py::test_understanding -v
pytest tests/integration/test_langgraph_agent.py::test_clarification -v
# etc for each node
```

**Deliverable:** ✅ PM agent refactored, tests passing

---

### Day 5: Integration Testing (6-8 hours)

#### Morning: Update Tests

**File:** `tests/integration/test_langgraph_agent.py`

**Changes:**

```python
# Old
result = agent.invoke({"messages": [...]})
text = result.content  # String

# New
result = agent.invoke({"messages": [...]})
for block in result.content_blocks:
    if block.type == "text":
        text = block.text
```

**Run full test suite:**

```bash
pytest tests/integration/ -v
pytest tests/e2e/ -v
```

#### Afternoon: Performance Benchmarking

```bash
# Baseline (v0.8.0)
git checkout main
pytest tests/integration/test_langgraph_agent.py --benchmark-only

# Current (v0.9.0)
git checkout feat/langchain-1.0-migration
pytest tests/integration/test_langgraph_agent.py --benchmark-only

# Compare results
```

**Acceptance:** <10% regression

**Deliverable:** ✅ All tests passing, performance validated

---

## Week 2: Documentation & Release (Nov 25-29)

### Day 6-7: Documentation (8-10 hours)

#### Create Migration Guide

**File:** `docs/LANGCHAIN_1.0_MIGRATION_GUIDE.md`

**Sections:**

1. Breaking changes
2. Code examples (before/after)
3. Import path changes
4. Troubleshooting

#### Update Architecture Docs

**File:** `docs/ARCHITECTURE.md`

**Add:**

- LangChain 1.0 architecture diagram
- `create_agent` usage patterns
- Version-selectability section

#### Update API Docs

**File:** `docs/API.md`

**Add:**

- Version headers
- New request/response schemas
- `content_blocks` interface docs

#### Update README

**File:** `README.md`

**Changes:**

- Python 3.10+ requirement
- LangChain 1.0 in stack
- Link to migration guide
- What's new in v0.9.0

**Deliverable:** ✅ All docs updated and reviewed

---

### Day 8: Release Prep (6 hours)

#### Update CHANGELOG

**File:** `CHANGELOG.md`

**Add v0.9.0 entry:**

```markdown
## [0.9.0] - 2025-12-02

### 🚀 Major Changes

- LangChain 1.0 Migration (0.3.15 → 1.0.0)
- LangGraph 1.0 Migration (0.2.39 → 1.0.0)
- Python 3.10+ Required

### ✨ Enhancements

- `create_agent` abstraction
- Version-selectable architecture
- Enhanced middleware support

### ⚠️ Breaking Changes

- Python 3.9 unsupported
- Import path changes
- `content_blocks` interface
```

#### Final Testing

```bash
# Full test suite
pytest -v

# Mock mode validation
NOTION_DATABASE_STORIES_ID="" GITHUB_REPO="" python mcp_server.py

# Manual testing
# 1. Start MCP server
# 2. Start frontend
# 3. Create story via UI
# 4. Verify in Notion
```

#### Create Release PR

```bash
git add .
git commit -m "feat: migrate to LangChain 1.0 + LangGraph 1.0

- Upgrade dependencies to LangChain 1.0.0 / LangGraph 1.0.0
- Refactor PM agent to use create_agent abstraction
- Implement version-selectable architecture
- Update all documentation for 1.0 patterns
- Require Python 3.10+ (drop 3.9 support)

BREAKING CHANGE: Python 3.9 no longer supported. Minimum version is 3.10.

Closes #XXX"

git push origin feat/langchain-1.0-migration
```

**Open PR on GitHub/GitLab**

- Add migration plan link
- Request code review
- Link to testing results

**Deliverable:** ✅ Release PR created, ready for review

---

### Day 9-10: Buffer & Stabilization (8 hours)

#### Activities:

1. Address code review feedback
2. Fix any discovered issues
3. Additional testing as needed
4. Documentation refinements
5. Stakeholder demo prep

#### Stakeholder Demo (Day 10 afternoon)

**Agenda:**

1. Show migration plan (5 min)
2. Demo refactored agent (10 min)
3. Discuss version-selectability (5 min)
4. Q&A (10 min)

**Deliverable:** ✅ Stakeholder approval to merge

---

## Daily Checklist

### Every Morning:

- [ ] Pull latest from main
- [ ] Run tests locally: `pytest -v`
- [ ] Check for LangChain 1.0 release notes/updates

### Every Evening:

- [ ] Commit progress: `git add . && git commit -m "wip: <description>"`
- [ ] Push to branch: `git push origin feat/langchain-1.0-migration`
- [ ] Update progress in Notion (if tracking)

---

## Rollback Procedure

### If Critical Issues Found:

```bash
# 1. Stop current work
git stash

# 2. Checkout backup
git checkout migration/langchain-1.0-backup

# 3. Revert to v0.8.0 dependencies
pip install langchain==0.3.15 langgraph==0.2.39

# 4. Validate rollback
pytest tests/integration/test_langgraph_agent.py -v

# 5. Document blocker
# Create docs/artifacts/MIGRATION_BLOCKERS.md
```

### Rollback Decision Criteria:

- Story creation completely broken
- Performance regression >25%
- Unresolvable LangChain 1.0 bug
- Unable to fix within 2-week timeline

---

## Quick Reference

### Key Files to Modify:

1. `requirements.txt` - Dependencies
2. `agent/pm_graph.py` - Main agent refactor
3. `agent/constants/prompts.py` - System prompts (new)
4. `backend/config/agent_versions.py` - Version config (new)
5. `tests/integration/test_langgraph_agent.py` - Test updates

### Key Commands:

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/integration/test_langgraph_agent.py -v

# Check version
python -c "import langchain; print(langchain.__version__)"

# Run MCP server
python mcp_server.py

# Run frontend
npm run dev
```

### Help & Resources:

- Migration Plan (detailed): `docs/artifacts/LANGCHAIN_1.0_MIGRATION_PLAN.md`
- LangChain 1.0 Docs: https://python.langchain.com/docs/
- LangGraph 1.0 Docs: https://langchain-ai.github.io/langgraph/
- User Requirements: (attached document from user)

---

## Success Indicators

### ✅ Ready to Merge When:

- [ ] All tests passing (`pytest -v`)
- [ ] Performance within 10% of baseline
- [ ] All documentation updated
- [ ] CHANGELOG entry complete
- [ ] Code review approved
- [ ] Stakeholder demo successful
- [ ] No critical bugs for 48 hours

### 🚀 Ready to Deploy When:

- [ ] Merged to main
- [ ] CI/CD pipeline green
- [ ] Development environment tested
- [ ] Rollback procedure validated

---

**Last Updated:** November 15, 2025  
**Next Review:** Daily during migration  
**Contact:** Engineering Team
