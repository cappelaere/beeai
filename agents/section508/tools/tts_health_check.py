"""
Check health status of Piper TTS service
"""

import json
import os

import requests
from beeai_framework.tools import StringToolOutput, tool

# Get Piper TTS base URL from environment, fallback to localhost
PIPER_TTS_URL = os.getenv("PIPER_TTS_URL", "http://localhost:8088").rstrip("/")


@tool
def tts_health_check() -> StringToolOutput:
    """
    Check the health status of the Piper TTS service.

    Returns:
        JSON with service status, engine type, and version information
    """
    try:
        url = f"{PIPER_TTS_URL}/healthz"

        response = requests.get(url, timeout=5)
        response.raise_for_status()

        data = response.json()

        output = {
            "service": "Piper TTS",
            "url": PIPER_TTS_URL,
            "status": data.get("status", "unknown"),
            "engine": data.get("engine", "unknown"),
            "version": data.get("version", "unknown"),
            "healthy": data.get("status") == "ok",
        }

        return StringToolOutput(json.dumps(output, indent=2))

    except requests.exceptions.ConnectionError:
        return StringToolOutput(
            json.dumps(
                {
                    "service": "Piper TTS",
                    "url": PIPER_TTS_URL,
                    "status": "unreachable",
                    "healthy": False,
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
                    "service": "Piper TTS",
                    "url": PIPER_TTS_URL,
                    "status": "timeout",
                    "healthy": False,
                    "error": "Timeout",
                    "message": "Health check request timed out",
                },
                indent=2,
            )
        )
    except requests.exceptions.HTTPError as e:
        return StringToolOutput(
            json.dumps(
                {
                    "service": "Piper TTS",
                    "url": PIPER_TTS_URL,
                    "status": "error",
                    "healthy": False,
                    "error": "HTTPError",
                    "message": f"HTTP error: {e}",
                    "status_code": e.response.status_code if hasattr(e, "response") else None,
                },
                indent=2,
            )
        )
    except Exception as e:
        return StringToolOutput(
            json.dumps(
                {
                    "service": "Piper TTS",
                    "url": PIPER_TTS_URL,
                    "status": "error",
                    "healthy": False,
                    "error": type(e).__name__,
                    "message": f"Unexpected error: {str(e)}",
                },
                indent=2,
            )
        )
