"""
TTS client for Section 508 mode - Generates audio for assistant responses
"""

import logging
import os

import requests

logger = logging.getLogger(__name__)

# Piper TTS service configuration
PIPER_BASE_URL = os.getenv("PIPER_BASE_URL", "http://localhost:8088")
DEFAULT_VOICE_ID = os.getenv("PIPER_DEFAULT_VOICE", "en_US-lessac-medium")


def get_piper_health():
    """
    Check if Piper TTS service is available.

    Returns:
        bool: True if service is healthy, False otherwise
    """
    try:
        response = requests.get(f"{PIPER_BASE_URL}/healthz", timeout=2)
        return response.status_code == 200
    except Exception as e:
        logger.warning(f"Piper health check failed: {e}")
        return False


def synthesize_speech_async(text: str, message_id: int, voice_id: str = None) -> dict:
    """
    Synthesize speech from text using Piper TTS service (non-blocking).

    This function is designed to be called asynchronously after the text response
    is returned to the user. It generates audio and returns the URL.

    Args:
        text: Text to convert to speech
        message_id: ChatMessage ID for tracking
        voice_id: Optional voice ID (defaults to DEFAULT_VOICE_ID)

    Returns:
        dict: {
            "success": bool,
            "audio_url": str (if successful),
            "audio_id": str (if successful),
            "error": str (if failed)
        }
    """
    if not voice_id:
        voice_id = DEFAULT_VOICE_ID

    try:
        # Generate audio via Piper TTS
        response = requests.post(
            f"{PIPER_BASE_URL}/v1/tts/synthesize",
            json={
                "text": text[:8000],  # Truncate to max length
                "voice_id": voice_id,
                "return_mode": "url",  # Get URL instead of bytes
                "cache_ttl_seconds": 86400,  # Cache for 24 hours
            },
            timeout=30,  # Allow up to 30s for synthesis
        )

        if response.status_code == 200:
            data = response.json()

            # Convert relative URL to absolute if needed
            audio_url = data.get("audio_url", "")
            if audio_url and not audio_url.startswith("http"):
                audio_url = f"{PIPER_BASE_URL}{audio_url}"

            logger.info(f"TTS generated for message {message_id}: {audio_url}")

            return {
                "success": True,
                "audio_url": audio_url,
                "audio_id": data.get("audio_id", ""),
                "content_type": data.get("content_type", "audio/wav"),
            }
        error_msg = f"TTS service returned {response.status_code}"
        logger.error(f"TTS synthesis failed for message {message_id}: {error_msg}")
        return {"success": False, "error": error_msg}

    except requests.exceptions.Timeout:
        logger.error(f"TTS synthesis timeout for message {message_id}")
        return {"success": False, "error": "TTS service timeout"}
    except Exception as e:
        logger.error(f"TTS synthesis error for message {message_id}: {e}")
        return {"success": False, "error": str(e)}


def synthesize_for_message(message_id: int, text: str, voice_id: str = None):
    """
    Generate TTS audio for a message and update the database.

    This is intended to be called in a background thread/task after
    returning the text response to the user.

    Args:
        message_id: ChatMessage ID to update
        text: Text to synthesize (may contain markdown)
        voice_id: Optional voice ID
    """
    from agent_app.markdown_utils import markdown_to_plain_text
    from agent_app.models import ChatMessage

    # Strip markdown formatting for natural TTS output
    # The visual display still shows markdown, but audio is plain text
    plain_text = markdown_to_plain_text(text)

    logger.info(
        f"Converting markdown to plain text for TTS (message {message_id}): {len(text)} → {len(plain_text)} chars"
    )

    result = synthesize_speech_async(plain_text, message_id, voice_id)

    if result["success"]:
        try:
            # Update message with audio URL
            message = ChatMessage.objects.get(id=message_id)
            message.audio_url = result["audio_url"]
            message.save(update_fields=["audio_url"])
            logger.info(f"Updated message {message_id} with audio URL")
        except ChatMessage.DoesNotExist:
            logger.error(f"Message {message_id} not found when saving audio URL")
        except Exception as e:
            logger.error(f"Error updating message {message_id} with audio: {e}")
    else:
        logger.warning(f"TTS synthesis failed for message {message_id}: {result.get('error')}")
