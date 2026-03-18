"""Configuration for Piper TTS Service"""
import os
from pathlib import Path

class Config:
    """Service configuration"""
    
    # Service
    SERVICE_NAME = "piper-tts"
    VERSION = "1.0.0"
    PORT = 8088
    HOST = "0.0.0.0"
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "info").lower()
    
    # Directories
    VOICES_DIR = Path("/voices")
    AUDIO_CACHE_DIR = Path("/audio")
    
    # TTS Settings
    MAX_TEXT_LENGTH = 8000
    DEFAULT_SAMPLE_RATE = 22050
    DEFAULT_SPEAKING_RATE = 1.0
    SUPPORTED_SAMPLE_RATES = [8000, 16000, 22050, 24000]
    
    # Cache Settings
    DEFAULT_CACHE_TTL_SECONDS = 3600
    CACHE_CLEANUP_INTERVAL_SECONDS = 300  # 5 minutes
    METADATA_FILE = ".metadata.json"
    
    # Output formats
    SUPPORTED_OUTPUT_FORMATS = ["wav"]  # MP3 not implemented yet
    DEFAULT_OUTPUT_FORMAT = "wav"
    
    @classmethod
    def ensure_directories(cls):
        """Ensure required directories exist"""
        cls.AUDIO_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        if not cls.VOICES_DIR.exists():
            raise RuntimeError(f"Voices directory not found: {cls.VOICES_DIR}")

config = Config()
