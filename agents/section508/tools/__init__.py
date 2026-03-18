"""
Section 508 Agent Tools
Text-to-speech tools for accessibility
"""

from agents.section508.tools.list_voices import list_voices
from agents.section508.tools.synthesize_speech import synthesize_speech
from agents.section508.tools.tts_health_check import tts_health_check

__all__ = [
    "list_voices",
    "synthesize_speech",
    "tts_health_check",
]
