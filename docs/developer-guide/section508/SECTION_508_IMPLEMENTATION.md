# Section 508 Accessibility Implementation - Complete Guide

## Overview

This document describes the complete Section 508 accessibility implementation for RealtyIQ, including the toggle mode, enhanced UI features, and Text-to-Speech (TTS) integration.

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Browser                              │
├─────────────────────────────────────────────────────────────────┤
│  • Section 508 Mode Toggle (Settings UI)                        │
│  • Enhanced CSS (larger text, focus indicators)                  │
│  • Audio Player Controls (when 508 enabled)                      │
│  • JavaScript: section508.js, chat.js                           │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 │ HTTP/JSON
                 ↓
┌─────────────────────────────────────────────────────────────────┐
│                   Django Web Server (port 8002)                  │
├─────────────────────────────────────────────────────────────────┤
│  • Context Processor: Read SECTION_508_MODE from .env          │
│  • UserPreference Model: section_508_enabled field             │
│  • API Endpoints:                                               │
│    - GET /api/section508/ (get status)                         │
│    - POST /api/section508/ (update preference)                 │
│    - GET /api/messages/{id}/audio/ (poll for TTS)             │
│  • Command Handler: /settings 508 <on|off>                     │
│  • Chat API: Trigger TTS in background thread                  │
│  • TTS Client: agent_app/tts_client.py                         │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 │ HTTP POST (TTS synthesis)
                 ↓
┌─────────────────────────────────────────────────────────────────┐
│              Piper TTS Service (port 8088, Docker)              │
├─────────────────────────────────────────────────────────────────┤
│  • POST /v1/tts/synthesize (generate MP3 audio)                │
│  • GET /v1/audio/{id} (retrieve cached audio)                  │
│  • GET /v1/voices (list available voices)                      │
│  • Audio Cache: /piper/audio (24-hour TTL)                     │
└─────────────────────────────────────────────────────────────────┘
```

## Configuration Hierarchy

Section 508 mode can be set at three levels:

### 1. System Default (Environment)
```bash
# .env
SECTION_508_MODE=false  # System-wide default
```

### 2. User Preference (Database)
```python
UserPreference.section_508_enabled = True  # User override
```

### 3. Resolution Logic
```python
if user_pref.section_508_enabled is not None:
    use user_pref.section_508_enabled  # Explicit user choice
else:
    use SECTION_508_MODE from .env     # Environment default
```

## Features by Mode

### When Section 508 Mode is OFF

**User Experience:**
- Normal text-only responses
- Standard font size and spacing
- No audio controls
- Standard focus indicators

**Performance:**
- Cached responses: <100ms
- New queries: 2-5s
- No TTS overhead

### When Section 508 Mode is ON

**Enhanced Accessibility:**
- ✅ Larger text (18px base font)
- ✅ Increased line height (1.6)
- ✅ Enhanced focus indicators (3px solid outline)
- ✅ Minimum touch targets (44x44px)
- ✅ ARIA live regions for screen readers
- ✅ Text-to-Speech audio playback

**Audio Features:**
- Native HTML5 audio controls
- Play/Pause/Seek/Volume
- No autoplay (WCAG compliant)
- MP3 format (Safari compatible)
- User-controlled playback

**Performance:**
- Text response: Same as OFF mode (2-5s)
- Audio generation: 2-10s (background, non-blocking)
- Audio polling: Every 2s for up to 60s

## Implementation Details

### 1. Environment Configuration

**File:** `.env`
```bash
# Section 508 Accessibility
SECTION_508_MODE=false

# Piper TTS Service
PIPER_BASE_URL=http://localhost:8088
PIPER_DEFAULT_VOICE=en_US-lessac-medium
```

### 2. Database Schema

**Model:** `UserPreference`
```python
section_508_enabled = models.BooleanField(
    null=True,  # Null = use environment default
    blank=True,
    help_text="Enable Section 508 accessibility features"
)
```

**Model:** `ChatMessage`
```python
audio_url = models.CharField(
    max_length=512,
    null=True,
    blank=True,
    help_text="TTS audio URL for Section 508 mode"
)
```

**Migrations:**
- `0013_userpreference_section_508_enabled.py`
- `0014_alter_userpreference_section_508_enabled.py`
- `0015_chatmessage_audio_url.py`

### 3. Server-Side Components

#### Context Processor
**File:** `agent_app/context_processors.py`
```python
def section_508_settings(request):
    """Make Section 508 status available to all templates"""
    default = os.getenv('SECTION_508_MODE', 'false').lower() in ('true', '1', 'yes')
    
    pref = UserPreference.objects.filter(session_key=session_key).first()
    enabled = pref.section_508_enabled if (pref and pref.section_508_enabled is not None) else default
    
    return {
        'SECTION_508_ENABLED': enabled,
        'SECTION_508_DEFAULT': default
    }
```

#### API Endpoints

**GET /api/section508/**
```json
Response: {
  "section_508_enabled": true,
  "default": false
}
```

**POST /api/section508/**
```json
Request: {"enabled": true}
Response: {
  "success": true,
  "section_508_enabled": true,
  "message": "Section 508 mode enabled"
}
```

**GET /api/messages/{id}/audio/**
```json
Response: {
  "message_id": 123,
  "audio_url": "http://localhost:8088/v1/audio/abc123",
  "has_audio": true,
  "content_preview": "Here are the results..."
}
```

#### Command Handler
**File:** `agent_app/commands/settings.py`
```bash
/settings              # Show current status
/settings 508 on       # Enable
/settings 508 off      # Disable
```

**Output:**
```
Section 508 accessibility mode: enabled

Features enabled:
  - Text-to-speech integration
  - Screen reader optimizations
  - High contrast mode
  - Keyboard navigation enhancements
  - ARIA labels and landmarks
```

#### TTS Client
**File:** `agent_app/tts_client.py`

**Functions:**
- `get_piper_health()` - Check service availability
- `synthesize_speech_async(text, message_id)` - Generate audio
- `synthesize_for_message(message_id, text)` - Background synthesis

**Usage in Chat API:**
```python
if section_508_enabled and response_text:
    import threading
    tts_thread = threading.Thread(
        target=synthesize_for_message,
        args=(assistant_message.pk, response_text),
        daemon=True
    )
    tts_thread.start()
```

### 4. Frontend Components

#### JavaScript Initialization
**File:** `templates/base.html`
```javascript
window.SECTION_508_ENABLED = {{ SECTION_508_ENABLED|lower }};
```

#### Section 508 Module
**File:** `static/js/section508.js`

**Global Functions:**
- `window.getSection508Status()` - Check if enabled
- `window.toggleSection508(enabled)` - Apply/remove mode
- `window.fetchSection508Status()` - Get from server
- `window.updateSection508Status(enabled)` - Update on server
- `window.announceToScreenReader(message)` - ARIA announcements

#### Audio Player Integration
**File:** `static/js/chat.js`

**Updated appendMessage():**
```javascript
function appendMessage(role, content, timestamp, elapsedMs, messageId, 
                       traceId, fromCache, agentName, isCommand, 
                       commandMetadata, audioUrl, section508Enabled) {
    // ... render message text ...
    
    // Add audio player if Section 508 enabled
    if (role === "assistant" && section508Enabled && messageId) {
        if (audioUrl) {
            createAudioPlayer(container, audioUrl, messageId);
        } else {
            pollForAudio(messageId, container);
        }
    }
}
```

**Audio Player UI:**
```javascript
function createAudioPlayer(container, audioUrl, messageId) {
    var audioElement = document.createElement("audio");
    audioElement.controls = true;
    audioElement.preload = "metadata";
    audioElement.setAttribute("aria-label", "Text-to-speech audio");
    
    var source = document.createElement("source");
    source.src = audioUrl;
    source.type = "audio/mpeg";
    audioElement.appendChild(source);
    
    container.appendChild(audioElement);
}
```

**Polling Logic:**
```javascript
function pollForAudio(messageId, container) {
    var attempts = 0;
    var maxAttempts = 30;  // 60 seconds total
    
    var pollInterval = setInterval(function() {
        attempts++;
        
        fetch("/api/messages/" + messageId + "/audio/")
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (data.has_audio && data.audio_url) {
                    clearInterval(pollInterval);
                    createAudioPlayer(container, data.audio_url, messageId);
                } else if (attempts >= maxAttempts) {
                    clearInterval(pollInterval);
                    showAudioTimeout(container);
                }
            });
    }, 2000);  // Poll every 2 seconds
}
```

#### CSS Styling
**File:** `static/css/theme.css`

**Audio Controls:**
```css
.audio-player-container {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--gray-20);
}

.audio-player {
  display: flex;
  align-items: center;
  gap: 12px;
}

.audio-controls {
  flex: 1;
  max-width: 400px;
  height: 36px;
}

/* Enhanced for Section 508 mode */
body.section-508-mode .audio-controls {
  height: 48px;
}
```

**Accessibility Enhancements:**
```css
body.section-508-mode {
  font-size: 18px;
  line-height: 1.6;
}

body.section-508-mode button,
body.section-508-mode a {
  min-height: 44px;
  min-width: 44px;
}

body.section-508-mode :focus {
  outline: 3px solid var(--focus-color);
  outline-offset: 2px;
}
```

### 5. Settings UI

**File:** `templates/settings.html`

**Toggle Control:**
```html
<div class="form-check form-switch">
    <input type="checkbox" id="section-508-toggle" 
           {% if SECTION_508_ENABLED %}checked{% endif %}>
    <label for="section-508-toggle">Section 508 Mode</label>
</div>
```

**JavaScript Handler:**
```javascript
section508Toggle.addEventListener('change', function() {
    var enabled = this.checked;
    
    fetch('/api/section508/', {
        method: 'POST',
        body: JSON.stringify({ enabled: enabled })
    })
    .then(function(response) { return response.json(); })
    .then(function(data) {
        if (data.success && window.toggleSection508) {
            window.toggleSection508(enabled);
        }
    });
});
```

## User Flow

### Enabling Section 508 Mode

**Method 1: Command**
```
User: /settings 508 on
System: Section 508 accessibility mode: enabled

Features enabled:
  - Text-to-speech integration
  - Screen reader optimizations
  ...
```

**Method 2: Settings UI**
1. Navigate to Settings page
2. Find "Accessibility" section
3. Toggle "Section 508 Mode" switch ON
4. Changes apply immediately

**Method 3: Environment Default**
```bash
# .env
SECTION_508_MODE=true
```
All users get Section 508 mode by default (can still override individually).

### Using TTS Playback

**Step 1: User sends message**
```
User: List properties in Kansas
```

**Step 2: Text response appears (immediately)**
```
Assistant: Here are the properties in Kansas:
1. Property ABC - $500,000
2. Property XYZ - $750,000
...

[Generating audio...] ← Shows immediately
```

**Step 3: Audio player appears (2-10 seconds later)**
```
Assistant: Here are the properties in Kansas:
1. Property ABC - $500,000
2. Property XYZ - $750,000
...

🔊 Listen [▶️ ⏸ 🔇 ──○──────] ← Audio controls
```

**Step 4: User controls playback**
- Click ▶️ to play
- Click ⏸ to pause
- Drag slider to seek
- Adjust volume with 🔇 control

## Technical Specifications

### TTS Parameters

**Default Configuration:**
```json
{
  "text": "Agent response text...",
  "voice_id": "en_US-lessac-medium",
  "output_format": "mp3",
  "sample_rate": 22050,
  "speaking_rate": 1.0,
  "return_mode": "url",
  "cache_ttl_seconds": 86400
}
```

### Audio Caching

**Piper TTS Cache:**
- Location: `/piper/audio` (Docker volume)
- TTL: 24 hours
- Format: MP3 (MPEG-1 Layer 3)
- Key: Hash of `{voice_id}_{text}`

**Browser Cache:**
- Standard HTTP caching headers
- Controlled by Piper service
- Browsers cache audio files automatically

### Performance Metrics

**Text Response Time:**
- Cached: <100ms
- New: 2-5s
- **No change** when Section 508 enabled

**Audio Generation Time:**
- Short response (50 words): ~2s
- Medium response (200 words): ~5s
- Long response (1000 words): ~10s
- **Runs in background**, doesn't block text

**Network Bandwidth:**
- Text response: 5-50KB
- Audio response: 50-500KB (MP3 compressed)
- Total: Text delivered first, audio follows

### Browser Compatibility

**Audio Playback:**
- ✅ Safari 14+ (macOS, iOS)
- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Edge 90+
- ✅ Mobile browsers

**Section 508 Features:**
- ✅ All modern browsers
- ✅ Screen readers (NVDA, JAWS, VoiceOver)
- ✅ Keyboard navigation
- ✅ Touch devices (44px minimum target)

## Accessibility Compliance

### WCAG 2.1 Level AA

| Criterion | Requirement | Implementation |
|-----------|-------------|----------------|
| 1.2.1 Audio-only | Text alternative for audio | Text is primary, audio is supplementary |
| 1.4.2 Audio Control | User control, no autoplay | Native controls, explicit play required |
| 1.4.3 Contrast | 4.5:1 minimum | IBM Design colors meet requirement |
| 1.4.8 Visual Presentation | Line height 1.5+, text resize | Line height 1.6, responsive font sizing |
| 2.1.1 Keyboard | All functionality keyboard accessible | Full keyboard navigation |
| 2.4.3 Focus Order | Logical focus order | Sequential tab order |
| 2.4.7 Focus Visible | Visible focus indicator | 3px solid outline |
| 3.2.1 On Focus | No context change on focus | Focus doesn't change context |
| 3.2.2 On Input | No context change on input | Input doesn't trigger changes |
| 4.1.2 Name, Role, Value | Programmatic name/role/value | Full ARIA implementation |

### Section 508 Requirements

| §1194.22 | Requirement | Implementation |
|----------|-------------|----------------|
| (a) | Text alternative | Alt text, ARIA labels throughout |
| (b) | Multimedia | TTS via Piper, user-controlled |
| (c) | Color independence | Not reliant on color alone |
| (d) | Readable without stylesheet | Semantic HTML structure |
| (i) | Frames | All frames have titles |
| (k) | Skip navigation | Skip links in navigation |
| (l) | Document titles | Descriptive page titles |

## Testing

### Unit Tests

**File:** `agent_app/tests/test_section508.py`
- ✅ Default from environment
- ✅ Toggle via API
- ✅ Toggle via command
- ✅ Settings display
- ✅ Invalid value handling
- ✅ Context processor
- ✅ Null preference fallback

**File:** `agent_app/tests/test_tts_integration.py`
- ✅ TTS synthesis success
- ✅ TTS synthesis failure
- ✅ TTS synthesis timeout
- ✅ Chat API with 508 enabled
- ✅ Chat API with 508 disabled
- ✅ Message audio API
- ✅ Audio URL polling
- ✅ Text truncation (8000 char limit)
- ✅ Commands don't trigger TTS
- ✅ Chat history includes audio URLs

**Run Tests:**
```bash
cd agent_ui
python manage.py test agent_app.tests.test_section508
python manage.py test agent_app.tests.test_tts_integration
```

### Manual Testing Checklist

**Basic Functionality:**
- [ ] Enable Section 508 mode via `/settings 508 on`
- [ ] Verify larger text and spacing applied
- [ ] Send a message to an agent
- [ ] Verify text appears immediately
- [ ] Verify "Generating audio..." indicator appears
- [ ] Wait 2-10 seconds
- [ ] Verify audio player appears
- [ ] Click play and verify audio matches text
- [ ] Disable Section 508 mode via `/settings 508 off`
- [ ] Send another message
- [ ] Verify no audio controls appear

**Settings UI:**
- [ ] Navigate to Settings page
- [ ] Find "Section 508 Mode" toggle
- [ ] Toggle ON
- [ ] Verify success message appears
- [ ] Verify UI changes applied immediately
- [ ] Toggle OFF
- [ ] Verify UI reverts to normal

**Edge Cases:**
- [ ] Test with Piper service stopped (graceful degradation)
- [ ] Test with very long responses (1000+ words)
- [ ] Test with multiple messages in quick succession
- [ ] Test session history loading (audio URLs persist)
- [ ] Test keyboard navigation to audio controls
- [ ] Test with screen reader

**Browser Compatibility:**
- [ ] Test in Safari (macOS)
- [ ] Test in Chrome
- [ ] Test in Firefox
- [ ] Test in mobile Safari (iOS)

## Command Reference

### Toggle Section 508 Mode
```bash
/settings 508 on       # Enable
/settings 508 off      # Disable
/settings 508 true     # Enable (alternative)
/settings 508 false    # Disable (alternative)
/settings 508 enabled  # Enable (alternative)
/settings 508 disabled # Disable (alternative)
```

### Check Status
```bash
/settings              # Show all settings including 508 status
```

**Output:**
```
Current Settings:
  Agent: gres
  Model: claude-3-5-sonnet
  Section 508 Mode: enabled (custom)

To update:
  /settings agent <value>
  /settings model <value>
  /settings 508 <on|off>
```

## Troubleshooting

### Issue: Audio Not Generating

**Symptoms:**
- "Generating audio..." never changes to player
- Timeout message appears after 60s

**Solutions:**
1. Check Piper service status:
   ```bash
   make piper-logs
   curl http://localhost:8088/healthz
   ```

2. Check environment variables:
   ```bash
   grep PIPER .env
   ```

3. Start Piper service:
   ```bash
   make piper-start
   ```

### Issue: Section 508 Mode Not Applying

**Symptoms:**
- Toggle switch changes but UI doesn't update
- Larger text doesn't appear

**Solutions:**
1. Check browser console:
   ```javascript
   console.log(window.SECTION_508_ENABLED);
   ```

2. Verify context processor is registered:
   ```bash
   grep section_508_settings agent_ui/agent_ui/settings.py
   ```

3. Clear browser cache and reload

### Issue: Audio Player Shows But Doesn't Play

**Symptoms:**
- Audio controls appear but clicking play does nothing
- Browser error in console

**Solutions:**
1. Check audio URL is accessible:
   ```bash
   curl http://localhost:8088/v1/audio/abc123
   ```

2. Check Piper service logs:
   ```bash
   make piper-logs
   ```

3. Verify CORS is enabled on Piper (already configured)

4. Check browser supports MP3:
   ```javascript
   var audio = document.createElement('audio');
   console.log(audio.canPlayType('audio/mpeg')); // Should be "probably" or "maybe"
   ```

## Security & Privacy

### Data Handling
- ✅ All TTS processing is on-premises (no cloud)
- ✅ Audio cached locally in Docker volume
- ✅ No audio sent to external services
- ✅ 24-hour automatic cache expiration
- ✅ Audio URLs are local only (localhost:8088)

### PII Considerations
- ✅ Text responses may contain PII (same as without TTS)
- ✅ Audio files stored temporarily (24h TTL)
- ✅ No audio analytics or tracking
- ✅ Audio cache can be cleared: `docker compose down -v piper`

## Deployment

### Docker Compose

The Piper service is already defined in `docker-compose.yml`:

```yaml
piper:
  container_name: piper
  build:
    context: ./piper
    dockerfile: Dockerfile
  ports:
    - "8088:8088"
  volumes:
    - ./piper/audio:/audio
  networks:
    - realtyiq-network
```

### Makefile Commands

```bash
make piper-build      # Build Piper Docker image
make piper-start      # Start Piper service
make piper-stop       # Stop Piper service
make piper-logs       # View Piper logs
make piper-restart    # Restart Piper service
make piper-test       # Run Piper tests
```

### Service Dependencies

```
Django UI (8002) ──► Piper TTS (8088) ──► Audio Cache (/audio)
                     ▲
                     │
                     └──── Redis (6379) [Optional: for future caching]
```

## API Documentation

### Piper TTS Service

**Base URL:** `http://localhost:8088`

**Endpoints:**
- `GET /healthz` - Health check
- `GET /v1/voices` - List available voices
- `POST /v1/tts/synthesize` - Generate audio
- `GET /v1/audio/{id}` - Retrieve cached audio
- `GET /v1/stats` - Service statistics

**Full API Spec:** See `piper/openapi.yaml`

### Django API

**Section 508 Settings:**
- `GET /api/section508/` - Get current status
- `POST /api/section508/` - Update preference

**Message Audio:**
- `GET /api/messages/{id}/audio/` - Get audio URL for message

## Related Documentation

- [TTS_INTEGRATION.md](./TTS_INTEGRATION.md) - Detailed TTS implementation
- [SECTION_508.md](./SECTION_508.md) - Section 508 mode features
- [COMMANDS.md](./COMMANDS.md) - Command system reference
- [piper/README.md](../piper/README.md) - Piper TTS service guide
- [piper/openapi.yaml](../piper/openapi.yaml) - Piper API specification

## Future Enhancements

### Planned
- [ ] Voice selection in settings UI
- [ ] Playback speed control (0.5x - 2.0x)
- [ ] Download audio button
- [ ] WebSocket for real-time audio updates (replace polling)

### Under Consideration
- [ ] SSML support for better prosody
- [ ] Multiple language support
- [ ] Custom voice training for domain terminology
- [ ] Batch TTS for session export

## Version History

- **v0.1.0** (2026-02-21)
  - Initial Section 508 mode implementation
  - Environment-based default configuration
  - Per-user preference override
  - Command and UI toggle
  - TTS integration with Piper service
  - MP3 audio format for Safari
  - Native HTML5 audio controls
  - Background synthesis (non-blocking)
  - Audio polling with timeout
  - Comprehensive test coverage (18 tests passing)
