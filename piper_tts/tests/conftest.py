"""Pytest configuration for Piper TTS tests.

Adds piper_tts to sys.path so that "from app.xxx" resolves when running
pytest from repo root (e.g. pytest piper_tts/tests/ or pytest piper_tts/tests/test_tts_engine.py).
"""
import sys
from pathlib import Path

# Ensure piper_tts is on the path so "app" resolves to piper_tts.app
piper_tts_root = Path(__file__).resolve().parent.parent
if str(piper_tts_root) not in sys.path:
    sys.path.insert(0, str(piper_tts_root))
