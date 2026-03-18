# Langfuse Observability Setup

## Overview

RealtyIQ uses [Langfuse](https://langfuse.com) for comprehensive LLM observability, providing:

- 📊 **Tracing**: Track every LLM call with full context
- 💰 **Cost Tracking**: Monitor token usage and costs
- ⏱️ **Performance**: Measure latency and response times
- 🐛 **Debugging**: Inspect prompts, responses, and tool calls
- 📈 **Analytics**: Analyze user feedback and success rates
- 🔍 **Search & Filter**: Find specific interactions quickly

## Configuration

Langfuse is configured via environment variables in `.env`:

```bash
# Enable/disable observability
LANGFUSE_ENABLED=true

# Langfuse API credentials (get from https://cloud.langfuse.com)
LANGFUSE_PUBLIC_KEY="pk-lf-..."
LANGFUSE_SECRET_KEY="sk-lf-..."
LANGFUSE_HOST="https://us.cloud.langfuse.com"

# Dashboard URL (for quick access)
OBSERVABILITY_DASHBOARD="https://us.cloud.langfuse.com/project/YOUR_PROJECT_ID"
```

### Getting Your API Keys

1. Sign up at https://cloud.langfuse.com
2. Create a new project
3. Go to **Settings** → **API Keys**
4. Copy your public and secret keys
5. Add them to `.env`

## Installation

Langfuse SDK is included in `requirements.txt`:

```bash
pip install -r requirements.txt
```

This installs `langfuse>=2.0.0` along with other dependencies.

## Features

### 1. Automatic Tracing

Every agent run is automatically traced with:
- **Input**: User prompt
- **Output**: Agent response
- **Metadata**: Session ID, user ID, source (CLI/web)
- **Timing**: Duration in milliseconds
- **Model**: LLM model name used

### 2. Session Tracking

All interactions are grouped by session:
- Web UI: Django session ID
- CLI: Generated session ID per terminal session
- View complete conversation history in Langfuse

### 3. User Feedback Integration

Thumbs up/down feedback from the UI is sent to Langfuse:
- ✅ Positive feedback → score 1.0
- ❌ Negative feedback → score 0.0
- Comments are attached to traces

### 4. Cost Tracking

(TODO: Requires token counting integration)
- Track token usage per request
- Calculate costs based on model pricing
- Monitor budget and usage trends

### 5. Error Tracking

Failed requests are logged with:
- Error type and message
- Stack traces
- Failed prompt and context

## Usage

### CLI Agent (`run_agent.py`)

Tracing is automatic when enabled:

```bash
python run_agent.py
```

Output shows Langfuse status:
```
Using LLM: anthropic:claude-sonnet-4-5
✓ Langfuse observability enabled
  Dashboard: https://us.cloud.langfuse.com/project/...

RealtyIQ> List all properties
...
```

### Web UI

Tracing happens automatically in the background:

1. User sends chat message
2. Agent processes request (traced)
3. Response displayed with trace ID
4. User can give feedback (sent to Langfuse)

### Programmatic Usage

For custom integrations:

```python
from observability import trace_agent_run

async def my_agent_function(prompt):
    with trace_agent_run(
        user_id="user123",
        session_id="session456",
        metadata={"custom": "data"}
    ) as tracer:
        # Log input
        tracer.log_input(prompt, model="claude-sonnet-4-5")
        
        # Run agent
        result = await agent.run(prompt)
        
        # Log output
        tracer.log_output(result.text)
        
        # Log specific LLM calls
        tracer.log_llm_call(
            model="claude-sonnet-4-5",
            prompt=prompt,
            response=result.text,
            tokens_used=500,
            cost=0.015
        )
        
        # Log tool calls
        tracer.log_tool_call(
            tool_name="list_properties",
            args={"site_id": 3},
            result=properties_list
        )
        
        # Log errors
        try:
            # ... code ...
        except Exception as e:
            tracer.log_error(e)
            raise
        
        # Add custom metadata
        tracer.add_metadata(
            custom_field="value",
            another_field=123
        )
```

### Decorator Usage

Trace any function automatically:

```python
from observability import trace_function

@trace_function("process_properties")
def process_properties(data):
    # Function code
    return result

# Automatically traced when called
result = process_properties(data)
```

### Logging Feedback

```python
from observability import log_feedback

# Log positive feedback
log_feedback(
    trace_id="trace-abc-123",
    score=1.0,
    comment="Great response!"
)

# Log negative feedback
log_feedback(
    trace_id="trace-abc-123",
    score=0.0,
    comment="Not helpful"
)
```

## Dashboard Access

### Via Web Browser

Open your dashboard URL (from `.env`):

```
https://us.cloud.langfuse.com/project/YOUR_PROJECT_ID
```

### Key Dashboards

1. **Traces**: View all LLM interactions
2. **Sessions**: Group by conversation
3. **Users**: See per-user activity
4. **Models**: Compare model performance
5. **Scores**: Analyze feedback
6. **Analytics**: Usage trends and costs

### Useful Filters

- **By Session**: See full conversations
- **By User**: Track specific users
- **By Feedback**: Find highly-rated or problematic responses
- **By Date Range**: Analyze time periods
- **By Model**: Compare different LLMs
- **By Error**: Debug failures

## Monitoring & Alerts

### Key Metrics to Track

1. **Response Time**
   - Average: Should be < 3s
   - P95: Should be < 5s
   - P99: Should be < 10s

2. **Error Rate**
   - Target: < 1%
   - Alert if > 5%

3. **Token Usage**
   - Track daily/weekly trends
   - Set budget alerts

4. **User Satisfaction**
   - % Positive feedback
   - Target: > 80%

5. **Cost per Query**
   - Monitor average cost
   - Compare models

### Setting Up Alerts

In Langfuse dashboard:
1. Go to **Settings** → **Alerts**
2. Create alert rules
3. Configure thresholds
4. Set notification channels (email, Slack)

## Performance Optimization

### Reducing Latency

1. **Streaming Responses**: (TODO) Implement streaming
2. **Caching**: Cache frequent queries
3. **Parallel Calls**: Use async for tool calls
4. **Model Selection**: Use faster models for simple queries

### Reducing Costs

1. **Prompt Engineering**: Shorter, clearer prompts
2. **Model Selection**: Use cheaper models when appropriate
3. **Caching**: Avoid redundant LLM calls
4. **Output Limits**: Set max tokens

## Debugging

### Finding Slow Requests

1. Go to **Traces**
2. Sort by **Duration** (descending)
3. Inspect slow traces
4. Check tool call times
5. Optimize bottlenecks

### Finding Errors

1. Go to **Traces**
2. Filter by **Level: ERROR**
3. Review error messages
4. Check input prompts
5. Fix underlying issues

### Analyzing Low-Rated Responses

1. Go to **Scores**
2. Filter by **Value: 0.0** (negative)
3. Read user comments
4. Review prompts and responses
5. Improve system prompts or tools

## Best Practices

### 1. Meaningful Session IDs

Use consistent session IDs:
```python
# Good
session_id = f"user_{user_id}_session_{session_num}"

# Bad
session_id = random_uuid()  # Can't track conversations
```

### 2. Rich Metadata

Add context to traces:
```python
metadata = {
    "source": "web_ui",
    "page": "dashboard",
    "user_role": "admin",
    "feature": "property_search"
}
```

### 3. Detailed Error Logging

Include full context:
```python
try:
    result = agent.run(prompt)
except Exception as e:
    tracer.log_error(e)
    tracer.add_metadata(
        error_context={
            "prompt": prompt,
            "stack_trace": traceback.format_exc(),
            "tools_available": [t.name for t in tools]
        }
    )
    raise
```

### 4. Regular Review

- Daily: Check error rate
- Weekly: Review feedback
- Monthly: Analyze costs and trends

## Privacy & Security

### Data Handling

Langfuse traces contain:
- ✅ Prompts and responses
- ✅ Metadata
- ✅ Tool calls
- ❌ NOT raw API keys or secrets

### PII Considerations

- Don't log sensitive user data
- Redact PII from traces if needed
- Use Langfuse's data retention settings
- Follow your organization's policies

### Disabling Observability

To disable Langfuse:

```bash
# In .env
LANGFUSE_ENABLED=false
```

Application will run normally without tracing.

## Troubleshooting

### "Langfuse not installed"

```bash
pip install langfuse>=2.0.0
```

### "Failed to initialize Langfuse"

Check:
1. API keys are correct
2. Host URL is valid
3. Network connectivity
4. Firewall/proxy settings

### "Failed to flush Langfuse"

Usually non-critical:
- Traces are buffered
- Will retry on next call
- Check network logs

### Traces not appearing

1. Verify `LANGFUSE_ENABLED=true`
2. Check API keys
3. Wait a few seconds (buffering)
4. Refresh Langfuse dashboard
5. Check application logs

## Advanced Usage

### Custom Trace Names

```python
with trace_agent_run(...) as tracer:
    tracer.trace.update(name="custom_operation_name")
```

### Multiple LLM Calls

```python
with trace_agent_run(...) as tracer:
    # First LLM call
    tracer.log_llm_call(...)
    
    # Second LLM call
    tracer.log_llm_call(...)
```

### Nested Spans

```python
with trace_agent_run(...) as tracer:
    # Parent operation
    span1 = tracer.trace.span(name="data_fetch")
    # ... fetch data ...
    span1.end()
    
    # Child operation
    span2 = tracer.trace.span(name="data_process")
    # ... process data ...
    span2.end()
```

## Integration with Other Tools

### Prometheus

Export metrics to Prometheus:
- Query Langfuse API
- Generate /metrics endpoint
- Scrape with Prometheus

### Grafana

Visualize metrics:
- Connect to Langfuse/Prometheus
- Create custom dashboards
- Set up alerts

### Slack

Get notifications:
- Use Langfuse webhooks
- Send to Slack channel
- Alert on errors/feedback

## Resources

- **Langfuse Docs**: https://langfuse.com/docs
- **API Reference**: https://api.reference.langfuse.com
- **SDK GitHub**: https://github.com/langfuse/langfuse-python
- **Community**: https://langfuse.com/discord

## Support

For issues:
1. Check logs: `grep -i langfuse <logfile>`
2. Verify `.env` configuration
3. Test with simple example
4. Review Langfuse status page
5. Contact Langfuse support

---

**Status**: ✅ Fully configured and operational

Langfuse provides complete visibility into your RealtyIQ agent's behavior, performance, and costs.
