"""
Redis cache module for LLM responses.
Caches responses by prompt hash to reduce API calls and improve performance.
"""

import hashlib
import json
import logging
import os

import redis

logger = logging.getLogger(__name__)


class LLMResponseCache:
    """Cache for LLM responses using Redis."""

    def __init__(self):
        self.enabled = os.getenv("REDIS_ENABLED", "false").lower() == "true"
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.ttl = int(os.getenv("REDIS_TTL", "3600"))  # Default 1 hour
        self.client = None

        if self.enabled:
            try:
                self.client = redis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                )
                # Test connection
                self.client.ping()
                logger.info(f"✅ Redis cache connected: {self.redis_url}")
            except Exception as e:
                logger.warning(f"⚠️  Redis cache disabled due to connection error: {e}")
                self.enabled = False
                self.client = None

    def _generate_key(self, prompt: str, session_id: str = None) -> str:
        """
        Generate a cache key from the prompt.
        Includes session_id to allow per-session caching if needed.
        """
        # Create hash of prompt for consistent key
        prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]

        if session_id:
            return f"llm:prompt:session:{session_id}:{prompt_hash}"
        return f"llm:prompt:{prompt_hash}"

    def get(self, prompt: str, session_id: str = None) -> tuple[str, dict] | None:
        """
        Retrieve cached response for a prompt.

        Args:
            prompt: User's input prompt
            session_id: Optional session ID for session-specific caching

        Returns:
            Tuple of (response_text, metadata) if cached, None otherwise
        """
        if not self.enabled or not self.client:
            return None

        try:
            key = self._generate_key(prompt, session_id)
            cached_data = self.client.get(key)

            if cached_data:
                data = json.loads(cached_data)
                response_text = data.get("response")
                metadata = data.get("metadata", {})
                metadata["from_cache"] = True

                logger.info(f"🎯 Cache HIT for prompt (key: {key[:32]}...)")
                return response_text, metadata

            logger.info(f"❌ Cache MISS for prompt (key: {key[:32]}...)")
            return None

        except Exception as e:
            logger.error(f"Error retrieving from cache: {e}")
            return None

    def set(
        self,
        prompt: str,
        response: str,
        metadata: dict = None,
        session_id: str = None,
        ttl: int = None,
    ):
        """
        Cache a response for a prompt.

        Args:
            prompt: User's input prompt
            response: LLM response text
            metadata: Optional metadata dict
            session_id: Optional session ID for session-specific caching
            ttl: Time-to-live in seconds (uses default if not specified)
        """
        if not self.enabled or not self.client:
            return

        try:
            key = self._generate_key(prompt, session_id)
            cache_ttl = ttl or self.ttl

            data = {
                "response": response,
                "metadata": metadata or {},
                "prompt_length": len(prompt),
                "response_length": len(response),
            }

            self.client.setex(key, cache_ttl, json.dumps(data))

            logger.info(f"💾 Cached response for prompt (key: {key[:32]}..., TTL: {cache_ttl}s)")

        except Exception as e:
            logger.error(f"Error caching response: {e}")

    def delete(self, prompt: str, session_id: str = None):
        """Delete a cached response."""
        if not self.enabled or not self.client:
            return

        try:
            key = self._generate_key(prompt, session_id)
            self.client.delete(key)
            logger.info(f"🗑️  Deleted cache entry (key: {key[:32]}...)")
        except Exception as e:
            logger.error(f"Error deleting cache entry: {e}")

    def clear_all(self):
        """Clear all cached LLM responses (database 0 only)."""
        if not self.enabled or not self.client:
            return

        try:
            # Only delete keys matching our pattern
            pattern = "llm:prompt:*"
            keys = self.client.keys(pattern)
            if keys:
                self.client.delete(*keys)
                logger.info(f"🗑️  Cleared {len(keys)} cached responses")
            else:
                logger.info("ℹ️  No cached responses to clear")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")

    def get_stats(self) -> dict:
        """Get cache statistics."""
        if not self.enabled or not self.client:
            return {"enabled": False, "connected": False}

        try:
            # Count keys with our pattern
            pattern = "llm:prompt:*"
            keys = self.client.keys(pattern)

            info = self.client.info("stats")

            return {
                "enabled": True,
                "connected": True,
                "cached_prompts": len(keys),
                "total_hits": info.get("keyspace_hits", 0),
                "total_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0), info.get("keyspace_misses", 0)
                ),
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"enabled": True, "connected": False, "error": str(e)}

    @staticmethod
    def _calculate_hit_rate(hits: int, misses: int) -> float:
        """Calculate cache hit rate percentage."""
        total = hits + misses
        if total == 0:
            return 0.0
        return round((hits / total) * 100, 2)


# Global cache instance
_cache_instance = None


def get_cache() -> LLMResponseCache:
    """Get or create the global cache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = LLMResponseCache()
    return _cache_instance
