"""Piper TTS Engine Wrapper.

The third-party package `piper` (install with: pip install piper-tts) is imported
lazily so this module can be loaded when running from repo root without piper-tts
(e.g. pytest collection). Import errors are raised when the engine is actually used.
"""
import io
import wave
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np

from .config import config
from .models import Voice, Gender

logger = logging.getLogger(__name__)

_PIPER_IMPORT_ERROR: Optional[ImportError] = None


def _get_piper_voice():
    """Import PiperVoice from the piper package. Raises if piper-tts is not installed."""
    global _PIPER_IMPORT_ERROR
    if _PIPER_IMPORT_ERROR is not None:
        raise ImportError(
            "The piper package is not installed. Install it with: pip install piper-tts"
        ) from _PIPER_IMPORT_ERROR
    try:
        from piper import PiperVoice
        return PiperVoice
    except ImportError as e:
        _PIPER_IMPORT_ERROR = e
        raise ImportError(
            "The piper package is not installed. Install it with: pip install piper-tts"
        ) from e


class TTSEngine:
    """Wrapper for Piper TTS engine with model caching"""

    def __init__(self, voices_dir: Path = None):
        self.voices_dir = voices_dir or config.VOICES_DIR
        self._loaded_models: Dict[str, Any] = {}
        self._available_voices: Optional[List[Voice]] = None
        logger.info(f"TTS Engine initialized with voices directory: {self.voices_dir}")

    def _load_voice(self, voice_id: str) -> Any:
        """
        Load a Piper voice model (with caching)
        
        Args:
            voice_id: Voice identifier (e.g., 'en_US-lessac-medium')
            
        Returns:
            Loaded PiperVoice instance
            
        Raises:
            ValueError: If voice not found
        """
        if voice_id in self._loaded_models:
            logger.debug(f"Using cached model for {voice_id}")
            return self._loaded_models[voice_id]
        
        # Find voice files in the voices directory
        voice_path = self.voices_dir / f"{voice_id}.onnx"
        config_path = self.voices_dir / f"{voice_id}.onnx.json"
        
        if not voice_path.exists() or not config_path.exists():
            available = [f.stem.replace('.onnx', '') for f in self.voices_dir.glob("*.onnx")]
            logger.error(f"Voice {voice_id} not found. Available: {available}")
            raise ValueError(f"Voice '{voice_id}' not found. Available voices: {', '.join(available)}")
        
        logger.info(f"Loading voice model: {voice_id}")
        piper_voice = _get_piper_voice()
        try:
            voice = piper_voice.load(str(voice_path), config_path=str(config_path))
            self._loaded_models[voice_id] = voice
            logger.info(f"Successfully loaded voice: {voice_id}")
            return voice
        except Exception as e:
            logger.error(f"Failed to load voice {voice_id}: {e}")
            raise ValueError(f"Failed to load voice '{voice_id}': {str(e)}")
    
    def synthesize(
        self,
        text: str,
        voice_id: str,
        sample_rate: int = 22050,
        speaking_rate: float = 1.0
    ) -> bytes:
        """
        Synthesize speech from text
        
        Args:
            text: Input text
            voice_id: Voice to use
            sample_rate: Output sample rate
            speaking_rate: Speed multiplier (via length_scale)
            
        Returns:
            WAV audio bytes
            
        Raises:
            ValueError: If voice not found or synthesis fails
        """
        voice = self._load_voice(voice_id)
        
        # Convert speaking_rate to length_scale (inverse relationship)
        # speaking_rate > 1.0 means faster, so length_scale < 1.0
        length_scale = 1.0 / speaking_rate
        
        logger.info(f"Synthesizing text (length={len(text)}) with voice={voice_id}, "
                   f"sample_rate={sample_rate}, speaking_rate={speaking_rate}")
        
        try:
            # Synthesize audio
            audio_stream = io.BytesIO()
            with wave.open(audio_stream, 'wb') as wav_file:
                # Set WAV parameters
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                
                # Synthesize
                voice.synthesize(
                    text,
                    wav_file,
                    length_scale=length_scale,
                    sentence_silence=0.0
                )
            
            audio_bytes = audio_stream.getvalue()
            logger.info(f"Synthesis successful, generated {len(audio_bytes)} bytes")
            return audio_bytes
            
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            raise ValueError(f"Speech synthesis failed: {str(e)}")
    
    def get_available_voices(self, language_code: Optional[str] = None) -> List[Voice]:
        """
        List available voices
        
        Args:
            language_code: Optional language filter (e.g., 'en-US')
            
        Returns:
            List of Voice objects
        """
        if self._available_voices is None:
            self._available_voices = self._discover_voices()
        
        voices = self._available_voices
        
        # Filter by language if requested
        if language_code:
            voices = [v for v in voices if v.language_code == language_code]
        
        return voices
    
    def _discover_voices(self) -> List[Voice]:
        """
        Discover available voices in the voices directory
        
        Returns:
            List of Voice objects
        """
        voices = []
        
        # Find all .onnx files
        for onnx_file in self.voices_dir.glob("*.onnx"):
            voice_id = onnx_file.stem
            config_file = onnx_file.with_suffix('.onnx.json')
            
            if not config_file.exists():
                logger.warning(f"Config file missing for {voice_id}, skipping")
                continue
            
            try:
                # Parse voice info from filename
                # Format: language_country-name-quality (e.g., en_US-lessac-medium)
                parts = voice_id.split('-')
                if len(parts) >= 2:
                    language_part = parts[0]
                    name_part = '-'.join(parts[1:])
                    
                    # Convert language format: en_US -> en-US
                    language_code = language_part.replace('_', '-')
                    
                    # Determine gender from name (heuristic)
                    gender = self._guess_gender(name_part)
                    
                    # Generate display name
                    name = f"{language_code} {name_part.replace('-', ' ').title()}"
                    
                    voice = Voice(
                        id=voice_id,
                        name=name,
                        language_code=language_code,
                        gender=gender,
                        sample_rates=[16000, 22050],  # Piper standard rates
                        engines=["standard"]
                    )
                    voices.append(voice)
                    logger.debug(f"Discovered voice: {voice_id}")
                    
            except Exception as e:
                logger.warning(f"Failed to parse voice {voice_id}: {e}")
                continue
        
        logger.info(f"Discovered {len(voices)} voices")
        return voices
    
    def _guess_gender(self, name: str) -> Gender:
        """Guess gender from voice name (heuristic)"""
        name_lower = name.lower()
        
        # Common female names/indicators
        if any(x in name_lower for x in ['lessac', 'amy', 'jenny', 'emma', 'female']):
            return Gender.FEMALE
        
        # Common male names/indicators
        if any(x in name_lower for x in ['ryan', 'alan', 'danny', 'joe', 'male']):
            return Gender.MALE
        
        return Gender.UNKNOWN


# Global engine instance
_engine_instance: Optional[TTSEngine] = None


def get_engine() -> TTSEngine:
    """Get or create global TTS engine instance"""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = TTSEngine()
    return _engine_instance
