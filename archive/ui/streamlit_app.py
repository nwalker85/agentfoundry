"""
PM Agent Streamlit UI
Interactive interface for Project Manager AI
"""

import streamlit as st
import asyncio
import os
from datetime import datetime
from pathlib import Path
from pm_agent import PMAgent
from pm_agent.tools import get_notion_tools
from core.logging import setup_logging, get_logger, session_id

# Initialize logging
log_dir = Path(os.getenv("WORKING_DIR", "/app/working_dir")) / "logs"
setup_logging(log_level="INFO", log_dir=log_dir)
logger = get_logger(__name__)


st.set_page_config(
    page_title="PM Agent - Engineering Department",
    page_icon="👔",
    layout="wide"
)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "pm_agent" not in st.session_state:
    st.session_state.pm_agent = None
if "initialized" not in st.session_state:
    st.session_state.initialized = False


async def initialize_pm():
    """Initialize PM agent"""
    if st.session_state.pm_agent is None:
        logger.info("Initializing PM Agent from UI")
        with st.spinner("Initializing PM Agent..."):
            st.session_state.pm_agent = PMAgent()
            success = await st.session_state.pm_agent.initialize()
            if success:
                st.session_state.initialized = True
                st.success("✓ PM Agent ready")
                logger.info("PM Agent initialized successfully")
            else:
                st.error("✗ Failed to initialize PM Agent - check Notion setup")
                logger.error("PM Agent initialization failed")


async def process_message(user_input: str):
    """Process user message with PM agent"""
    logger.info(f"Processing user message: {user_input[:50]}...")
    response = await st.session_state.pm_agent.process_message(user_input)
    logger.debug(f"Response generated: {len(response)} chars")
    return response


st.title("👔 PM Agent - Engineering Department")
st.caption("AI Project Manager for SDLC Orchestration")

with st.sidebar:
    st.header("Status")
    
    if st.session_state.initialized:
        st.success("🟢 PM Agent Active")
        st.info(f"Model: {os.getenv('OLLAMA_MODEL', 'qwen2.5:14b')}")
    else:
        st.warning("🟡 Initializing...")
    
    st.divider()
    
    st.header("Quick Actions")
    
    if st.button("📊 View All Tasks"):
        st.session_state.messages.append({
            "role": "user",
            "content": "Show me all current tasks with their status"
        })
    
    if st.button("🚨 Check Blockers"):
        st.session_state.messages.append({
            "role": "user",
            "content": "What tasks are currently blocked?"
        })
    
    if st.button("📈 Sprint Progress"):
        st.session_state.messages.append({
            "role": "user",
            "content": "Give me a progress report"
        })
    
    st.divider()
    
    st.header("Resources")
    st.caption("Available Engineers:")
    resources = [
        "fastmcp_engineer",
        "python_engineer",
        "streamlit_engineer",
        "qa_functional"
    ]
    for resource in resources:
        st.text(f"• {resource}")
    
    st.divider()
    
    if st.button("🔄 Reset Conversation"):
        st.session_state.messages = []
        st.rerun()

col1, col2 = st.columns([2, 1])

with col1:
    st.header("Chat with PM")
    
    chat_container = st.container(height=400)
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
    
    if prompt := st.chat_input("Ask PM anything..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with chat_container:
            with st.chat_message("user"):
                st.write(prompt)
        
        with chat_container:
            with st.chat_message("assistant"):
                with st.spinner("PM is thinking..."):
                    response = asyncio.run(process_message(prompt))
                    st.write(response)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response
                    })

with col2:
    st.header("Task Board")
    
    if st.session_state.initialized:
        with st.spinner("Loading tasks..."):
            notion_tools = get_notion_tools()
            result = asyncio.run(notion_tools.query_tasks())
            
            if result["success"] and result["data"]:
                tasks = result["data"]
                
                statuses = {}
                for task in tasks:
                    status = task.get("status", "Unknown")
                    if status not in statuses:
                        statuses[status] = []
                    statuses[status].append(task)
                
                for status, task_list in statuses.items():
                    with st.expander(f"{status} ({len(task_list)})", expanded=(status in ["In Progress", "Blocked"])):
                        for task in task_list:
                            priority = task.get("priority", "P2")
                            
                            priority_color = {
                                "P0": "🔴",
                                "P1": "🟠",
                                "P2": "🟡",
                                "P3": "⚪"
                            }.get(priority, "⚪")
                            
                            st.markdown(f"{priority_color} **{task['title']}**")
                            st.divider()
            else:
                st.info("No tasks yet. Create your first epic!")
    else:
        st.info("Initializing PM Agent...")

if not st.session_state.initialized:
    asyncio.run(initialize_pm())

st.divider()
st.caption(f"PM Agent v1.0 | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
