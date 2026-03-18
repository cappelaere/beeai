# Section 508 TTS Integration

## Overview

When Section 508 Mode is enabled, RealtyIQ provides optional voice playback for all agent responses using the on-prem Piper TTS service. Audio is user-controlled (no autoplay) and consistent with the text transcript.

## System Flow

### 1. Agent Response Generation
```
User Input → Agent Processing → Final Text Response
```

The agent generates the complete text response first, which is the source of truth.

### 2. Section 508 Check
```python
if section_508_enabled and response_text:
    # Trigger TTS synthesis in background
    synthesize_for_message(message_id, response_text)
```

The system checks if Section 508 mode is enabled for the user. If enabled, TTS synthesis is triggered **asynchronously** to avoid blocking the text response.

### 3. Text Response Delivery
```
Return text immediately → User sees response in <100ms
```

The text response is returned immediately to the frontend, regardless of TTS status. This ensures the user gets the information without waiting for audio generation.

### 4. Background TTS Synthesis
```
Background Thread → Piper TTS → Audio File → Update Database
```

TTS synthesis happens in a background thread:
1. Markdown is converted to plain text (removes ##, **, `, etc.)
2. Plain text is sent to Piper TTS service (`POST /v1/tts/synthesize`)
3. Piper generates WAV audio (universally compatible, native format)
4. Audio is cached and URL is returned
5. `ChatMessage.audio_url` is updated in the database

**Note:** The visual display still shows markdown formatting, but the audio speaks natural plain text without markdown syntax.

### 5. Audio Delivery to Frontend
```
Frontend polls → Audio URL available → Display audio player
```

The frontend polls the `/api/messages/{id}/audio/` endpoint every 2 seconds for up to 60 seconds. When audio is ready, native HTML5 audio controls are displayed.

## Implementation Details

### Backend Components

#### 1. TTS Client (`agent_app/tts_client.py`)

**Functions:**
- `get_piper_health()` - Check if Piper service is available
- `synthesize_speech_async()` - Generate audio and return URL
- `synthesize_for_message()` - Update database with audio URL

**Configuration:**
```python
PIPER_BASE_URL = os.getenv('PIPER_BASE_URL', 'http://localhost:8088')
DEFAULT_VOICE_ID = os.getenv('PIPER_DEFAULT_VOICE', 'en_US-lessac-medium')
```

**Markdown Processing:**
```python
# Convert markdown to plain text first
from agent_app.markdown_utils import markdown_to_plain_text
plain_text = markdown_to_plain_text(response_text)
```

**TTS Request:**
```python
{
    "text": plain_text[:8000],  # Plain text, no markdown
    "voice_id": "en_US-lessac-medium",
    "return_mode": "url",
    "cache_ttl_seconds": 86400  # 24 hour cache
}
```

#### 2. Chat API Integration (`agent_app/views.py`)

**Section 508 Check:**
```python
# Get user preference or environment default
pref = UserPreference.objects.filter(session_key=session_key).first()
section_508_enabled = pref.section_508_enabled if (pref and pref.section_508_enabled is not None) else default_508
```

**Async TTS Trigger:**
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

**Response:**
```json
{
  "response": "Agent response text...",
  "message_id": 123,
  "audio_url": null,
  "section_508_enabled": true
}
```

#### 3. Audio Polling API (`/api/messages/{id}/audio/`)

Allows frontend to check if audio has been generated:

**Response:**
```json
{
  "message_id": 123,
  "audio_url": "http://localhost:8088/v1/audio/abc123",
  "has_audio": true,
  "content_preview": "Here are the properties..."
}
```

#### 4. Database Model (`ChatMessage`)

Added `audio_url` field:
```python
audio_url = models.CharField(
    max_length=512,
    null=True,
    blank=True,
    help_text="TTS audio URL for Section 508 mode"
)
```

### Frontend Components

#### 1. Updated `appendMessage()` Function

New parameters:
- `audioUrl` - TTS audio URL (may be null initially)
- `section508Enabled` - Whether Section 508 mode is active

```javascript
appendMessage(
    role,
    content,
    timestamp,
    elapsedMs,
    messageId,
    traceId,
    fromCache,
    agentName,
    isCommand,
    commandMetadata,
    audioUrl,              // NEW
    section508Enabled      // NEW
);
```

#### 2. Audio Player Creation

When Section 508 is enabled:

```javascript
if (role === "assistant" && section508Enabled && messageId) {
    if (audioUrl) {
        // Show player immediately
        createAudioPlayer(container, audioUrl, messageId);
    } else {
        // Show loading state and poll
        pollForAudio(messageId, container);
    }
}
```

#### 3. Polling Logic

Polls every 2 seconds for up to 60 seconds (30 attempts):

```javascript
function pollForAudio(messageId, container) {
    var attempts = 0;
    var maxAttempts = 30;
    
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
                    container.innerHTML = '<div class="audio-error">Audio generation timed out</div>';
                }
            });
    }, 2000);
}
```

#### 4. Audio Player UI

Native HTML5 audio controls with accessibility:

```html
<div class="audio-player">
    <span class="audio-label">
        <svg>🔊</svg>Listen
    </span>
    <audio controls preload="metadata" aria-label="Text-to-speech audio">
        <source src="http://localhost:8088/v1/audio/abc123" type="audio/mpeg">
    </audio>
</div>
```

### CSS Styling (`theme.css`)

**Audio Player:**
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

**Loading States:**
```css
.audio-loading {
  display: flex;
  align-items: center;
  gap: 8px;
  animation: spin 1s linear infinite;
}

.audio-error {
  color: var(--red-50);
  font-size: 0.875rem;
}
```

## User Experience

### When Section 508 Mode is OFF
- Normal text-only responses
- No TTS generation or audio controls
- Standard chat experience

### When Section 508 Mode is ON

**For each assistant message:**

1. **Text appears immediately** (within 100-200ms for cached, 2-5s for new queries)
2. **"Generating audio..." indicator appears** below the message
3. **Audio player appears** when synthesis completes (typically 2-10 seconds)
4. **User can click play/pause** to listen at their convenience

**Audio Controls:**
- ▶️ Play/Pause (native browser controls)
- 🔇 Volume (native browser controls)
- ⏩ Seek bar (native browser controls)
- No autoplay - user must explicitly click play

## Configuration

### Environment Variables

```bash
# .env

# Enable Section 508 mode by default
SECTION_508_MODE=true

# Piper TTS service URL
PIPER_BASE_URL=http://localhost:8088

# Default voice for synthesis
PIPER_DEFAULT_VOICE=en_US-lessac-medium
```

### User Preferences

Users can override the environment default:

```bash
# Enable for current user
/settings 508 on

# Disable for current user
/settings 508 off
```

## Performance

### Text Response Time
- **Cached**: <100ms (no change from normal mode)
- **New Query**: 2-5s (no change from normal mode)

### Audio Generation Time
- **Typical**: 2-5 seconds for average response (100-500 words)
- **Long Response**: 5-10 seconds (1000+ words)
- **Cached Audio**: Instant (if same text synthesized before)

**Key Point:** Text is never blocked by audio generation. Audio happens asynchronously.

### Network Requirements
- Text response: ~5-50KB
- Audio response: ~50-500KB (MP3 compressed)
- Total: Text + Audio delivered separately

### Caching Strategy
- **Piper TTS**: 24-hour cache for audio files
- **Browser**: Standard HTTP caching headers
- **Database**: `audio_url` stored with message for quick retrieval

## Error Handling

### Piper Service Unavailable
- Text response still delivered normally
- Audio loading indicator remains visible
- After 30 poll attempts (60s), shows "Audio unavailable" message
- User can continue using text responses without interruption

### TTS Synthesis Failure
- Logged server-side: `logger.error(f"TTS synthesis failed for message {message_id}")`
- Frontend shows "Audio generation timed out" after 60s
- Does not affect text response delivery

### Network Timeout
- 30-second timeout for TTS synthesis request
- Frontend polls for 60 seconds before giving up
- Graceful degradation to text-only mode

## Accessibility Features

### WCAG 2.1 Compliance
- ✅ **1.2.1 Audio-only**: Text is always primary; audio is supplementary
- ✅ **1.4.2 Audio Control**: User-controlled (no autoplay)
- ✅ **2.1.1 Keyboard**: All controls keyboard-accessible
- ✅ **4.1.2 Name, Role, Value**: Proper ARIA labels on audio element

### Screen Reader Announcements
When audio becomes available:
```javascript
window.announceToScreenReader('Audio available for this response');
```

### Keyboard Navigation
- Tab to audio controls
- Space/Enter to play/pause
- Arrow keys to seek (native browser behavior)

## Testing

### Manual Testing

1. **Enable Section 508 mode:**
   ```bash
   /settings 508 on
   ```

2. **Send a message:**
   - Verify text appears immediately
   - Verify "Generating audio..." appears
   - Wait 2-10 seconds
   - Verify audio player appears

3. **Test playback:**
   - Click play button
   - Verify audio matches text
   - Test pause/volume/seek controls

4. **Disable and re-enable:**
   ```bash
   /settings 508 off
   # Verify no audio controls appear
   
   /settings 508 on
   # Verify audio controls return
   ```

### Testing Without Piper Service

If Piper is not running:
- Text responses work normally
- Audio loading indicator appears
- After 60s timeout, "Audio unavailable" message
- System remains functional (graceful degradation)

### Testing Commands

Commands should NOT trigger TTS:
```bash
/help
/agent list
/settings
```

Only actual agent responses trigger TTS.

## API Reference

### Generate TTS for Message

**Internal function (background thread):**
```python
from agent_app.tts_client import synthesize_for_message

synthesize_for_message(
    message_id=123,
    text="Hello, this is a test response.",
    voice_id="en_US-lessac-medium"  # Optional
)
```

### Poll for Audio URL

**GET** `/api/messages/{message_id}/audio/`

**Response:**
```json
{
  "message_id": 123,
  "audio_url": "http://localhost:8088/v1/audio/abc123",
  "has_audio": true,
  "content_preview": "Hello, this is a test..."
}
```

### Piper TTS Synthesize

**POST** `http://localhost:8088/v1/tts/synthesize`

**Request:**
```json
{
  "text": "Hello, this is a test.",
  "voice_id": "en_US-lessac-medium",
  "output_format": "mp3",
  "return_mode": "url"
}
```

**Response:**
```json
{
  "audio_id": "abc123",
  "audio_url": "/v1/audio/abc123",
  "content_type": "audio/mpeg",
  "expires_in": 86400
}
```

## Troubleshooting

### Audio Not Generating

1. **Check Piper service status:**
   ```bash
   make piper-logs
   curl http://localhost:8088/healthz
   ```

2. **Check environment variables:**
   ```bash
   echo $PIPER_BASE_URL
   echo $PIPER_DEFAULT_VOICE
   ```

3. **Check Django logs:**
   ```bash
   # Look for TTS-related messages
   grep "TTS" agent_ui/logs/*.log
   ```

### Audio Player Not Appearing

1. **Verify Section 508 mode is enabled:**
   ```bash
   /settings
   # Should show: Section 508 Mode: enabled
   ```

2. **Check browser console:**
   ```javascript
   console.log(window.SECTION_508_ENABLED);  // Should be true
   ```

3. **Check network tab:**
   - Look for `/api/messages/{id}/audio/` requests
   - Verify polling is happening every 2 seconds

### Audio Not Playing

1. **Check browser compatibility:**
   - MP3 is supported in all modern browsers
   - Safari, Chrome, Firefox, Edge all support MP3

2. **Check audio URL:**
   - Verify URL is accessible: `curl http://localhost:8088/v1/audio/abc123`
   - Check Piper service is running: `docker compose ps piper`

3. **Check browser console for errors:**
   - Look for CORS issues
   - Verify audio file loads successfully

## Security & Privacy

### Audio Storage
- Audio files cached on-prem (not cloud)
- 24-hour TTL for cached audio
- No audio transmitted to external services
- All TTS processing happens locally

### Data Handling
- Text responses stored in database (SQLite)
- Audio URLs reference Piper service cache
- No PII in audio cache keys (uses hash)
- Audio automatically expires after 24 hours

## Future Enhancements

### Potential Improvements
- [ ] Voice selection UI in settings
- [ ] Playback speed control
- [ ] Download audio button
- [ ] Batch TTS for session export
- [ ] WebSocket for real-time audio updates (instead of polling)
- [ ] Audio format selection (WAV vs MP3)
- [ ] Custom voice training for specialized terminology

### Considered but Not Implemented
- ❌ Autoplay - Violates WCAG 1.4.2
- ❌ Audio-only content - Text must always be available
- ❌ Cloud TTS - Must be on-prem for privacy/security

## Related Documentation

- [SECTION_508.md](./SECTION_508.md) - Section 508 mode overview
- [piper/README.md](../piper/README.md) - Piper TTS service documentation
- [piper/openapi.yaml](../piper/openapi.yaml) - Piper API specification
- [COMMANDS.md](./COMMANDS.md) - Command system reference

## Version History

- **v0.1.0** (2026-02) - Initial TTS integration
  - Async TTS synthesis
  - MP3 format for Safari
  - Native audio controls
  - Polling for audio availability
  - No autoplay
  - 24-hour audio caching
