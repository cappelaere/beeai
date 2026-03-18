# Debugging Tool Tracking in Langfuse

## Issue: Tools Not Appearing in Langfuse Traces

If you're not seeing tools in your Langfuse traces, follow these debugging steps:

## Step 1: Verify Langfuse is Enabled

```bash
# Check environment variables
cat .env | grep LANGFUSE

# Should show:
# LANGFUSE_ENABLED=true
# LANGFUSE_PUBLIC_KEY=...
# LANGFUSE_SECRET_KEY=...
# LANGFUSE_HOST=https://us.cloud.langfuse.com
```

## Step 2: Check Console Logs

When you run a query that uses tools, you should see:

**Web UI** (`make dev-ui`):
```
INFO - 🔧 Tool starting: list_properties
INFO - ✓ Tool completed: list_properties (156ms)
INFO - 📊 Trace complete: 2 tools used
```

**If you DON'T see these logs**, the events aren't being captured.

## Step 3: Run Event Debugger

We've created a debug script to see what events BeeAI actually emits:

```bash
# Run the event debugger
python debug_events.py
```

This will:
1. Create an agent with tools
2. Run a query that should use tools
3. Capture ALL events emitted
4. Report which events are tool-related

**Expected output**:
```
🔍 BeeAI Event Debugger
==================================================
This script captures ALL events emitted during agent execution

Creating agent with tools...
Running agent with a query that requires tools...

🔧 TOOL EVENT: tools.list_properties.start | ToolStartEvent | tool: list_properties
🔧 TOOL EVENT: tools.list_properties.success | ToolSuccessEvent | tool: list_properties

✅ Agent completed successfully
Response: Here are some properties...

==================================================
📊 Event Summary:
   Total events captured: 25
   Tool-related events: 2

🔧 Tool Events Detected:
   - tools.list_properties.start (ToolStartEvent)
   - tools.list_properties.success (ToolSuccessEvent)
==================================================
```

## Step 4: Check Event Patterns

Based on the debug output, verify the event listener patterns in `agent_runner.py`:

```python
# Current implementation uses a wildcard listener
root.on("*.*", on_all_events)

# This should capture ALL events, including tool events
```

The event filter checks:
- `'start' in meta.name and hasattr(event, 'tool')` for tool starts
- `'success' in meta.name and hasattr(event, 'tool')` for tool completions

## Step 5: Enable Debug Logging

Temporarily enable debug logging to see event paths:

```python
# In agent_runner.py, change this line:
if 'tool' in meta.path.lower() or 'tool' in str(type(event)).lower():
    logger.debug(f"🔍 Event: {meta.path} | type: {type(event).__name__}")

# To:
logger.info(f"🔍 Event: {meta.path} | type: {type(event).__name__}")
```

Then restart the UI and watch the console for ALL event paths.

## Step 6: Verify observability.py

Check that `log_tool_call` is working:

```python
# In observability.py
def log_tool_call(self, tool_name: str, args: Dict[str, Any], result: Any):
    try:
        trace_context = self.observation.get_trace_context()
        tool_span = self.client.start_observation(
            trace_context=trace_context,
            name=f"tool_{tool_name}",
            as_type="tool",
            input=args,
            output=result,
            metadata={"tool": tool_name}
        )
        tool_span.end()
        self._child_observations.append(tool_span)
    except Exception as e:
        print(f"Warning: Failed to log tool call: {e}")
```

If you see `"Warning: Failed to log tool call"`, there's an issue with the Langfuse API call.

## Step 7: Test with CLI

The CLI provides more immediate feedback:

```bash
make dev-cli

# Then try a query that uses tools:
RealtyIQ> List some properties

# You should see:
  🔧 list_properties...
  ✓ list_properties (156ms)

RealtyIQ> [Response]

📊 Used 1 tool(s)
```

If you see the emoji output, events are being captured. If not, the events aren't being emitted or captured.

## Step 8: Check BeeAI Version

Ensure you're using a compatible BeeAI framework version:

```bash
pip show beeai-framework

# Should show version 0.x.x or higher
```

## Common Issues

### Issue: No Events Captured

**Symptom**: `debug_events.py` shows 0 tool events

**Cause**: Events aren't being emitted or listener isn't registered correctly

**Fix**:
1. Verify BeeAI framework is installed: `pip list | grep beeai`
2. Check if tools are actually being called (agent might not need them)
3. Try a more explicit query like "Use the list_properties tool to show properties"

### Issue: Events Captured But Not in Langfuse

**Symptom**: Console shows "✓ Tool completed" but not in Langfuse dashboard

**Cause**: `tracer.log_tool_call()` is failing silently

**Fix**:
1. Check Langfuse credentials are valid
2. Check Langfuse API errors in console
3. Verify `observability.py` `log_tool_call` method isn't throwing exceptions

### Issue: Wrong Event Pattern

**Symptom**: Some tools captured, others not

**Cause**: Event filtering logic is too specific

**Fix**: The current implementation uses a wildcard `*.*` listener and checks `hasattr(event, 'tool')`, which should capture all tool events regardless of naming.

## Manual Test in Python

```python
import asyncio
from beeai_framework.emitter import Emitter, EventMeta
from beeai_framework.agents.requirement import RequirementAgent
from beeai_framework.backend import ChatModel
from tools import list_properties
from dotenv import load_dotenv
import os

load_dotenv()

async def test():
    def log_event(event, meta: EventMeta):
        print(f"Event: {meta.path} | {type(event).__name__}")
        if hasattr(event, 'tool'):
            print(f"  -> Tool: {event.tool.name if hasattr(event.tool, 'name') else type(event.tool).__name__}")
    
    root = Emitter.root()
    root.on("*.*", log_event)
    
    llm = ChatModel.from_name(os.getenv("LLM_CHAT_MODEL_NAME"))
    agent = RequirementAgent(llm=llm, tools=[list_properties])
    
    result = await agent.run("List properties")
    print(f"\nResponse: {result.last_message.text[:100]}")

asyncio.run(test())
```

Save this as `test_events.py` and run:
```bash
python test_events.py
```

## Expected Behavior

**When Working Correctly:**
1. Console logs show tool start/completion
2. Langfuse dashboard shows traces with child tool observations
3. Each tool appears with input/output data
4. Metadata shows `tools_used` count

**To Verify in Langfuse:**
1. Go to https://us.cloud.langfuse.com
2. Navigate to Traces
3. Click any recent `realtyiq_agent_run` trace
4. Should see "Observations" section
5. Should list `tool_{tool_name}` entries
6. Click to expand and see input/output

## Need Help?

If tools still aren't showing:
1. Run `debug_events.py` and share the output
2. Check console logs for errors
3. Verify the query actually requires tool usage
4. Try the manual test script above

---

**Last Updated**: February 16, 2026
