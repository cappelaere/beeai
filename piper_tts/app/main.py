"""Piper TTS FastAPI Application"""
import logging
import uuid
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Response, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from .config import config
from .models import (
    HealthResponse,
    VoicesResponse,
    SynthesizeRequest,
    SynthesizeUrlResponse,
    ErrorResponse,
    ErrorDetail,
    ReturnMode
)
from .tts_engine import get_engine
from .audio_cache import get_cache

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def cleanup_cache_task():
    """Background task to cleanup expired cache files"""
    import asyncio
    cache = get_cache()
    while True:
        await asyncio.sleep(config.CACHE_CLEANUP_INTERVAL_SECONDS)
        try:
            removed = cache.cleanup_expired()
            if removed > 0:
                logger.info(f"Cleanup task removed {removed} expired files")
        except Exception as e:
            logger.error(f"Error in cleanup task: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management"""
    # Startup
    logger.info(f"Starting {config.SERVICE_NAME} v{config.VERSION}")
    config.ensure_directories()
    
    # Initialize engine (loads voices)
    engine = get_engine()
    voices = engine.get_available_voices()
    logger.info(f"Loaded {len(voices)} voices")
    
    # Start cleanup task
    import asyncio
    cleanup_task = asyncio.create_task(cleanup_cache_task())
    
    yield
    
    # Shutdown
    logger.info("Shutting down service")
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass


# Create FastAPI app
app = FastAPI(
    title="Piper TTS Service",
    description="Fast local TTS service using Piper",
    version=config.VERSION,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="ok",
        engine="piper",
        version=config.VERSION
    )


@app.get("/v1/voices", response_model=VoicesResponse)
async def list_voices(language_code: Optional[str] = None):
    """
    List available voices
    
    Args:
        language_code: Optional language filter (e.g., 'en-US')
    """
    try:
        engine = get_engine()
        voices = engine.get_available_voices(language_code=language_code)
        return VoicesResponse(voices=voices)
    except Exception as e:
        logger.error(f"Error listing voices: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "VoiceListError",
                    "message": f"Failed to list voices: {str(e)}"
                },
                "request_id": str(uuid.uuid4())
            }
        )


@app.post("/v1/tts/synthesize")
async def synthesize_speech(request: SynthesizeRequest):
    """
    Synthesize speech from text or SSML
    
    Returns audio bytes directly or URL depending on return_mode
    """
    request_id = str(uuid.uuid4())
    
    try:
        # Validate output format
        if request.output_format.value not in config.SUPPORTED_OUTPUT_FORMATS:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": {
                        "code": "UnsupportedFormatException",
                        "message": f"Output format '{request.output_format.value}' not supported. "
                                 f"Supported: {', '.join(config.SUPPORTED_OUTPUT_FORMATS)}"
                    },
                    "request_id": request_id
                }
            )
        
        # Validate sample rate
        if request.sample_rate not in config.SUPPORTED_SAMPLE_RATES:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": {
                        "code": "InvalidSampleRateException",
                        "message": f"Sample rate {request.sample_rate} not supported"
                    },
                    "request_id": request_id
                }
            )
        
        # Synthesize audio
        engine = get_engine()
        try:
            audio_bytes = engine.synthesize(
                text=request.text,
                voice_id=request.voice_id,
                sample_rate=request.sample_rate,
                speaking_rate=request.speaking_rate
            )
        except ValueError as e:
            # Voice not found or synthesis error
            raise HTTPException(
                status_code=422,
                detail={
                    "error": {
                        "code": "InvalidVoiceIdException",
                        "message": str(e)
                    },
                    "request_id": request_id
                }
            )
        
        content_type = "audio/wav" if request.output_format.value == "wav" else "audio/mpeg"
        
        # Return based on mode
        if request.return_mode == ReturnMode.BYTES:
            # Return audio bytes directly
            return Response(
                content=audio_bytes,
                media_type=content_type,
                headers={
                    "Content-Length": str(len(audio_bytes)),
                    "X-Request-ID": request_id
                }
            )
        else:
            # Save to cache and return URL
            cache = get_cache()
            audio_id, audio_url = cache.save_audio(
                audio_bytes=audio_bytes,
                content_type=content_type,
                ttl_seconds=request.cache_ttl_seconds
            )
            
            return SynthesizeUrlResponse(
                audio_id=audio_id,
                audio_url=audio_url,
                content_type=content_type,
                expires_in=request.cache_ttl_seconds
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Synthesis error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "SynthesisException",
                    "message": f"Speech synthesis failed: {str(e)}"
                },
                "request_id": request_id
            }
        )


@app.api_route("/v1/audio/{audio_id}", methods=["GET", "HEAD"])
async def get_cached_audio(request: Request, audio_id: str):
    """
    Retrieve cached audio by ID (supports GET and HEAD requests)
    
    Args:
        request: FastAPI Request object
        audio_id: Audio identifier from synthesize endpoint
    """
    cache = get_cache()
    result = cache.get_audio(audio_id)
    
    if result is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "AudioNotFoundException",
                    "message": f"Audio '{audio_id}' not found or expired"
                },
                "request_id": str(uuid.uuid4())
            }
        )
    
    audio_bytes, content_type = result
    
    # For HEAD requests, return headers only (no body)
    if request.method == "HEAD":
        return Response(
            content=None,
            media_type=content_type,
            headers={
                "Content-Length": str(len(audio_bytes)),
                "Accept-Ranges": "bytes"
            }
        )
    
    return Response(
        content=audio_bytes,
        media_type=content_type,
        headers={
            "Content-Length": str(len(audio_bytes)),
            "Cache-Control": "public, max-age=3600"
        }
    )


@app.get("/stats")
async def get_stats():
    """Get service statistics (internal/debug endpoint)"""
    cache = get_cache()
    engine = get_engine()
    
    return {
        "service": {
            "name": config.SERVICE_NAME,
            "version": config.VERSION,
            "engine": "piper"
        },
        "cache": cache.get_stats(),
        "voices": {
            "total": len(engine.get_available_voices()),
            "loaded_models": len(engine._loaded_models)
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=config.HOST,
        port=config.PORT,
        log_level=config.LOG_LEVEL
    )
