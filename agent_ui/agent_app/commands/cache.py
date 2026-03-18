"""
/cache command handler - Manage Redis cache
"""


def handle_cache(request, args, session_key):
    """
    Handle cache-related commands.

    Commands:
        /cache - Show cache statistics
        /cache clear - Clear all cached responses
        /cache stats - Show detailed cache statistics

    Args:
        request: Django HTTP request
        args: Command arguments
        session_key: User session key

    Returns:
        Dictionary with content and metadata
    """
    import logging

    logger = logging.getLogger(__name__)

    # Import cache module
    try:
        from cache import get_cache
    except ModuleNotFoundError:
        return {
            "content": "❌ Cache module not available. Redis may not be configured.",
            "metadata": {"error": True, "command": "cache"},
        }

    if not args or args[0] == "stats":
        # Show cache statistics
        try:
            cache = get_cache()
            stats = cache.get_stats()

            if not stats.get("enabled"):
                return {
                    "content": "ℹ️ Redis cache is not enabled.",
                    "metadata": {"command": "cache stats", "enabled": False},
                }

            if not stats.get("connected"):
                return {
                    "content": "❌ Redis cache is not connected.",
                    "metadata": {"command": "cache stats", "connected": False},
                }

            # Format statistics
            lines = ["📊 Cache Statistics", ""]
            lines.append("Status: ✅ Connected")
            lines.append(f"Cached Prompts: {stats.get('cached_prompts', 0):,}")
            lines.append(f"Total Hits: {stats.get('total_hits', 0):,}")
            lines.append(f"Total Misses: {stats.get('total_misses', 0):,}")

            # Show hit rate from stats
            hit_rate = stats.get("hit_rate", 0)
            lines.append(f"Hit Rate: {hit_rate}%")
            lines.append("")
            lines.append("💡 Use `/cache clear` to clear all cached responses")

            return {
                "content": "\n".join(lines),
                "metadata": {"command": "cache stats", "stats": stats},
            }

        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {
                "content": f"❌ Error getting cache statistics: {str(e)}",
                "metadata": {"error": True, "command": "cache stats"},
            }

    if args[0] == "clear":
        # Clear cache
        try:
            cache = get_cache()

            if not cache.enabled:
                return {
                    "content": "ℹ️ Cache is not enabled.",
                    "metadata": {"command": "cache clear", "enabled": False},
                }

            # Get stats before clearing
            before_stats = cache.get_stats()
            keys_before = before_stats.get("total_keys", 0)

            # Clear all cached responses
            cache.clear_all()

            # Get stats after clearing
            after_stats = cache.get_stats()
            keys_after = after_stats.get("total_keys", 0)
            keys_cleared = keys_before - keys_after

            logger.info(f"🗑️ Cleared {keys_cleared} keys from Redis cache")

            return {
                "content": f"✅ Cache cleared successfully!\n\nRemoved {keys_cleared} cached responses.",
                "metadata": {
                    "command": "cache clear",
                    "keys_cleared": keys_cleared,
                    "before": before_stats,
                    "after": after_stats,
                },
            }

        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return {
                "content": f"❌ Error clearing cache: {str(e)}",
                "metadata": {"error": True, "command": "cache clear"},
            }

    # Unknown subcommand
    return {
        "content": "Usage:\n  /cache - Show cache statistics\n  /cache stats - Show detailed statistics\n  /cache clear - Clear all cached responses",
        "metadata": {"error": True, "command": "cache"},
    }
