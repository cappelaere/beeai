# Piper TTS Microservice

Fast, local Text-to-Speech service using Piper TTS, designed for on-premises deployment on Apple Silicon laptops.

## Features

- 🎙️ **High-quality TTS** - Powered by Piper neural TTS engine
- 🚀 **Fast synthesis** - Optimized for local CPU inference
- 🎭 **Multiple voices** - Pre-installed English voices (US & British, male & female)
- 📦 **Docker-ready** - Easy deployment with Docker Compose
- 🔄 **Audio caching** - Optional caching with configurable TTL
- 🎵 **WAV output** - Native high-quality WAV format
- 📊 **RESTful API** - OpenAPI 3.1 compliant

## Quick Start

### Using Docker Compose (Recommended)

1. **Build and start the service:**

```bash
docker-compose up --build piper
```

2. **Test the health endpoint:**

```bash
curl http://localhost:8088/healthz
```

3. **Synthesize speech:**

```bash
curl -X POST http://localhost:8088/v1/tts/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, this is a test of the Piper text to speech system.",
    "voice_id": "en_US-lessac-medium"
  }' \
  --output hello.wav
```

4. **Play the audio:**

```bash
afplay hello.wav  # macOS
# or
aplay hello.wav   # Linux
```

### Local Development

1. **Install dependencies:**

```bash
cd piper_tts
pip install -r requirements.txt
```

2. **Download voice models** (required for local dev):

```bash
mkdir -p voices
cd voices

# Download en_US-lessac-medium
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json

# Download additional voices as needed
```

3. **Run the service:**

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8088 --reload
```

## API Endpoints

### Health Check

```bash
GET /healthz
```

**Response:**
```json
{
  "status": "ok",
  "engine": "piper",
  "version": "1.0.0"
}
```

### List Available Voices

```bash
GET /v1/voices
GET /v1/voices?language_code=en-US
```

**Response:**
```json
{
  "voices": [
    {
      "id": "en_US-lessac-medium",
      "name": "en-US lessac medium",
      "language_code": "en-US",
      "gender": "Female",
      "sample_rates": [16000, 22050],
      "engines": ["standard"]
    }
  ]
}
```

### Synthesize Speech

#### Mode 1: Return Audio Bytes (Default)

```bash
POST /v1/tts/synthesize
Content-Type: application/json

{
  "text": "Your text here",
  "voice_id": "en_US-lessac-medium",
  "return_mode": "bytes"  // optional, default
}
```

**Response:** Audio bytes (audio/wav)

#### Mode 2: Return URL with Caching

```bash
POST /v1/tts/synthesize
Content-Type: application/json

{
  "text": "Your text here",
  "voice_id": "en_US-lessac-medium",
  "return_mode": "url",
  "cache_ttl_seconds": 3600
}
```

**Response:**
```json
{
  "audio_id": "abc-123-def",
  "audio_url": "/v1/audio/abc-123-def",
  "content_type": "audio/wav",
  "expires_in": 3600
}
```

### Get Cached Audio

```bash
GET /v1/audio/{audio_id}
```

**Response:** Audio bytes (audio/wav)

## Request Parameters

### SynthesizeRequest

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `text` | string | Yes | - | Text to synthesize (max 8000 chars) |
| `voice_id` | string | Yes | - | Voice identifier from `/v1/voices` |
| `text_type` | string | No | `"text"` | `"text"` or `"ssml"` |
| `output_format` | string | No | `"wav"` | Audio format (only `"wav"` supported) |
| `sample_rate` | integer | No | `22050` | Sample rate: 8000, 16000, 22050, or 24000 |
| `speaking_rate` | float | No | `1.0` | Speed multiplier (0.5 = slower, 2.0 = faster) |
| `return_mode` | string | No | `"bytes"` | `"bytes"` or `"url"` |
| `cache_ttl_seconds` | integer | No | `3600` | Cache TTL if `return_mode="url"` |

## Pre-installed Voices

| Voice ID | Language | Gender | Quality | Use Case |
|----------|----------|--------|---------|----------|
| `en_US-lessac-medium` | English (US) | Female | High | General purpose, clear |
| `en_US-ryan-high` | English (US) | Male | High | Professional, authoritative |
| `en_GB-alan-medium` | English (GB) | Male | Medium | British accent |

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `info` | Logging level (debug, info, warning, error) |

Volumes:

| Container Path | Description |
|---------------|-------------|
| `/audio` | Audio cache directory (mount to persist cache) |
| `/voices` | Voice models (pre-loaded in image) |

## Examples

### Basic Synthesis

```bash
curl -X POST http://localhost:8088/v1/tts/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Welcome to the RealtyIQ platform.",
    "voice_id": "en_US-lessac-medium"
  }' \
  --output welcome.wav
```

### Faster Speech

```bash
curl -X POST http://localhost:8088/v1/tts/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This will be spoken faster.",
    "voice_id": "en_US-lessac-medium",
    "speaking_rate": 1.5
  }' \
  --output fast.wav
```

### Using Cached URL Mode

```bash
# Generate and cache audio
curl -X POST http://localhost:8088/v1/tts/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This audio will be cached.",
    "voice_id": "en_US-ryan-high",
    "return_mode": "url",
    "cache_ttl_seconds": 7200
  }'

# Response:
# {
#   "audio_id": "xyz-789",
#   "audio_url": "/v1/audio/xyz-789",
#   "content_type": "audio/wav",
#   "expires_in": 7200
# }

# Retrieve cached audio
curl http://localhost:8088/v1/audio/xyz-789 --output cached.wav
```

### Different Sample Rates

```bash
# Lower quality, smaller file
curl -X POST http://localhost:8088/v1/tts/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Lower sample rate example.",
    "voice_id": "en_US-lessac-medium",
    "sample_rate": 16000
  }' \
  --output low_rate.wav
```

### British Voice

```bash
curl -X POST http://localhost:8088/v1/tts/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Good afternoon, this is a British voice.",
    "voice_id": "en_GB-alan-medium"
  }' \
  --output british.wav
```

## Testing

### Run Tests

```bash
cd piper_tts

# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_api.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

### Test Structure

```
tests/
├── test_api.py           # FastAPI endpoint tests
├── test_tts_engine.py    # TTS engine unit tests
└── test_audio_cache.py   # Cache manager tests
```

## Docker Build

### Build Image

```bash
docker build -t piper-tts:latest ./piper_tts
```

### Run Container

```bash
docker run -d \
  --name piper-tts \
  -p 8088:8088 \
  -v $(pwd)/piper_tts/audio:/audio \
  piper-tts:latest
```

### Check Logs

```bash
docker logs -f piper-tts
```

## Troubleshooting

### Voice Not Found Error

**Problem:** `Voice 'xyz' not found`

**Solution:** Check available voices:
```bash
curl http://localhost:8088/v1/voices | jq '.voices[].id'
```

### Service Won't Start

**Problem:** Container exits immediately

**Solution:** Check logs:
```bash
docker logs realtyiq-piper-tts
```

Common issues:
- Voice files missing in `/voices` directory
- Port 8088 already in use
- Insufficient memory (needs ~500MB)

### Audio Cache Not Persisting

**Problem:** Cached audio lost after restart

**Solution:** Ensure volume is mounted:
```bash
# Check docker-compose.yml has:
volumes:
  - ./piper_tts/audio:/audio
```

### Slow Synthesis

**Problem:** First request is slow

**Explanation:** Voice model loads on first use (normal behavior)

**Solution:** 
- Subsequent requests will be fast (model cached in memory)
- Pre-warm by making a test request after startup

## Performance

### Benchmarks (Apple M1)

| Metric | Value |
|--------|-------|
| First synthesis | ~2-3 seconds (model load) |
| Subsequent synthesis | ~0.5-1 second |
| Memory usage | ~400-500 MB |
| Image size | ~380 MB |

### Optimization Tips

1. **Reuse voices** - Models are cached after first load
2. **Use WAV format** - No conversion overhead
3. **Tune sample rate** - Lower = faster (16000 vs 22050)
4. **Batch requests** - Keep container warm
5. **Cache URLs** - Use `return_mode="url"` for repeated playback

## API Documentation

Interactive API documentation available at:
- Swagger UI: http://localhost:8088/docs
- ReDoc: http://localhost:8088/redoc
- OpenAPI spec: [`openapi.yaml`](openapi.yaml)

## Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ HTTP
       ▼
┌─────────────────┐
│   FastAPI App   │
│   (port 8088)   │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌──────┐  ┌───────┐
│ Piper│  │ Cache │
│Engine│  │Manager│
└──┬───┘  └───┬───┘
   │          │
   ▼          ▼
┌──────┐  ┌──────┐
│Voices│  │/audio│
│/voices  │volume│
└──────┘  └──────┘
```

## License

This service uses Piper TTS, which is licensed under MIT License.

## Support

For issues or questions:
1. Check logs: `docker logs realtyiq-piper-tts`
2. Test health: `curl http://localhost:8088/healthz`
3. View stats: `curl http://localhost:8088/stats`
