# LiveKit Voice Agent - Quick Reference

**Date:** November 16, 2025  
**SDK Version:** livekit-agents==1.2.18  
**Pattern:** Agent + AgentSession (Modern)

## Minimal Working Example

```python
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    WorkerOptions,
    cli,
    function_tool,
)
from livekit.plugins import deepgram, openai, silero


@function_tool
async def example_tool(ctx, arg: str) -> str:
    """Tool description for LLM"""
    return f"Result for {arg}"


async def entrypoint(ctx: JobContext):
    # CRITICAL: Connect to room via WebRTC
    await ctx.connect()

    # Define agent
    agent = Agent(
        instructions="System prompt here",
        tools=[example_tool],
    )

    # Create session with pipeline
    session = AgentSession(
        agent=agent,
        vad=silero.VAD.load(),
        stt=deepgram.STT(),
        llm=openai.LLM(model="gpt-4o-mini"),
        tts=openai.TTS(voice="alloy"),
    )

    # Start session
    await session.start(ctx.room)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
```

## Core Concepts

### 1. Agent vs AgentSession

**Agent**

- Defines behavior (instructions + tools)
- Stateless configuration
- Reusable across sessions

**AgentSession**

- Manages conversation lifecycle
- Contains VAD/STT/LLM/TTS pipeline
- Handles WebRTC media

### 2. Required Environment Variables

```bash
# LiveKit Server
LIVEKIT_URL=ws://livekit:7880
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret

# AI Providers
OPENAI_API_KEY=sk-...
DEEPGRAM_API_KEY=...
```

### 3. Function Tools

```python
@function_tool
async def tool_name(
    ctx: RunContext,  # Required first parameter
    param1: str,      # Tool parameters
    param2: int = 0,  # Optional with default
) -> str:           # Return type
    """
    Tool description shown to LLM.

    Args:
        param1: Description
        param2: Description
    """
    # Implementation
    return "result"
```

### 4. Worker Lifecycle

```python
cli.run_app(WorkerOptions(
    entrypoint_fnc=entrypoint,
    # Worker automatically:
    # 1. Connects to LIVEKIT_URL
    # 2. Registers with server
    # 3. Listens for room assignments
    # 4. Calls entrypoint() for each room
))
```

## Common Patterns

### Pattern: Simple Voice Assistant

```python
agent = Agent(
    instructions="You are a helpful assistant",
)

session = AgentSession(
    agent=agent,
    vad=silero.VAD.load(),
    stt=deepgram.STT(),
    llm=openai.LLM(model="gpt-4o-mini"),
    tts=openai.TTS(voice="alloy"),
)
```

### Pattern: Agent with Tools

```python
@function_tool
async def get_weather(ctx, location: str) -> str:
    return f"Weather in {location}: Sunny, 70°F"


agent = Agent(
    instructions="""
    You are a weather assistant.
    Use the get_weather tool to answer weather questions.
    """,
    tools=[get_weather],
)
```

### Pattern: Custom LLM Configuration

```python
session = AgentSession(
    agent=agent,
    llm=openai.LLM(
        model="gpt-4o-mini",
        temperature=0.7,
        max_tokens=500,
    ),
)
```

### Pattern: Room Events

```python
async def entrypoint(ctx: JobContext):
    await ctx.connect()

    @ctx.room.on("participant_connected")
    def on_participant(participant):
        logger.info(f"User joined: {participant.identity}")

    @ctx.room.on("participant_disconnected")
    def on_disconnect(participant):
        logger.info(f"User left: {participant.identity}")

    # ... rest of setup
```

## SDK Versions

### Current (Modern):

```
livekit==1.0.19
livekit-agents==1.2.18        # Agent + AgentSession
livekit-api==1.0.7
livekit-plugins-deepgram
livekit-plugins-openai
livekit-plugins-silero
```

### Deprecated (Old):

```
livekit-agents<1.0  # VoiceAssistant class (deprecated)
```

## Migration from VoiceAssistant

### Before:

```python
assistant = voice.VoiceAssistant(
    vad=silero.VAD.load(),
    stt=deepgram.STT(),
    llm=custom_llm_wrapper,
    tts=openai.TTS(),
)
assistant.start(ctx.room)
```

### After:

```python
agent = Agent(instructions="...")
session = AgentSession(
    agent=agent,
    vad=silero.VAD.load(),
    stt=deepgram.STT(),
    llm=openai.LLM(model="gpt-4o-mini"),
    tts=openai.TTS(),
)
await session.start(ctx.room)
```

## Debugging

### Enable Debug Logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("livekit")
logger.setLevel(logging.DEBUG)
```

### Common Errors:

**"Worker not connecting"** → Check `LIVEKIT_URL`, `LIVEKIT_API_KEY`,
`LIVEKIT_API_SECRET`

**"Agent not joining room"** → Ensure `await ctx.connect()` is called

**"No audio from agent"** → Verify `OPENAI_API_KEY` and TTS configuration

**"Tools not being called"** → Add tool usage hints in `instructions`

## Testing

### Local Testing:

```bash
python voice_agent_worker.py start
```

### Docker Testing:

```bash
docker compose up voice-agent-worker -d
docker compose logs -f voice-agent-worker
```

### Room Testing:

```bash
# Create room
curl -X POST http://localhost:8000/api/voice/session \
  -d '{"user_id":"test","agent_id":"pm"}'
```

## Resources

- [Official Docs](https://docs.livekit.io/agents/)
- [Quickstart](https://docs.livekit.io/agents/quickstarts/voice-agent/)
- [Examples](https://github.com/livekit/agents/tree/main/examples)
- [Starter Project](https://github.com/livekit-examples/agent-starter-python)

---

**Key Takeaways:**

1. Always use `Agent` + `AgentSession` (not `VoiceAssistant`)
2. Always call `await ctx.connect()` first
3. Use `@function_tool` for LLM function calling
4. Use native `openai.LLM()` (not custom wrappers)
5. Follow official examples for best practices
