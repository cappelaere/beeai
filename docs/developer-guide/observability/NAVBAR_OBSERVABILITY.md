# Langfuse Dashboard in Navigation

## Overview

The Langfuse observability dashboard is now accessible directly from the left navigation bar.

## Location

**Left Navbar** → **Observability** (between Dashboard and Start Chat)

## Features

### Visual Indicators

1. **Chart Icon**: Bar chart icon indicates analytics/observability
2. **External Link Icon**: Small arrow icon shows it opens in new tab
3. **Purple Accent**: Left border highlights observability section
4. **Hover Effect**: Purple tint on hover for visual feedback

### Behavior

- **Opens in New Tab**: Dashboard opens in separate tab to keep your work context
- **Conditional Display**: Only shows when Langfuse is enabled
- **Direct Access**: No need to remember or bookmark the dashboard URL

## Configuration

The link appears automatically when:

1. **Langfuse is enabled** in `.env`:
   ```bash
   LANGFUSE_ENABLED=true
   ```

2. **Dashboard URL is set**:
   ```bash
   OBSERVABILITY_DASHBOARD="https://us.cloud.langfuse.com/project/YOUR_PROJECT_ID"
   ```

If either is missing or disabled, the link won't appear in the navbar.

## Usage

### Quick Access

1. Click **Observability** in left navbar
2. Dashboard opens in new tab
3. View traces, sessions, scores, analytics
4. Return to RealtyIQ tab to continue work

### What You'll See

When you click the Observability link, you'll be taken to your Langfuse dashboard where you can:

- **View Traces**: See all LLM interactions
- **Analyze Sessions**: Review conversation threads
- **Check Scores**: View user feedback (thumbs up/down)
- **Monitor Performance**: Response times, costs, errors
- **Search & Filter**: Find specific interactions

## Implementation Details

### Context Processor

Added `agent_app/context_processors.py`:
```python
def observability_settings(request):
    """Add Langfuse dashboard URL to all templates"""
    langfuse_enabled = os.getenv("LANGFUSE_ENABLED", "false").lower() == "true"
    dashboard_url = os.getenv("OBSERVABILITY_DASHBOARD", "")
    
    return {
        'langfuse_enabled': langfuse_enabled,
        'langfuse_dashboard_url': dashboard_url if langfuse_enabled else None,
    }
```

### Template Code

In `base.html`:
```django
{% if langfuse_dashboard_url %}
<a href="{{ langfuse_dashboard_url }}" 
   class="nav-link" 
   target="_blank" 
   rel="noopener noreferrer" 
   title="Open Langfuse Observability Dashboard">
    <span class="nav-icon">
        <!-- Bar chart icon -->
    </span>
    <span class="nav-label">Observability</span>
    <!-- External link icon -->
</a>
{% endif %}
```

### Styling

Special styling in `theme.css`:
```css
/* Purple left border for observability link */
.nav-link[target="_blank"][title*="Observability"] {
  border-left: 3px solid #6366f1;
  padding-left: calc(1rem - 3px);
}

/* Purple hover effect */
.nav-link[target="_blank"][title*="Observability"]:hover {
  background: rgba(99, 102, 241, 0.08);
  border-left-color: #4f46e5;
}
```

## Security

### `rel="noopener noreferrer"`

The link includes security attributes:
- `noopener`: Prevents new page from accessing `window.opener`
- `noreferrer`: Doesn't send referrer information

### HTTPS Only

The dashboard URL must use HTTPS (Langfuse Cloud enforces this).

## Customization

### Change Label

Edit `base.html`:
```django
<span class="nav-label">Your Label Here</span>
```

### Change Icon

Replace the SVG in `base.html`:
```django
<span class="nav-icon">
    <!-- Your custom SVG icon -->
</span>
```

### Change Accent Color

Edit `theme.css`:
```css
.nav-link[target="_blank"][title*="Observability"] {
  border-left: 3px solid #your-color;
}
```

### Change Position

Move the entire `<a>` block to different location in navbar in `base.html`.

## Troubleshooting

### Link Not Appearing

**Check 1**: Is Langfuse enabled?
```bash
grep LANGFUSE_ENABLED .env
# Should show: LANGFUSE_ENABLED=true
```

**Check 2**: Is dashboard URL set?
```bash
grep OBSERVABILITY_DASHBOARD .env
# Should show: OBSERVABILITY_DASHBOARD=https://...
```

**Check 3**: Restart server
```bash
# Stop server (Ctrl+C)
# Start again
uvicorn agent_ui.asgi:application --port 8002
```

**Check 4**: Clear browser cache
- Hard refresh: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows/Linux)

### Link Goes to Wrong Dashboard

Update `.env`:
```bash
OBSERVABILITY_DASHBOARD="https://us.cloud.langfuse.com/project/YOUR_CORRECT_PROJECT_ID"
```

Then restart server.

### 404 or Access Denied

1. Verify project ID in URL is correct
2. Check you're logged into Langfuse
3. Verify you have access to the project
4. Try logging in directly at https://cloud.langfuse.com

## Benefits

### For Developers

- 🚀 **Instant Access**: No need to bookmark or search for dashboard
- 🔍 **Quick Debugging**: Jump to traces immediately
- 📊 **Live Monitoring**: Check performance while developing
- 🐛 **Error Investigation**: See errors in real-time

### For Admins

- 📈 **Usage Analytics**: Monitor system health
- 💰 **Cost Tracking**: Keep eye on token consumption
- 👥 **User Behavior**: Understand how users interact
- 🎯 **Quality Control**: Track satisfaction metrics

### For Product Managers

- 📊 **Dashboard Visibility**: Always available in UI
- 🎯 **Data-Driven Decisions**: Easy access to metrics
- 💡 **Feature Insights**: See what users actually use
- 🔄 **Continuous Improvement**: Track impact of changes

## Related Documentation

- **Setup Guide**: `docs/OBSERVABILITY.md`
- **Quick Start**: `docs/OBSERVABILITY_QUICKSTART.md`
- **Test Script**: `python test_observability.py`
- **Main Setup**: `OBSERVABILITY_SETUP.md`

## Future Enhancements

Potential improvements:
- 🔔 Badge with unread error count
- 📊 Mini metrics preview on hover
- 🎨 Custom theme matching RealtyIQ colors
- 🔗 Deep links to specific traces
- 📱 Mobile-optimized dashboard view

---

**Status**: ✅ **Active**

The Observability link is now permanently visible in the navigation when Langfuse is enabled, providing one-click access to your observability dashboard.
