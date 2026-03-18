"""Tests for Audio Cache Manager"""
import pytest
import time
import tempfile
from pathlib import Path

from app.audio_cache import AudioCache


class TestAudioCache:
    """Test Audio Cache functionality"""
    
    @pytest.fixture
    def cache(self):
        """Create cache with temporary directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            yield AudioCache(cache_dir=cache_dir)
    
    def test_cache_initialization(self, cache):
        """Test cache initializes correctly"""
        assert cache.cache_dir.exists()
        assert isinstance(cache.metadata, dict)
    
    def test_save_and_retrieve_audio(self, cache):
        """Test saving and retrieving audio"""
        audio_data = b"fake wav data"
        content_type = "audio/wav"
        
        # Save audio
        audio_id, audio_url = cache.save_audio(
            audio_bytes=audio_data,
            content_type=content_type,
            ttl_seconds=3600
        )
        
        assert audio_id is not None
        assert audio_url == f"/v1/audio/{audio_id}"
        
        # Retrieve audio
        result = cache.get_audio(audio_id)
        assert result is not None
        retrieved_data, retrieved_type = result
        assert retrieved_data == audio_data
        assert retrieved_type == content_type
    
    def test_audio_file_created_on_disk(self, cache):
        """Test audio file is actually written to disk"""
        audio_data = b"fake wav data"
        
        audio_id, _ = cache.save_audio(
            audio_bytes=audio_data,
            content_type="audio/wav",
            ttl_seconds=3600
        )
        
        # Check file exists
        audio_file = cache.cache_dir / f"{audio_id}.wav"
        assert audio_file.exists()
        
        # Verify content
        with open(audio_file, 'rb') as f:
            assert f.read() == audio_data
    
    def test_metadata_persistence(self, cache):
        """Test metadata is saved to disk"""
        audio_data = b"fake wav data"
        
        cache.save_audio(
            audio_bytes=audio_data,
            content_type="audio/wav",
            ttl_seconds=3600
        )
        
        # Check metadata file exists
        assert cache.metadata_file.exists()
        
        # Create new cache instance (loads from disk)
        new_cache = AudioCache(cache_dir=cache.cache_dir)
        assert len(new_cache.metadata) == 1
    
    def test_get_nonexistent_audio(self, cache):
        """Test retrieving non-existent audio returns None"""
        result = cache.get_audio("nonexistent-id")
        assert result is None
    
    def test_audio_expiry(self, cache):
        """Test expired audio is not returned"""
        audio_data = b"fake wav data"
        
        # Save with very short TTL
        audio_id, _ = cache.save_audio(
            audio_bytes=audio_data,
            content_type="audio/wav",
            ttl_seconds=1  # 1 second
        )
        
        # Should be retrievable immediately
        result = cache.get_audio(audio_id)
        assert result is not None
        
        # Wait for expiry
        time.sleep(1.5)
        
        # Should now return None
        result = cache.get_audio(audio_id)
        assert result is None
    
    def test_cleanup_expired_files(self, cache):
        """Test cleanup removes expired files"""
        # Save audio with short TTL
        audio_id1, _ = cache.save_audio(
            audio_bytes=b"data1",
            content_type="audio/wav",
            ttl_seconds=1
        )
        
        # Save audio with long TTL
        audio_id2, _ = cache.save_audio(
            audio_bytes=b"data2",
            content_type="audio/wav",
            ttl_seconds=3600
        )
        
        assert len(cache.metadata) == 2
        
        # Wait for first to expire
        time.sleep(1.5)
        
        # Run cleanup
        removed = cache.cleanup_expired()
        
        assert removed == 1
        assert len(cache.metadata) == 1
        assert audio_id2 in cache.metadata
        assert audio_id1 not in cache.metadata
    
    def test_cleanup_removes_orphaned_files(self, cache):
        """Test cleanup deletes both metadata and files"""
        audio_data = b"fake wav data"
        
        audio_id, _ = cache.save_audio(
            audio_bytes=audio_data,
            content_type="audio/wav",
            ttl_seconds=1
        )
        
        audio_file = cache.cache_dir / f"{audio_id}.wav"
        assert audio_file.exists()
        
        # Wait for expiry
        time.sleep(1.5)
        
        # Cleanup
        cache.cleanup_expired()
        
        # File should be deleted
        assert not audio_file.exists()
    
    def test_get_stats(self, cache):
        """Test cache statistics"""
        # Empty cache
        stats = cache.get_stats()
        assert stats["total_files"] == 0
        assert stats["active_files"] == 0
        assert stats["total_size_bytes"] == 0
        
        # Add some files
        cache.save_audio(b"data1" * 100, "audio/wav", ttl_seconds=3600)
        cache.save_audio(b"data2" * 200, "audio/wav", ttl_seconds=1)
        
        stats = cache.get_stats()
        assert stats["total_files"] == 2
        assert stats["active_files"] == 2
        assert stats["total_size_bytes"] > 0
        
        # Wait for one to expire
        time.sleep(1.5)
        
        # Stats still show both (cleanup not run)
        stats = cache.get_stats()
        assert stats["total_files"] == 2
        assert stats["active_files"] == 1  # Only one still valid
    
    def test_multiple_saves_unique_ids(self, cache):
        """Test multiple saves generate unique IDs"""
        audio_data = b"fake wav data"
        
        id1, _ = cache.save_audio(audio_data, "audio/wav", ttl_seconds=3600)
        id2, _ = cache.save_audio(audio_data, "audio/wav", ttl_seconds=3600)
        id3, _ = cache.save_audio(audio_data, "audio/wav", ttl_seconds=3600)
        
        # All IDs should be unique
        assert len({id1, id2, id3}) == 3
    
    def test_content_type_preservation(self, cache):
        """Test different content types are preserved"""
        wav_data = b"wav data"
        mp3_data = b"mp3 data"
        
        wav_id, _ = cache.save_audio(wav_data, "audio/wav", ttl_seconds=3600)
        mp3_id, _ = cache.save_audio(mp3_data, "audio/mpeg", ttl_seconds=3600)
        
        # Retrieve and check types
        wav_result = cache.get_audio(wav_id)
        mp3_result = cache.get_audio(mp3_id)
        
        assert wav_result[1] == "audio/wav"
        assert mp3_result[1] == "audio/mpeg"
        
        # Check file extensions
        wav_file = cache.cache_dir / f"{wav_id}.wav"
        mp3_file = cache.cache_dir / f"{mp3_id}.mp3"
        
        assert wav_file.exists()
        assert mp3_file.exists()
