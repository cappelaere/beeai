"""
List available TTS voices from Piper service
"""

import json
import os

import requests
from beeai_framework.tools import StringToolOutput, tool

# Get Piper TTS base URL from environment, fallback to localhost
PIPER_TTS_URL = os.getenv("PIPER_TTS_URL", "http://localhost:8088").rstrip("/")


@tool
def list_voices(language_code: str = "") -> StringToolOutput:
    """
    List all available text-to-speech voices from the Piper TTS service.

    Args:
        language_code: Optional language code to filter voices (e.g., "en-US", "es-ES")

    Returns:
        JSON list of available voices with their metadata (id, name, language, gender, sample rates)
    """
    try:
        url = f"{PIPER_TTS_URL}/v1/voices"
        params = {}
        if language_code:
            params["language_code"] = language_code

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        voices = data.get("voices", [])

        # Format output for readability
        output = {
            "total_voices": len(voices),
            "language_filter": language_code if language_code else "none",
            "voices": voices,
        }

        return StringToolOutput(json.dumps(output, indent=2))

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
                {"error": "Timeout", "message": "Request to Piper TTS service timed out"}, indent=2
            )
        )
    except requests.exceptions.HTTPError as e:
        return StringToolOutput(
            json.dumps(
                {"error": "HTTPError", "message": f"HTTP error from Piper TTS service: {e}"},
                indent=2,
            )
        )
    except Exception as e:
        return StringToolOutput(
            json.dumps(
                {"error": type(e).__name__, "message": f"Unexpected error: {str(e)}"}, indent=2
            )
        )
