# Section 508 Agent Documentation

## Overview

**Agent Name:** Section 508 Agent 🔊  
**Purpose:** Section 508 accessibility compliance assistant with text-to-speech capabilities  
**Type:** Text-to-speech (TTS) service integration for accessibility

The Section 508 Agent provides text-to-speech capabilities using the Piper TTS microservice, enabling users to convert text content into natural-sounding speech for accessibility purposes. This supports Section 508 compliance requirements for making digital content accessible to users with visual impairments.

## When to Use This Agent

Use the Section 508 Agent when you need to:
- Convert text to speech for accessibility purposes
- Generate audio versions of written content
- Provide alternative formats for visually impaired users
- Test different voice options and languages
- Create narrated content
- Ensure Section 508 compliance for digital materials

## Quick Start

### Selecting the Agent
1. Open the RealtyIQ interface
2. Use the agent selector dropdown in the top bar
3. Select "🔊 Section 508"

### Starting the TTS Service

Before using this agent, ensure the Piper TTS service is running:

```bash
make piper-start
```

### Basic Usage Examples

**Convert text to speech:**
```
Convert this text to speech: "Welcome to our application"
Read this paragraph aloud: [paste your text]
Generate audio for accessibility: "User agreement terms and conditions..."
```

**List available voices:**
```
What voices are available?
Show me English voices
List all female voices
```

**Check service status:**
```
Is the TTS service running?
Check the health of the speech service
```

## Available Tools

### Voice Management

#### list_voices
**Purpose:** List all available text-to-speech voices with metadata

**Key Parameters:**
- `language_code` (str, optional): Filter by language (e.g., "en-US", "es-ES")

**Example:**
```
list_voices()
list_voices(language_code="en-US")
```

**Returns:**
- Total voices available
- Language filter applied (if any)
- List of voices with:
  - Voice ID (for synthesis)
  - Name
  - Language code
  - Gender (Female, Male, Neutral, Unknown)
  - Sample rates available
  - Engines supported

**Common Voice IDs:**
- `en_US_female_1` - English US Female
- `en_US_male_1` - English US Male
- Additional voices depending on installation

**Use Cases:**
- Discover available voices
- Find voices in specific languages
- Select appropriate voice for content
- Check gender options

### Speech Synthesis

#### synthesize_speech
**Purpose:** Convert text or SSML to natural-sounding speech audio

**Key Parameters:**
- `text` (str, required): Text or SSML to convert (max 8000 characters)
- `voice_id` (str, required): Voice identifier from list_voices
- `text_type` (str): "text" or "ssml" (default: "text")
- `output_format` (str): "wav" or "mp3" (default: "wav")
- `sample_rate` (int): 8000, 16000, 22050, or 24000 Hz (default: 22050)
- `speaking_rate` (float): Speed multiplier, 1.0 is normal (default: 1.0)
- `return_mode` (str): "url" (returns playable URL) or "bytes" (default: "url")
- `cache_ttl_seconds` (int): Cache lifetime (default: 3600 = 1 hour)

**Example:**
```
synthesize_speech(
    text="Hello, welcome to our service",
    voice_id="en_US_female_1",
    output_format="wav",
    speaking_rate=1.0
)

synthesize_speech(
    text="<speak>This is <emphasis>important</emphasis></speak>",
    voice_id="en_US_male_1",
    text_type="ssml",
    speaking_rate=0.9
)
```

**Returns (when return_mode="url"):**
- Success status
- Audio ID (unique identifier)
- Audio URL (playable link)
- Content type (audio/wav or audio/mp3)
- Expiration time (seconds until cached audio expires)
- Voice used
- Text length
- Format

**Use Cases:**
- Generate audio for web content
- Create accessible versions of documents
- Produce narrated content
- Test different voice options
- Generate multilingual audio

**Text Format Options:**

**Plain Text:**
```
"This is regular text that will be spoken naturally."
```

**SSML (Speech Synthesis Markup Language):**
```xml
<speak>
  This text has <emphasis>emphasis</emphasis> and 
  <prosody rate="slow">slower speech</prosody>.
</speak>
```

### Service Monitoring

#### tts_health_check
**Purpose:** Check the health and status of the Piper TTS service

**Example:**
```
tts_health_check()
```

**Returns:**
- Service name (Piper TTS)
- Service URL
- Status (ok, unreachable, timeout, error)
- Engine type (piper)
- Version
- Healthy status (True/False)
- Error details (if any)

**Use Cases:**
- Verify service is running
- Diagnose connection issues
- Check service version
- Troubleshoot TTS problems

## Common Workflows

### Converting Text to Speech

1. **Check service is running:**
   ```
   tts_health_check()
   ```

2. **List available voices:**
   ```
   list_voices(language_code="en-US")
   ```

3. **Select appropriate voice** based on:
   - Language of content
   - Gender preference
   - Voice quality

4. **Generate audio:**
   ```
   synthesize_speech(
       text="Your content here",
       voice_id="en_US_female_1",
       output_format="wav"
   )
   ```

5. **Use the returned audio URL** to play or embed

### Creating Accessible Content

1. **Prepare text content:**
   - Remove formatting
   - Ensure proper punctuation
   - Keep under 8000 characters per request

2. **Choose voice:**
   ```
   list_voices()
   ```

3. **Generate with optimal settings:**
   ```
   synthesize_speech(
       text="[your content]",
       voice_id="en_US_female_1",
       output_format="wav",
       sample_rate=22050,
       speaking_rate=1.0
   )
   ```

4. **Cache for reuse:**
   - Audio is cached automatically
   - Default TTL: 1 hour
   - Adjust cache_ttl_seconds if needed

### Troubleshooting Service Issues

1. **Check service health:**
   ```
   tts_health_check()
   ```

2. **If service is down:**
   ```bash
   make piper-start
   ```

3. **Verify service started:**
   ```
   tts_health_check()
   ```

4. **Check logs if issues persist:**
   ```bash
   make piper-logs
   ```

## Technical Details

### Piper TTS Service

**Technology:**
- **Engine:** Piper TTS (open-source neural TTS)
- **Architecture:** FastAPI microservice
- **Port:** 8088 (localhost)
- **Format:** REST API

**Service Management:**
```bash
make piper-build    # Build Docker image
make piper-start    # Start service
make piper-stop     # Stop service
make piper-logs     # View logs
make piper-restart  # Restart service
make piper-shell    # Access container
```

### Audio Quality

**Sample Rates:**
- **8000 Hz** - Telephone quality
- **16000 Hz** - Good for speech
- **22050 Hz** - High quality (default)
- **24000 Hz** - Studio quality

**Format Comparison:**
- **WAV:** Uncompressed, fast processing, larger files
- **MP3:** Compressed, smaller files, slower processing

**Recommendation:** Use WAV format for fastest processing on local systems.

### Voice Models

**Pre-installed Voices:**
- Multiple English voices (US, UK, etc.)
- Various genders and tones
- Additional languages (depending on installation)

**Voice Selection:**
- Browse with `list_voices()`
- Test different voices
- Consider audience and content

### Caching System

**Audio Caching:**
- Generated audio is cached automatically
- Cache location: `/piper/audio` (volume mount)
- Default TTL: 1 hour
- Reduces processing for repeated requests

**Cache Benefits:**
- Faster repeated playback
- Reduced CPU usage
- Lower latency for common phrases

### API Integration

**Base URL:** `http://localhost:8088` (configurable via `PIPER_TTS_URL`)

**Endpoints Used:**
- `GET /healthz` - Health check
- `GET /v1/voices` - List voices
- `POST /v1/tts/synthesize` - Generate speech
- `GET /v1/audio/{audio_id}` - Retrieve cached audio

**Authentication:** None (local service)

## Example Use Cases

### For Content Creators
- "Convert this blog post to audio"
- "Generate narration for tutorial video"
- "Create audio version of newsletter"

### For Accessibility Officers
- "Make this document Section 508 compliant with audio"
- "Generate speech for web content"
- "Provide audio alternative for text content"

### For Developers
- "Test TTS integration with different voices"
- "Generate audio alerts for application"
- "Create audio feedback for UI elements"

### For Educators
- "Convert lesson material to audio"
- "Generate pronunciation examples"
- "Create audio study guides"

## Section 508 Compliance

### What is Section 508?

Section 508 of the Rehabilitation Act requires federal agencies to make electronic and information technology accessible to people with disabilities, including providing alternative formats for content.

### How This Agent Helps

**Text-to-Speech Capabilities:**
- Converts text content to audio
- Provides alternative format for visual content
- Supports multiple voices and languages
- Enables customizable speech parameters

**Accessibility Features:**
- Multiple voice options
- Adjustable speaking rate
- Various audio formats
- Cached audio for performance

### Best Practices

1. **Provide Audio Alternatives:**
   - Generate audio for key text content
   - Embed audio players in web pages
   - Offer downloadable audio files

2. **Use Clear, Natural Speech:**
   - Select appropriate voices
   - Use normal speaking rate (1.0)
   - Ensure proper punctuation in text

3. **Test Accessibility:**
   - Try different voices
   - Verify audio quality
   - Check playback compatibility

4. **Maintain Audio:**
   - Update audio when text changes
   - Monitor cache expiration
   - Regenerate as needed

## Limitations

### Current Limitations

1. **Text Length:**
   - Maximum 8000 characters per request
   - Split longer content into chunks

2. **Local Service:**
   - Requires Piper service running locally
   - Not available if service is down

3. **Language Support:**
   - Depends on installed voice models
   - English voices pre-installed
   - Other languages require additional models

4. **Processing Time:**
   - Synthesis takes a few seconds
   - Longer for large texts
   - First generation slower (caching helps)

### Workarounds

**For Long Text:**
- Split into 8000-character chunks
- Generate multiple audio files
- Concatenate if needed

**For Other Languages:**
- Install additional voice models
- Rebuild Piper service
- Update voice list

## Performance Optimization

### Speed Tips

1. **Use WAV Format:**
   - Faster than MP3
   - Better for real-time needs

2. **Leverage Caching:**
   - Identical text uses cached audio
   - Adjust TTL based on needs

3. **Optimize Sample Rate:**
   - 16000 Hz for speech is sufficient
   - Higher rates slower but better quality

4. **Batch Processing:**
   - Generate audio during off-peak
   - Pre-generate common phrases

### Resource Management

**CPU Usage:**
- Synthesis is CPU-intensive
- Consider Docker resource limits
- Monitor during high usage

**Disk Space:**
- Cache uses disk space
- Monitor `/piper/audio` volume
- Clean old cache files periodically

**Memory:**
- Service uses ~500MB-1GB RAM
- Scales with concurrent requests

## Related Agents

- **Library Agent** - For searching accessible documentation
- **GRES Agent** - For property listings (can add audio descriptions)
- **Identity Verification Agent** - For accessible verification workflows

## Support

### Service Not Running

**Start the service:**
```bash
make piper-start
```

**Check service status:**
```bash
docker ps | grep piper
make piper-logs
```

### Generation Errors

**Common Issues:**
1. Text too long: Split into smaller chunks
2. Invalid voice_id: Use `list_voices()` to find valid IDs
3. Service timeout: Check service health and resources

### Audio Issues

**Quality Problems:**
- Try different sample rates
- Test alternative voices
- Verify source text quality

**Playback Issues:**
- Check audio URL is accessible
- Verify browser audio support
- Try different audio format

### Getting Help

1. Check service logs: `make piper-logs`
2. Verify service health: `tts_health_check()`
3. Restart service: `make piper-restart`
4. Review Piper documentation in `/piper/README.md`

## Additional Resources

- **Piper TTS Documentation:** See `/piper/README.md`
- **OpenAPI Specification:** See `/piper/openapi.yaml`
- **Service Configuration:** See `/piper/app/config.py`
- **Docker Compose:** See main `docker-compose.yml`
