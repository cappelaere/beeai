"""Tests for FastAPI endpoints"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock

from app.main import app
from app.models import Voice, Gender

client = TestClient(app)


class TestHealthCheck:
    """Test /healthz endpoint"""
    
    def test_health_check_success(self):
        """Test health check returns OK"""
        response = client.get("/healthz")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["engine"] == "piper"
        assert "version" in data


class TestVoicesEndpoint:
    """Test /v1/voices endpoint"""
    
    @patch('app.main.get_engine')
    def test_list_voices_success(self, mock_get_engine):
        """Test listing all voices"""
        mock_engine = Mock()
        mock_engine.get_available_voices.return_value = [
            Voice(
                id="en_US-lessac-medium",
                name="English US Female",
                language_code="en-US",
                gender=Gender.FEMALE,
                sample_rates=[16000, 22050],
                engines=["standard"]
            )
        ]
        mock_get_engine.return_value = mock_engine
        
        response = client.get("/v1/voices")
        assert response.status_code == 200
        data = response.json()
        assert "voices" in data
        assert len(data["voices"]) == 1
        assert data["voices"][0]["id"] == "en_US-lessac-medium"
    
    @patch('app.main.get_engine')
    def test_list_voices_with_language_filter(self, mock_get_engine):
        """Test listing voices with language filter"""
        mock_engine = Mock()
        mock_engine.get_available_voices.return_value = [
            Voice(
                id="en_US-lessac-medium",
                name="English US Female",
                language_code="en-US",
                gender=Gender.FEMALE
            )
        ]
        mock_get_engine.return_value = mock_engine
        
        response = client.get("/v1/voices?language_code=en-US")
        assert response.status_code == 200
        mock_engine.get_available_voices.assert_called_once_with(language_code="en-US")


class TestSynthesizeEndpoint:
    """Test /v1/tts/synthesize endpoint"""
    
    @patch('app.main.get_engine')
    def test_synthesize_bytes_mode(self, mock_get_engine):
        """Test synthesis with bytes return mode"""
        mock_engine = Mock()
        mock_audio = b"RIFF....fake wav data...."
        mock_engine.synthesize.return_value = mock_audio
        mock_get_engine.return_value = mock_engine
        
        response = client.post(
            "/v1/tts/synthesize",
            json={
                "text": "Hello world",
                "voice_id": "en_US-lessac-medium",
                "return_mode": "bytes"
            }
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/wav"
        assert response.content == mock_audio
        mock_engine.synthesize.assert_called_once()
    
    @patch('app.main.get_cache')
    @patch('app.main.get_engine')
    def test_synthesize_url_mode(self, mock_get_engine, mock_get_cache):
        """Test synthesis with URL return mode"""
        mock_engine = Mock()
        mock_audio = b"RIFF....fake wav data...."
        mock_engine.synthesize.return_value = mock_audio
        mock_get_engine.return_value = mock_engine
        
        mock_cache = Mock()
        mock_cache.save_audio.return_value = ("abc123", "/v1/audio/abc123")
        mock_get_cache.return_value = mock_cache
        
        response = client.post(
            "/v1/tts/synthesize",
            json={
                "text": "Hello world",
                "voice_id": "en_US-lessac-medium",
                "return_mode": "url",
                "cache_ttl_seconds": 3600
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["audio_id"] == "abc123"
        assert data["audio_url"] == "/v1/audio/abc123"
        assert data["content_type"] == "audio/wav"
        assert data["expires_in"] == 3600
    
    @patch('app.main.get_engine')
    def test_synthesize_invalid_voice(self, mock_get_engine):
        """Test synthesis with invalid voice ID"""
        mock_engine = Mock()
        mock_engine.synthesize.side_effect = ValueError("Voice 'invalid' not found")
        mock_get_engine.return_value = mock_engine
        
        response = client.post(
            "/v1/tts/synthesize",
            json={
                "text": "Hello world",
                "voice_id": "invalid-voice"
            }
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "InvalidVoiceIdException"
    
    def test_synthesize_text_too_long(self):
        """Test synthesis with text exceeding max length"""
        long_text = "a" * 9000  # Exceeds 8000 char limit
        
        response = client.post(
            "/v1/tts/synthesize",
            json={
                "text": long_text,
                "voice_id": "en_US-lessac-medium"
            }
        )
        
        assert response.status_code == 422
    
    def test_synthesize_unsupported_format(self):
        """Test synthesis with unsupported output format"""
        response = client.post(
            "/v1/tts/synthesize",
            json={
                "text": "Hello world",
                "voice_id": "en_US-lessac-medium",
                "output_format": "mp3"
            }
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "error" in data
        assert "UnsupportedFormatException" in data["error"]["code"]


class TestCachedAudioEndpoint:
    """Test /v1/audio/{audio_id} endpoint"""
    
    @patch('app.main.get_cache')
    def test_get_cached_audio_success(self, mock_get_cache):
        """Test retrieving cached audio"""
        mock_cache = Mock()
        mock_audio = b"RIFF....fake wav data...."
        mock_cache.get_audio.return_value = (mock_audio, "audio/wav")
        mock_get_cache.return_value = mock_cache
        
        response = client.get("/v1/audio/abc123")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/wav"
        assert response.content == mock_audio
    
    @patch('app.main.get_cache')
    def test_get_cached_audio_not_found(self, mock_get_cache):
        """Test retrieving non-existent audio"""
        mock_cache = Mock()
        mock_cache.get_audio.return_value = None
        mock_get_cache.return_value = mock_cache
        
        response = client.get("/v1/audio/nonexistent")
        
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "AudioNotFoundException"


class TestStatsEndpoint:
    """Test /stats endpoint (internal)"""
    
    @patch('app.main.get_cache')
    @patch('app.main.get_engine')
    def test_stats_endpoint(self, mock_get_engine, mock_get_cache):
        """Test stats endpoint returns service info"""
        mock_engine = Mock()
        mock_engine.get_available_voices.return_value = [Mock(), Mock()]
        mock_engine._loaded_models = {"voice1": Mock()}
        mock_get_engine.return_value = mock_engine
        
        mock_cache = Mock()
        mock_cache.get_stats.return_value = {
            "total_files": 5,
            "active_files": 3,
            "total_size_bytes": 1024000
        }
        mock_get_cache.return_value = mock_cache
        
        response = client.get("/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "cache" in data
        assert "voices" in data
        assert data["voices"]["total"] == 2
        assert data["cache"]["total_files"] == 5
