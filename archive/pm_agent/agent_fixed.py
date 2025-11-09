"""
PM Agent - Fixed and Improved Version
Addresses priority enum issues and performance tracking bugs
"""

import os
import json
import uuid
import time
from typing import Dict, Any
from enum import Enum
from langgraph.graph import StateGraph, END
from langchain_core.messages import AIMessage
from ollama import AsyncClient
from jsonschema import validate, ValidationError

from core.logging import (
    get_logger,
    get_perf_logger,
    correlation_id,
    user_id as log_user_id,
    log_function_call
)
from pm_agent.state import PMState, Task, Story, Epic, TaskStatus, TaskPriority, ResourceType
from pm_agent.tools import get_notion_tools
from pm_agent.prompts import (
    PM_SYSTEM_PROMPT,
    BREAKDOWN_PROMPT_TEMPLATE,
    ASSIGNMENT_PROMPT_TEMPLATE,
    BLOCKER_ANALYSIS_PROMPT
)

logger = get_logger(__name__)
perf = get_perf_logger()

# Create reverse mapping for priority values
PRIORITY_VALUE_MAP = {p.value: p for p in TaskPriority}
PRIORITY_NAME_MAP = {p.name: p for p in TaskPriority}

# JSON Schema for LLM output validation
BREAKDOWN_SCHEMA = {
    "type": "object",
    "properties": {
        "epic": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "description": {"type": "string"},
                "business_value": {"type": "string"},
                "success_metrics": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["title", "description"]
        },
        "stories": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "user_story": {"type": "string"},
                    "acceptance_criteria": {"type": "array", "items": {"type": "string"}},
                    "priority": {"type": "string", "enum": ["P0", "P1", "P2", "P3", "CRITICAL", "HIGH", "MEDIUM", "LOW"]},
                    "story_points": {"type": "integer"}
                },
                "required": ["title", "user_story"]
            }
        },
        "tasks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "priority": {"type": "string", "enum": ["P0", "P1", "P2", "P3", "CRITICAL", "HIGH", "MEDIUM", "LOW"]},
                    "story_id": {"type": "string"},
                    "dependencies": {"type": "array", "items": {"type": "string"}},
                    "estimate_hours": {"type": "number"}
                },
                "required": ["title"]
            }
        }
    }
}


class PMAgent:
    """Project Manager AI Agent - Fixed Version"""
    
    def __init__(self):
        self.ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
        self.llm = AsyncClient(host=self.ollama_host)
        self.notion = get_notion_tools()
        self.graph = self._build_graph()
        logger.info(f"PM Agent initialized with model={self.model}, host={self.ollama_host}")
    
    def _parse_priority(self, priority_value: str) -> TaskPriority:
        """
        Parse priority from various formats
        Handles: P0-P3 values, CRITICAL/HIGH/MEDIUM/LOW names
        """
        if not priority_value:
            return TaskPriority.MEDIUM
        
        priority_upper = priority_value.upper()
        
        # Try as value (P0, P1, etc.)
        if priority_upper in PRIORITY_VALUE_MAP:
            return PRIORITY_VALUE_MAP[priority_upper]
        
        # Try as name (CRITICAL, HIGH, etc.)
        if priority_upper in PRIORITY_NAME_MAP:
            return PRIORITY_NAME_MAP[priority_upper]
        
        # Default fallback
        logger.warning(f"Unknown priority value: {priority_value}, defaulting to MEDIUM")
        return TaskPriority.MEDIUM
    
    def _build_graph(self) -> StateGraph:
        """Build LangGraph workflow"""
        workflow = StateGraph(PMState)
        
        workflow.add_node("analyze_request", self.analyze_request)
        workflow.add_node("breakdown_work", self.breakdown_work)
        workflow.add_node("assign_tasks", self.assign_tasks)
        workflow.add_node("track_progress", self.track_progress)
        workflow.add_node("generate_response", self.generate_response)
        
        workflow.set_entry_point("analyze_request")
        
        workflow.add_conditional_edges(
            "analyze_request",
            self.route_operation,
            {
                "breakdown": "breakdown_work",
                "assign": "assign_tasks",
                "track": "track_progress",
                "response": "generate_response"
            }
        )
        
        workflow.add_edge("breakdown_work", "generate_response")
        workflow.add_edge("assign_tasks", "generate_response")
        workflow.add_edge("track_progress", "generate_response")
        workflow.add_edge("generate_response", END)
        
        logger.debug("LangGraph workflow compiled")
        return workflow.compile()
    
    @log_function_call()
    async def analyze_request(self, state: PMState) -> PMState:
        """Analyze user input to determine operation type"""
        user_input = state["user_input"]
        logger.info(f"Analyzing request: {user_input[:100]}...")
        
        start = time.time()
        prompt = f"""Analyze this PM request and categorize:

User Input: {user_input}

Categories:
- breakdown: Create new epic/stories/tasks from requirements
- assign: Assign existing tasks to resources
- track: Status update on blockers/progress
- response: Simple question or clarification

Output only the category name.
"""
        
        response = await self.llm.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": PM_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
        )
        
        operation = response["message"]["content"].strip().lower()
        state["operation"] = operation if operation in ["breakdown", "assign", "track"] else "response"
        
        perf.track("analyze_request", time.time() - start, determined_operation=operation)
        logger.info(f"Operation determined: {state['operation']}")
        
        return state
    
    def route_operation(self, state: PMState) -> str:
        """Route to appropriate operation node"""
        operation = state["operation"]
        logger.debug(f"Routing to: {operation}")
        
        if operation == "breakdown":
            return "breakdown"
        elif operation == "assign":
            return "assign"
        elif operation == "track":
            return "track"
        else:
            return "response"
    
    @log_function_call()
    async def breakdown_work(self, state: PMState) -> PMState:
        """Break down requirements into epic/stories/tasks with proper validation"""
        user_input = state["user_input"]
        logger.info("Starting work breakdown")
        start = time.time()
        
        # Enhanced prompt with explicit output format
        prompt = f"""{BREAKDOWN_PROMPT_TEMPLATE.format(user_input=user_input)}

IMPORTANT: Output must be valid JSON with this exact structure:
{{
    "epic": {{
        "title": "string",
        "description": "string",
        "business_value": "string",
        "success_metrics": ["string", ...]
    }},
    "stories": [
        {{
            "title": "string",
            "description": "string", 
            "user_story": "As a ... I want ... so that ...",
            "acceptance_criteria": ["string", ...],
            "priority": "P1",  // Use P0, P1, P2, or P3
            "story_points": 5
        }}
    ],
    "tasks": [
        {{
            "title": "string",
            "description": "string",
            "priority": "P2",  // Use P0, P1, P2, or P3
            "story_id": "optional_string",
            "dependencies": [],
            "estimate_hours": 4.0
        }}
    ]
}}

Use priority values: P0 (Critical), P1 (High), P2 (Medium), P3 (Low)
"""
        
        try:
            response = await self.llm.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": PM_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                format="json"
            )
            
            breakdown = json.loads(response["message"]["content"])
            
            # Validate against schema
            try:
                validate(instance=breakdown, schema=BREAKDOWN_SCHEMA)
            except ValidationError as e:
                logger.warning(f"Schema validation failed: {e}, attempting to fix...")
                # Could implement auto-fixing logic here
            
            # Create epic with proper priority parsing
            epic_data = breakdown.get("epic", {})
            epic = Epic(
                title=epic_data.get("title", "Untitled Epic"),
                description=epic_data.get("description", ""),
                business_value=epic_data.get("business_value", ""),
                success_metrics=epic_data.get("success_metrics", []),
                stories=[],
                priority=TaskPriority.MEDIUM  # Default priority for epics
            )
            
            epic_result = await self.notion.create_epic(epic)
            if epic_result["success"]:
                epic.notion_id = epic_result["notion_id"]
                state["current_epic"] = epic
                logger.info(f"Created epic: {epic.title} (ID: {epic.notion_id})")
            
            # Create stories with fixed priority parsing
            stories = []
            for story_data in breakdown.get("stories", []):
                priority = self._parse_priority(story_data.get("priority", "P2"))
                
                story = Story(
                    title=story_data.get("title", ""),
                    description=story_data.get("description", ""),
                    user_story=story_data.get("user_story", ""),
                    acceptance_criteria=story_data.get("acceptance_criteria", []),
                    epic_id=epic.notion_id,
                    tasks=[],
                    priority=priority,
                    story_points=story_data.get("story_points")
                )
                
                story_result = await self.notion.create_story(story)
                if story_result["success"]:
                    story.notion_id = story_result["notion_id"]
                    stories.append(story)
                    logger.debug(f"Created story: {story.title}")
            
            state["current_stories"] = stories
            
            # Create tasks with fixed priority parsing
            tasks = []
            for task_data in breakdown.get("tasks", []):
                priority = self._parse_priority(task_data.get("priority", "P2"))
                
                task = Task(
                    title=task_data.get("title", ""),
                    description=task_data.get("description", ""),
                    status=TaskStatus.BACKLOG,
                    priority=priority,
                    assigned_to=None,
                    story_id=task_data.get("story_id"),
                    dependencies=task_data.get("dependencies", []),
                    estimate_hours=task_data.get("estimate_hours", 0)
                )
                
                task_result = await self.notion.create_task(task)
                if task_result["success"]:
                    task.notion_id = task_result["notion_id"]
                    tasks.append(task)
                    logger.debug(f"Created task: {task.title}")
            
            state["current_tasks"] = tasks
            state["messages"].append(
                AIMessage(content=f"Created epic '{epic.title}' with {len(stories)} stories and {len(tasks)} tasks in Notion")
            )
            
            perf.track("breakdown_work", time.time() - start, 
                      stories_created=len(stories), tasks_created=len(tasks))
            logger.info(f"Breakdown complete: {len(stories)} stories, {len(tasks)} tasks")
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in breakdown: {e}", exc_info=True)
            state["messages"].append(
                AIMessage(content=f"Error parsing breakdown: {str(e)}")
            )
        except Exception as e:
            logger.error(f"Error in breakdown_work: {e}", exc_info=True)
            state["messages"].append(
                AIMessage(content=f"Error creating work items: {str(e)}")
            )
        
        return state
    
    @log_function_call()
    async def assign_tasks(self, state: PMState) -> PMState:
        """Assign tasks to available resources"""
        logger.info("Starting task assignment")
        start = time.time()
        
        tasks = state.get("current_tasks", [])
        available_resources = state.get("available_resources", [r.value for r in ResourceType])
        resource_capacity = state.get("resource_capacity", {})
        
        if not tasks:
            result = await self.notion.query_tasks()
            if result["success"]:
                tasks = result["data"]
        
        logger.debug(f"Assigning {len(tasks)} tasks across {len(available_resources)} resources")
        
        prompt = ASSIGNMENT_PROMPT_TEMPLATE.format(
            available_resources=json.dumps(available_resources),
            resource_capacity=json.dumps(resource_capacity),
            tasks=json.dumps([{"title": t.get("title") if isinstance(t, dict) else t.title} for t in tasks])
        )
        
        response = await self.llm.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": PM_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
        )
        
        assignment_text = response["message"]["content"]
        state["messages"].append(AIMessage(content=f"Assignment plan:\n{assignment_text}"))
        
        perf.track("assign_tasks", time.time() - start, task_count=len(tasks))
        logger.info(f"Assignment complete for {len(tasks)} tasks")
        
        return state
    
    @log_function_call()
    async def track_progress(self, state: PMState) -> PMState:
        """Track progress, identify blockers"""
        logger.info("Tracking progress")
        start = time.time()
        
        result = await self.notion.query_tasks()
        
        if result["success"]:
            tasks = result["data"]
            
            blocked = [t for t in tasks if t.get("status") == "Blocked"]
            in_progress = [t for t in tasks if t.get("status") == "In Progress"]
            
            state["blockers"] = [
                {"task_id": t["id"], "title": t["title"], "reason": "Unknown"}
                for t in blocked
            ]
            
            logger.info(f"Progress: {len(in_progress)} in progress, {len(blocked)} blocked")
            
            report = f"""Progress Report:

In Progress: {len(in_progress)} tasks
Blocked: {len(blocked)} tasks

Blocked Tasks:
{chr(10).join([f"- {t['title']}" for t in blocked]) if blocked else "None"}
"""
            state["messages"].append(AIMessage(content=report))
            perf.track("track_progress", time.time() - start, 
                      tasks_in_progress=len(in_progress), tasks_blocked=len(blocked))
        else:
            logger.error(f"Failed to query tasks: {result.get('error')}")
        
        return state
    
    @log_function_call()
    async def generate_response(self, state: PMState) -> PMState:
        """Generate final response to user"""
        if state.get("messages") and isinstance(state["messages"][-1], AIMessage):
            return state
        
        logger.debug("Generating final response")
        user_input = state["user_input"]
        operation = state["operation"]
        
        prompt = f"""User asked: {user_input}

Operation completed: {operation}

Generate a helpful, conversational response summarizing what was done.
"""
        
        response = await self.llm.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": PM_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
        )
        
        state["messages"].append(AIMessage(content=response["message"]["content"]))
        
        return state
    
    async def process_message(self, user_input: str, session_state: Dict[str, Any] = None) -> str:
        """Process user message and return response - FIXED VERSION"""
        # Set correlation ID for request tracing
        corr_id = str(uuid.uuid4())
        correlation_id.set(corr_id)
        
        logger.info(f"Processing message (corr_id={corr_id}): {user_input[:100]}...")
        start = time.time()
        
        state: PMState = {
            "messages": [],
            "user_input": user_input,
            "operation": "idle",
            "current_epic": None,
            "current_stories": [],
            "current_tasks": [],
            "available_resources": [r.value for r in ResourceType],
            "resource_capacity": {r.value: 40.0 for r in ResourceType},
            "blockers": [],
            "overdue_tasks": [],
            "dependencies_unmet": [],
            "needs_user_input": False,
            "has_critical_blocker": False,
            "current_sprint": None,
            "sprint_end_date": None
        }
        
        if session_state:
            state.update(session_state)
        
        try:
            final_state = await self.graph.ainvoke(state)
            
            if final_state["messages"]:
                last_message = final_state["messages"][-1]
                if isinstance(last_message, AIMessage):
                    response = last_message.content
                else:
                    response = "I processed your request."
            else:
                response = "I processed your request."
            
            # FIXED: Don't pass 'operation' as keyword arg to track()
            perf.track("process_message", time.time() - start, 
                      success=True,
                      determined_operation=final_state.get("operation", "unknown"))
            
            logger.info(f"Message processed successfully (corr_id={corr_id})")
            return response
            
        except Exception as e:
            logger.error(f"Error processing message (corr_id={corr_id}): {e}", exc_info=True)
            perf.track("process_message", time.time() - start, success=False, error=str(e))
            raise
    
    async def initialize(self):
        """Initialize PM agent (setup Notion databases)"""
        logger.info("Initializing PM Agent...")
        start = time.time()
        
        try:
            result = await self.notion.initialize_databases()
            if result["success"]:
                logger.info("✓ Notion databases initialized successfully")
                perf.track("initialize", time.time() - start, success=True)
                return True
            else:
                logger.error(f"Database initialization failed: {result['error']}")
                perf.track("initialize", time.time() - start, success=False, error=result['error'])
                return False
        except Exception as e:
            logger.error(f"Exception during initialization: {e}", exc_info=True)
            perf.track("initialize", time.time() - start, success=False, error=str(e))
            return False
