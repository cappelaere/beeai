# Langfuse Tool Tracking

## Overview

The RealtyIQ observability integration now captures **all tool calls** made by the agent and logs them to Langfuse as separate observations. This provides complete visibility into which tools are being used, their inputs/outputs, and execution times.

## What Gets Tracked

### 1. Agent-Level Trace
Each agent run creates a main trace/observation with:
- **Input**: User prompt
- **Output**: Agent response
- **Metadata**: User ID, session ID, source, tools used count
- **Duration**: Total elapsed time

### 2. Tool-Level Observations
Each tool call creates a child observation with:
- **Tool Name**: Which tool was called (e.g., `list_properties`, `get_property_detail`)
- **Input**: Tool parameters/arguments
- **Output**: Tool response (truncated to 500 chars for large outputs)
- **Duration**: Tool execution time in milliseconds
- **Type**: Marked as "tool" observation type

### 3. LLM-Level Generations (if logged)
Optionally tracks:
- Model used
- Tokens consumed
- Cost (if available)

## Implementation

### How It Works

1. **Event Subscription**: Listens to BeeAI framework tool events:
   - `ToolStartEvent` - When tool execution begins
   - `ToolSuccessEvent` - When tool completes successfully
   - `ToolErrorEvent` - When tool encounters an error

2. **Event Matching**: Uses wildcard pattern `*.*tool*start`, `*.*tool*success`, `*.*tool*error` to capture all tool-related events from the BeeAI framework's event emitter

3. **Langfuse Logging**: For each tool call:
   - Creates a child observation in Langfuse
   - Links it to the parent agent trace
   - Records input, output, and timing

4. **Metadata**: Adds tool usage summary to agent output metadata

## Data Flow

```
User Prompt
    ↓
Agent Run (Main Trace)
    ├─ Tool Call 1 (Child Observation)
    │   ├─ Input: {property_id: 123}
    │   ├─ Output: {...property data...}
    │   └─ Duration: 150ms
    ├─ Tool Call 2 (Child Observation)
    │   ├─ Input: {site_id: 3}
    │   ├─ Output: {...site data...}
    │   └─ Duration: 85ms
    └─ Agent Response (Output)
        ├─ Tools Used: 2
        └─ Tool Names: [list_properties, get_site_detail]
```

## Viewing in Langfuse Dashboard

### Access the Dashboard

1. Click **Observability** in the left navbar
2. Or visit: `https://us.cloud.langfuse.com/project/...`

### What You'll See

**Traces View:**
```
realtyiq_agent_run
├─ Input: "Show me properties for site 3"
├─ Duration: 1.2s
├─ Observations: 3
│   ├─ tool_list_properties (150ms)
│   ├─ tool_get_site_detail (85ms)
│   └─ tool_think (45ms)
└─ Output: "Here are the properties..."
```

**Details Panel:**
- Agent trace with full conversation
- Each tool as a separate observation
- Input/output for each tool
- Execution timeline
- Performance metrics

## Benefits

### 1. Complete Visibility
See exactly which tools are being called for each query:
- Tool usage patterns
- Most frequently used tools
- Tool call sequences

### 2. Performance Analysis
Identify slow tools:
- Compare tool execution times
- Find bottlenecks
- Optimize API calls

### 3. Debugging
Understand agent behavior:
- Why a tool was called
- What data was passed
- What results were returned

### 4. Cost Tracking
Monitor API usage:
- Tool call counts
- External API usage
- Resource consumption

### 5. Quality Assurance
Verify correct tool usage:
- Appropriate tool selection
- Valid parameters
- Expected outputs

## Example Trace

### User Query
```
"What properties are available for site 3?"
```

### Langfuse Trace

```yaml
Trace: realtyiq_agent_run
  User ID: session_abc123
  Session ID: chat_session_456
  Duration: 1,234ms
  
  Input: "What properties are available for site 3?"
  
  Observations:
    1. tool_list_properties
       Duration: 156ms
       Input:
         site_id: 3
         page_size: 12
         page: 1
       Output:
         total: 42
         properties: [...]
       
    2. tool_get_site_detail
       Duration: 89ms
       Input:
         domain: "example.com"
       Output:
         site_name: "Example Site"
         [...]
  
  Output: "Here are 42 properties available for site 3..."
  
  Metadata:
    source: web_ui
    tools_used: 2
    tool_names: ["list_properties", "get_site_detail"]
```

## Configuration

### Enable Tool Tracking

Tool tracking is automatically enabled when:
1. `LANGFUSE_ENABLED=true` in `.env`
2. Langfuse credentials are configured
3. Agent runs with observability

### Disable Tool Tracking

To disable while keeping basic tracing:
- Comment out the tool event listeners in `agent_runner.py`
- Or set `LANGFUSE_ENABLED=false`

## Performance Impact

### Minimal Overhead
- Event listeners are lightweight
- Async logging doesn't block execution
- Batched flushing to Langfuse

### Typical Overhead
- <5ms per tool call for logging
- Negligible impact on total execution time
- Async flush happens in background

## Logging Output

### Console Logs

With tool tracking enabled, you'll see:
```
🔧 Tool starting: list_properties
✓ Tool completed: list_properties (156ms)
🔧 Tool starting: get_site_detail
✓ Tool completed: get_site_detail (89ms)
📊 Trace complete: 2 tools used
```

### Log Levels

- `INFO`: Tool start/complete events
- `WARNING`: Tool errors
- `ERROR`: Tracing failures

## Advanced Usage

### Custom Tool Metadata

Add custom metadata to tool calls:
```python
tracer.log_tool_call(
    tool_name="custom_tool",
    args={"param": "value"},
    result="output",
    metadata={"priority": "high", "cache": False}
)
```

### Tool Call Filtering

Filter which tools to track:
```python
# Only track specific tools
TRACKED_TOOLS = ['list_properties', 'get_property_detail']

def on_tool_start(event, meta):
    tool_name = event.tool.name
    if tool_name in TRACKED_TOOLS:
        tracer.log_tool_call(...)
```

## Troubleshooting

### Tool Calls Not Showing

**Check:**
1. Is `LANGFUSE_ENABLED=true`?
2. Are Langfuse credentials valid?
3. Is agent actually using tools? (check console logs)
4. Check Langfuse dashboard for traces

### Tool Event Not Captured

**Possible causes:**
- Event listener registered after agent.run()
- Event name pattern doesn't match
- BeeAI version compatibility

**Solution:**
- Verify event listener registration
- Check BeeAI framework version
- Test with `GlobalTrajectoryMiddleware`

### Partial Tool Data

**If some fields are missing:**
- Tool output might be too large (truncated to 500 chars)
- Tool returned non-serializable data
- Check Langfuse logs for errors

## Comparison: Before vs After

### Before (Basic Tracing)
```
Trace: realtyiq_agent_run
  Input: "Show properties"
  Output: "Here are the properties..."
  Duration: 1.2s
```

**Limitations:**
- ❌ No tool visibility
- ❌ Can't see which tools were used
- ❌ No per-tool timing
- ❌ No tool parameters

### After (With Tool Tracking)
```
Trace: realtyiq_agent_run
  Input: "Show properties"
  ├─ tool_list_properties (156ms)
  │   Input: {site_id: 3, page: 1}
  │   Output: {total: 42, properties: [...]}
  ├─ tool_get_site_detail (89ms)
  │   Input: {domain: "example.com"}
  │   Output: {site_name: "..."}
  Output: "Here are the properties..."
  Duration: 1.2s
```

**Benefits:**
- ✅ Full tool visibility
- ✅ Tool execution order
- ✅ Per-tool timing
- ✅ Input/output for each tool
- ✅ Error tracking per tool

## Related Documentation

- **[OBSERVABILITY.md](OBSERVABILITY.md)** - Complete observability setup
- **[tools.md](tools.md)** - Available tools reference
- **[SPECS.md](SPECS.md)** - Technical specifications

## Summary

✅ **Tool calls are now tracked in Langfuse**  
✅ **Each tool appears as a child observation**  
✅ **Full input/output captured**  
✅ **Performance metrics per tool**  
✅ **Complete execution visibility**  

**View your tool usage**: Observability → Traces → Expand any trace → See tool observations

---

**Last Updated**: February 16, 2026  
**Status**: Active and tracking all tool calls
