"""Tests for TTS Engine"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile

from app.tts_engine import TTSEngine
from app.models import Gender


class TestTTSEngine:
    """Test TTS Engine functionality"""
    
    @pytest.fixture
    def mock_voices_dir(self):
        """Create temporary voices directory with mock files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            voices_dir = Path(tmpdir)
            
            # Create mock voice files
            (voices_dir / "en_US-lessac-medium.onnx").touch()
            (voices_dir / "en_US-lessac-medium.onnx.json").write_text('{}')
            (voices_dir / "en_US-ryan-high.onnx").touch()
            (voices_dir / "en_US-ryan-high.onnx.json").write_text('{}')
            
            yield voices_dir
    
    def test_engine_initialization(self, mock_voices_dir):
        """Test engine initializes correctly"""
        engine = TTSEngine(voices_dir=mock_voices_dir)
        assert engine.voices_dir == mock_voices_dir
        assert len(engine._loaded_models) == 0
    
    def test_discover_voices(self, mock_voices_dir):
        """Test voice discovery from directory"""
        engine = TTSEngine(voices_dir=mock_voices_dir)
        voices = engine.get_available_voices()
        
        assert len(voices) == 2
        voice_ids = [v.id for v in voices]
        assert "en_US-lessac-medium" in voice_ids
        assert "en_US-ryan-high" in voice_ids
    
    def test_filter_voices_by_language(self, mock_voices_dir):
        """Test filtering voices by language code"""
        engine = TTSEngine(voices_dir=mock_voices_dir)
        
        # All voices are en-US
        en_voices = engine.get_available_voices(language_code="en-US")
        assert len(en_voices) == 2
        
        # No Spanish voices
        es_voices = engine.get_available_voices(language_code="es-ES")
        assert len(es_voices) == 0
    
    def test_guess_gender(self, mock_voices_dir):
        """Test gender guessing from voice name"""
        engine = TTSEngine(voices_dir=mock_voices_dir)
        
        assert engine._guess_gender("lessac") == Gender.FEMALE
        assert engine._guess_gender("ryan") == Gender.MALE
        assert engine._guess_gender("unknown") == Gender.UNKNOWN
    
    @patch('app.tts_engine._get_piper_voice')
    def test_load_voice_success(self, mock_get_piper_voice, mock_voices_dir):
        """Test successful voice loading"""
        mock_piper_voice = Mock()
        mock_voice_instance = Mock()
        mock_piper_voice.load.return_value = mock_voice_instance
        mock_get_piper_voice.return_value = mock_piper_voice

        engine = TTSEngine(voices_dir=mock_voices_dir)
        voice = engine._load_voice("en_US-lessac-medium")

        assert voice == mock_voice_instance
        assert "en_US-lessac-medium" in engine._loaded_models
        mock_piper_voice.load.assert_called_once()

    @patch('app.tts_engine._get_piper_voice')
    def test_load_voice_caching(self, mock_get_piper_voice, mock_voices_dir):
        """Test voice model is cached after first load"""
        mock_piper_voice = Mock()
        mock_voice_instance = Mock()
        mock_piper_voice.load.return_value = mock_voice_instance
        mock_get_piper_voice.return_value = mock_piper_voice

        engine = TTSEngine(voices_dir=mock_voices_dir)

        # First load
        voice1 = engine._load_voice("en_US-lessac-medium")
        # Second load (should use cache)
        voice2 = engine._load_voice("en_US-lessac-medium")

        assert voice1 == voice2
        # Should only call load once
        assert mock_piper_voice.load.call_count == 1
    
    def test_load_voice_not_found(self, mock_voices_dir):
        """Test loading non-existent voice raises error"""
        engine = TTSEngine(voices_dir=mock_voices_dir)
        
        with pytest.raises(ValueError) as exc_info:
            engine._load_voice("nonexistent-voice")
        
        assert "not found" in str(exc_info.value).lower()
    
    @patch('app.tts_engine._get_piper_voice')
    def test_synthesize_success(self, mock_get_piper_voice, mock_voices_dir):
        """Test successful speech synthesis"""
        mock_piper_voice = Mock()
        mock_voice_instance = Mock()
        mock_piper_voice.load.return_value = mock_voice_instance
        mock_get_piper_voice.return_value = mock_piper_voice

        def mock_synthesize(text, wav_file, **kwargs):
            wav_file.writeframes(b"fake audio data")

        mock_voice_instance.synthesize = mock_synthesize

        engine = TTSEngine(voices_dir=mock_voices_dir)
        audio_bytes = engine.synthesize(
            text="Hello world",
            voice_id="en_US-lessac-medium",
            sample_rate=22050,
            speaking_rate=1.0
        )

        assert isinstance(audio_bytes, bytes)
        assert len(audio_bytes) > 0

    @patch('app.tts_engine._get_piper_voice')
    def test_synthesize_with_speaking_rate(self, mock_get_piper_voice, mock_voices_dir):
        """Test synthesis with different speaking rates"""
        mock_piper_voice = Mock()
        mock_voice_instance = Mock()
        mock_piper_voice.load.return_value = mock_voice_instance
        mock_get_piper_voice.return_value = mock_piper_voice

        def mock_synthesize(text, wav_file, **kwargs):
            length_scale = kwargs.get('length_scale', 1.0)
            assert length_scale == 0.5  # speaking_rate=2.0 -> length_scale=0.5
            wav_file.writeframes(b"fake audio data")

        mock_voice_instance.synthesize = mock_synthesize

        engine = TTSEngine(voices_dir=mock_voices_dir)
        audio_bytes = engine.synthesize(
            text="Hello world",
            voice_id="en_US-lessac-medium",
            sample_rate=22050,
            speaking_rate=2.0  # Faster speech
        )

        assert isinstance(audio_bytes, bytes)

    @patch('app.tts_engine._get_piper_voice')
    def test_synthesize_invalid_voice(self, mock_get_piper_voice, mock_voices_dir):
        """Test synthesis with invalid voice ID"""
        mock_piper_voice = Mock()
        mock_get_piper_voice.return_value = mock_piper_voice

        engine = TTSEngine(voices_dir=mock_voices_dir)

        with pytest.raises(ValueError) as exc_info:
            engine.synthesize(
                text="Hello world",
                voice_id="invalid-voice",
                sample_rate=22050
            )

        assert "not found" in str(exc_info.value).lower()
