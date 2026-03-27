"""
Synthesize speech from text using Piper TTS service
"""

import json
import os

import requests
from beeai_framework.tools import StringToolOutput, tool

# Get Piper TTS base URL from environment, fallback to localhost
PIPER_TTS_URL = os.getenv("PIPER_TTS_URL", "http://localhost:8088").rstrip("/")


@tool
def synthesize_speech(
    text: str,
    voice_id: str,
    text_type: str = "text",
    output_format: str = "wav",
    sample_rate: int = 22050,
    speaking_rate: float = 1.0,
    return_mode: str = "url",
    cache_ttl_seconds: int = 3600,
) -> StringToolOutput:
    """
    Convert text to speech using the Piper TTS service.

    Args:
        text: The text or SSML to convert to speech (max 8000 characters)
        voice_id: Voice identifier from list_voices (e.g., "en_US_female_1")
        text_type: Either "text" or "ssml" (default: "text")
        output_format: Either "wav" or "mp3" (default: "wav" for speed)
        sample_rate: Sample rate in Hz - 8000, 16000, 22050, or 24000 (default: 22050)
        speaking_rate: Speed multiplier, 1.0 is normal speed (default: 1.0)
        return_mode: Either "url" (returns audio URL) or "bytes" (returns raw audio)
        cache_ttl_seconds: Time-to-live for cached audio when return_mode="url" (default: 3600)

    Returns:
        JSON with audio_url and audio_id when return_mode="url", or audio bytes when return_mode="bytes"
    """
    # Validate text length
    if len(text) > 8000:
        return StringToolOutput(
            json.dumps(
                {
                    "error": "TextTooLong",
                    "message": f"Text length ({len(text)}) exceeds maximum of 8000 characters",
                },
                indent=2,
            )
        )

    try:
        url = f"{PIPER_TTS_URL}/v1/tts/synthesize"

        payload = {
            "text": text,
            "voice_id": voice_id,
            "text_type": text_type,
            "output_format": output_format,
            "sample_rate": sample_rate,
            "speaking_rate": speaking_rate,
            "return_mode": return_mode,
            "cache_ttl_seconds": cache_ttl_seconds,
        }

        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()

        # If return_mode is "url", response is JSON
        if return_mode == "url":
            data = response.json()

            # Construct full URL for audio playback
            audio_path = data.get("audio_url", "")
            full_audio_url = (
                f"{PIPER_TTS_URL}{audio_path}" if audio_path.startswith("/") else audio_path
            )

            output = {
                "success": True,
                "audio_id": data.get("audio_id"),
                "audio_url": full_audio_url,
                "content_type": data.get("content_type"),
                "expires_in_seconds": data.get("expires_in"),
                "voice_used": voice_id,
                "text_length": len(text),
                "format": output_format,
            }

            return StringToolOutput(json.dumps(output, indent=2))
        # return_mode is "bytes" - not practical for agent responses
        return StringToolOutput(
            json.dumps(
                {
                    "success": True,
                    "message": "Audio bytes generated (not displayed in text format)",
                    "content_type": response.headers.get("Content-Type"),
                    "size_bytes": len(response.content),
                    "note": "Use return_mode='url' to get a playable URL instead",
                },
                indent=2,
            )
        )

    except requests.exceptions.ConnectionError:
        return StringToolOutput(
            json.dumps(
                {
                    "error": "ConnectionError",
                    "message": f"Cannot connect to Piper TTS service at {PIPER_TTS_URL}. "
                    "Make sure the service is running with 'make piper-start'",
                },
                indent=2,
            )
        )
    except requests.exceptions.Timeout:
        return StringToolOutput(
            json.dumps(
                {
                    "error": "Timeout",
                    "message": "Request to Piper TTS service timed out after 30 seconds",
                },
                indent=2,
            )
        )
    except requests.exceptions.HTTPError as e:
        try:
            error_data = e.response.json()
            error_info = error_data.get("error", {})
            return StringToolOutput(
                json.dumps(
                    {
                        "error": error_info.get("code", "HTTPError"),
                        "message": error_info.get("message", str(e)),
                        "status_code": e.response.status_code,
                    },
                    indent=2,
                )
            )
        except (AttributeError, TypeError, ValueError):
            return StringToolOutput(
                json.dumps(
                    {
                        "error": "HTTPError",
                        "message": f"HTTP error from Piper TTS service: {e}",
                        "status_code": e.response.status_code if hasattr(e, "response") else None,
                    },
                    indent=2,
                )
            )
    except Exception as e:
        return StringToolOutput(
            json.dumps(
                {"error": type(e).__name__, "message": f"Unexpected error: {str(e)}"}, indent=2
            )
        )
