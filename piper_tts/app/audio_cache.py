"""Filesystem-based audio cache manager"""
import json
import time
import uuid
from pathlib import Path
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import logging

from app.config import config

logger = logging.getLogger(__name__)


class AudioCache:
    """Manages cached audio files with TTL"""
    
    def __init__(self, cache_dir: Path = None):
        self.cache_dir = cache_dir or config.AUDIO_CACHE_DIR
        self.metadata_file = self.cache_dir / config.METADATA_FILE
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._load_metadata()
    
    def _load_metadata(self):
        """Load metadata from disk"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    self.metadata = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load metadata: {e}, starting fresh")
                self.metadata = {}
        else:
            self.metadata = {}
    
    def _save_metadata(self):
        """Save metadata to disk"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
    
    def save_audio(
        self, 
        audio_bytes: bytes, 
        content_type: str, 
        ttl_seconds: int = None
    ) -> Tuple[str, str]:
        """
        Save audio to cache and return (audio_id, audio_url)
        
        Args:
            audio_bytes: Audio file content
            content_type: MIME type (e.g., 'audio/wav')
            ttl_seconds: Time to live in seconds
            
        Returns:
            Tuple of (audio_id, audio_url)
        """
        audio_id = str(uuid.uuid4())
        
        # Determine file extension from content type
        extension = "wav" if "wav" in content_type else "mp3"
        filename = f"{audio_id}.{extension}"
        filepath = self.cache_dir / filename
        
        # Write audio file
        with open(filepath, 'wb') as f:
            f.write(audio_bytes)
        
        # Calculate expiry time
        ttl = ttl_seconds or config.DEFAULT_CACHE_TTL_SECONDS
        expiry_timestamp = time.time() + ttl
        
        # Store metadata
        self.metadata[audio_id] = {
            "filename": filename,
            "content_type": content_type,
            "expiry_timestamp": expiry_timestamp,
            "created_at": time.time(),
            "size_bytes": len(audio_bytes)
        }
        self._save_metadata()
        
        audio_url = f"/v1/audio/{audio_id}"
        logger.info(f"Cached audio {audio_id}, expires in {ttl}s")
        
        return audio_id, audio_url
    
    def get_audio(self, audio_id: str) -> Optional[Tuple[bytes, str]]:
        """
        Retrieve audio from cache
        
        Args:
            audio_id: Audio identifier
            
        Returns:
            Tuple of (audio_bytes, content_type) or None if not found/expired
        """
        if audio_id not in self.metadata:
            logger.debug(f"Audio {audio_id} not found in metadata")
            return None
        
        meta = self.metadata[audio_id]
        
        # Check if expired
        if time.time() > meta["expiry_timestamp"]:
            logger.info(f"Audio {audio_id} has expired, removing")
            self._remove_audio(audio_id)
            return None
        
        # Read audio file
        filepath = self.cache_dir / meta["filename"]
        if not filepath.exists():
            logger.warning(f"Audio file missing: {filepath}")
            del self.metadata[audio_id]
            self._save_metadata()
            return None
        
        with open(filepath, 'rb') as f:
            audio_bytes = f.read()
        
        return audio_bytes, meta["content_type"]
    
    def _remove_audio(self, audio_id: str):
        """Remove audio file and metadata"""
        if audio_id in self.metadata:
            meta = self.metadata[audio_id]
            filepath = self.cache_dir / meta["filename"]
            
            # Delete file
            if filepath.exists():
                try:
                    filepath.unlink()
                    logger.debug(f"Deleted audio file: {filepath}")
                except Exception as e:
                    logger.error(f"Failed to delete {filepath}: {e}")
            
            # Remove metadata
            del self.metadata[audio_id]
            self._save_metadata()
    
    def cleanup_expired(self) -> int:
        """
        Remove expired audio files
        
        Returns:
            Number of files removed
        """
        current_time = time.time()
        expired_ids = []
        
        for audio_id, meta in self.metadata.items():
            if current_time > meta["expiry_timestamp"]:
                expired_ids.append(audio_id)
        
        for audio_id in expired_ids:
            self._remove_audio(audio_id)
        
        if expired_ids:
            logger.info(f"Cleaned up {len(expired_ids)} expired audio files")
        
        return len(expired_ids)
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        total_size = sum(meta.get("size_bytes", 0) for meta in self.metadata.values())
        current_time = time.time()
        active_count = sum(1 for meta in self.metadata.values() 
                          if current_time <= meta["expiry_timestamp"])
        
        return {
            "total_files": len(self.metadata),
            "active_files": active_count,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2)
        }


# Global cache instance
_cache_instance: Optional[AudioCache] = None


def get_cache() -> AudioCache:
    """Get or create global cache instance"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = AudioCache()
    return _cache_instance
