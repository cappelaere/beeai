# Langfuse Observability - Quick Start

## 5-Minute Setup

### 1. Install Dependencies

```bash
pip install langfuse>=2.0.0
```

(Already included in `requirements.txt`)

### 2. Get Langfuse Credentials

1. Go to https://cloud.langfuse.com
2. Create account (free tier available)
3. Create a new project
4. Copy your API keys from **Settings** → **API Keys**

### 3. Configure Environment

Your `.env` already has Langfuse configured:

```bash
LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY="pk-lf-..."
LANGFUSE_SECRET_KEY="sk-lf-..."
LANGFUSE_HOST="https://us.cloud.langfuse.com"
OBSERVABILITY_DASHBOARD="https://us.cloud.langfuse.com/project/YOUR_PROJECT_ID"
```

✅ **Already configured!** Just verify the keys are correct.

### 4. Test It

#### Test CLI Agent

```bash
python run_agent.py
```

You should see:
```
✓ Langfuse observability enabled
  Dashboard: https://us.cloud.langfuse.com/project/...
```

Try a query:
```
RealtyIQ> List all properties
```

#### Test Web UI

```bash
cd agent_ui
uvicorn agent_ui.asgi:application --port 8002
```

Open http://localhost:8002 and send a chat message.

### 5. View Dashboard

Open your dashboard URL:

```
https://us.cloud.langfuse.com/project/YOUR_PROJECT_ID
```

You should see:
- ✅ Traces from your interactions
- ✅ Session information
- ✅ Timing data
- ✅ User feedback (after giving thumbs up/down)

## What's Tracked?

### Automatic

- 📊 **Every LLM call** with full context
- ⏱️ **Response times** in milliseconds
- 🔍 **Prompts and responses** (full text)
- 👤 **User and session IDs** for tracking
- 📍 **Source** (CLI vs Web UI)

### Manual (via UI)

- 👍 **Thumbs up/down** feedback
- 💬 **Comments** on responses
- ⭐ **Ratings** and scores

## Dashboard Features

### Traces Tab
View all LLM interactions:
- Filter by session, user, date
- Search by prompt text
- Sort by duration, cost
- Click to see full details

### Sessions Tab
See conversation threads:
- Group messages by session
- View full context
- Track multi-turn conversations

### Scores Tab
Analyze feedback:
- See all rated responses
- Filter by positive/negative
- Read user comments
- Identify patterns

### Analytics Tab
Usage metrics:
- Daily/weekly trends
- Token usage
- Average response time
- Error rates

## Common Tasks

### Find a Specific Conversation

1. Go to **Sessions**
2. Filter by date range
3. Search by user ID or session ID
4. Click to expand

### Debug a Slow Response

1. Go to **Traces**
2. Sort by **Duration** (desc)
3. Click slow trace
4. Check:
   - LLM latency
   - Tool call times
   - Network delays

### See What Users Like

1. Go to **Scores**
2. Filter **Value = 1.0** (positive)
3. Read successful interactions
4. Identify patterns
5. Improve prompts

### Check Errors

1. Go to **Traces**
2. Filter **Level = ERROR**
3. Review error messages
4. Fix underlying issues

## Quick Checks

### ✅ Is it Working?

```python
# Run this in Python
from observability import is_enabled

if is_enabled():
    print("✓ Langfuse is enabled")
else:
    print("✗ Langfuse is disabled")
```

### ✅ Can I Connect?

```python
# Test connection
from observability import get_langfuse_client

client = get_langfuse_client()
if client:
    print("✓ Connected to Langfuse")
    client.flush()  # Force sync
else:
    print("✗ Cannot connect")
```

### ✅ Are Traces Appearing?

1. Send a test message in CLI or Web UI
2. Wait 5 seconds
3. Refresh Langfuse dashboard
4. Should see new trace

## Troubleshooting

### Not Seeing Traces?

**Check 1**: Is it enabled?
```bash
grep LANGFUSE_ENABLED .env
# Should show: LANGFUSE_ENABLED=true
```

**Check 2**: Are keys valid?
```bash
# Try running agent - should see confirmation
python run_agent.py
```

**Check 3**: Wait and refresh
- Traces are buffered
- May take 5-10 seconds
- Refresh dashboard

### "ImportError: No module named langfuse"

```bash
pip install langfuse>=2.0.0
```

### Connection Errors

1. Check internet connection
2. Verify `LANGFUSE_HOST` URL
3. Check firewall/proxy settings
4. Try different network

## Disable Observability

To turn off Langfuse:

```bash
# In .env
LANGFUSE_ENABLED=false
```

Or comment out:
```bash
# LANGFUSE_ENABLED=true
```

Application works normally without it.

## Next Steps

1. ✅ Verify traces appear in dashboard
2. ✅ Try giving feedback in Web UI
3. ✅ Explore different dashboard views
4. ✅ Set up alerts (optional)
5. ✅ Review cost tracking (optional)

## Full Documentation

See `docs/OBSERVABILITY.md` for:
- Advanced usage
- Custom tracing
- Performance tips
- Best practices
- Privacy considerations

## Support

- **Langfuse Docs**: https://langfuse.com/docs
- **Discord**: https://langfuse.com/discord
- **Issues**: Check application logs

---

**Status**: ✅ Ready to use!

Langfuse is now tracking all your RealtyIQ agent interactions.
