"""
Health check utilities for external services
"""

import logging
import os
from typing import Any

import requests

logger = logging.getLogger(__name__)


def check_api_health() -> dict[str, Any]:
    """
    Check BidHom API health.

    Returns:
        dict: {
            "status": "healthy" | "unhealthy" | "unknown",
            "url": str,
            "response_time_ms": int,
            "error": str (if unhealthy)
        }
    """
    api_url = os.getenv("API_URL", "http://127.0.0.1:8000")
    health_endpoint = f"{api_url}/healthz"

    # Get auth token (optional - healthz endpoint doesn't require it)
    auth_token = os.getenv("AUTH_TOKEN", "")

    try:
        import time

        start = time.time()

        # Add auth header if token is available (not required for /healthz)
        headers = {}
        if auth_token:
            headers["Authorization"] = f"Token {auth_token}"

        response = requests.get(health_endpoint, headers=headers, timeout=5)
        elapsed_ms = int((time.time() - start) * 1000)

        if response.status_code == 200:
            data = (
                response.json()
                if response.headers.get("content-type", "").startswith("application/json")
                else {}
            )
            return {
                "status": "healthy",
                "url": api_url,
                "response_time_ms": elapsed_ms,
                "version": data.get("version", "Unknown"),
                "service": data.get("service", "API"),
            }
        return {
            "status": "unhealthy",
            "url": api_url,
            "response_time_ms": elapsed_ms,
            "error": f"HTTP {response.status_code}",
        }
    except requests.exceptions.Timeout:
        return {"status": "unhealthy", "url": api_url, "error": "Timeout (>5s)"}
    except requests.exceptions.ConnectionError:
        return {
            "status": "unhealthy",
            "url": api_url,
            "error": "Connection refused - Service may be stopped",
        }
    except Exception as e:
        logger.warning(f"API health check failed: {e}")
        return {"status": "unknown", "url": api_url, "error": str(e)}


def check_piper_health() -> dict[str, Any]:
    """
    Check Piper TTS service health.

    Returns:
        dict: {
            "status": "healthy" | "unhealthy" | "unknown",
            "url": str,
            "response_time_ms": int,
            "version": str,
            "error": str (if unhealthy)
        }
    """
    piper_url = os.getenv("PIPER_BASE_URL", "http://localhost:8088")
    health_endpoint = f"{piper_url}/healthz"

    try:
        import time

        start = time.time()
        response = requests.get(health_endpoint, timeout=5)
        elapsed_ms = int((time.time() - start) * 1000)

        if response.status_code == 200:
            data = response.json()
            return {
                "status": "healthy",
                "url": piper_url,
                "response_time_ms": elapsed_ms,
                "version": data.get("version", "Unknown"),
                "engine": data.get("engine", "piper"),
            }
        return {
            "status": "unhealthy",
            "url": piper_url,
            "response_time_ms": elapsed_ms,
            "error": f"HTTP {response.status_code}",
        }
    except requests.exceptions.Timeout:
        return {"status": "unhealthy", "url": piper_url, "error": "Timeout (>5s)"}
    except requests.exceptions.ConnectionError:
        return {
            "status": "unhealthy",
            "url": piper_url,
            "error": "Connection refused - Service may be stopped",
        }
    except Exception as e:
        logger.warning(f"Piper health check failed: {e}")
        return {"status": "unknown", "url": piper_url, "error": str(e)}


def check_redis_health() -> dict[str, Any]:
    """
    Check Redis cache health.

    Returns:
        dict: {
            "status": "healthy" | "unhealthy" | "unknown",
            "url": str,
            "response_time_ms": int,
            "version": str,
            "memory_used": str,
            "error": str (if unhealthy)
        }
    """
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_enabled = os.getenv("REDIS_ENABLED", "false").lower() == "true"

    if not redis_enabled:
        return {"status": "disabled", "url": redis_url, "error": "REDIS_ENABLED=false in .env"}

    try:
        import time

        from cache import get_cache

        start = time.time()
        cache = get_cache()
        stats = cache.get_stats()
        elapsed_ms = int((time.time() - start) * 1000)

        if stats.get("connected"):
            return {
                "status": "healthy",
                "url": redis_url,
                "response_time_ms": elapsed_ms,
                "version": stats.get("redis_version", "Unknown"),
                "memory_used": stats.get("memory_used", "Unknown"),
                "cached_items": stats.get("cached_prompts", 0),
                "hit_rate": stats.get("hit_rate", 0),
            }
        return {
            "status": "unhealthy",
            "url": redis_url,
            "error": stats.get("error", "Not connected"),
        }
    except ImportError:
        return {"status": "unknown", "url": redis_url, "error": "Cache module not available"}
    except Exception as e:
        logger.warning(f"Redis health check failed: {e}")
        return {"status": "unhealthy", "url": redis_url, "error": str(e)}


def check_postgres_health() -> dict[str, Any]:
    """
    Check database health (PostgreSQL or SQLite).

    Returns:
        dict: {
            "status": "healthy" | "unhealthy" | "unknown",
            "url": str,
            "response_time_ms": int,
            "version": str,
            "error": str (if unhealthy)
        }
    """
    from django.db import connection
    from django.db.utils import OperationalError

    try:
        import time

        start = time.time()

        # Get database settings
        db_settings = connection.settings_dict
        db_engine = db_settings.get("ENGINE", "Unknown")
        db_name = db_settings.get("NAME", "Unknown")

        # Determine database type and appropriate version query
        is_sqlite = "sqlite" in db_engine.lower()
        is_postgres = "postgres" in db_engine.lower()

        # Execute version query based on database type
        with connection.cursor() as cursor:
            if is_sqlite:
                cursor.execute("SELECT sqlite_version();")
                version_info = cursor.fetchone()
                version = f"SQLite {version_info[0]}" if version_info else "Unknown"
            elif is_postgres:
                cursor.execute("SELECT version();")
                version_info = cursor.fetchone()
                # Extract short version (e.g., "PostgreSQL 16.2")
                version = version_info[0].split(",")[0] if version_info else "Unknown"
            else:
                # Generic test query
                cursor.execute("SELECT 1;")
                version = "Unknown"

        elapsed_ms = int((time.time() - start) * 1000)

        return {
            "status": "healthy",
            "database": str(db_name) if not isinstance(db_name, str) else db_name,
            "engine": db_engine.split(".")[-1] if "." in db_engine else db_engine,
            "response_time_ms": elapsed_ms,
            "version": version,
        }
    except OperationalError as e:
        return {
            "status": "unhealthy",
            "database": str(db_settings.get("NAME", "Unknown")),
            "error": f"Connection error: {str(e)}",
        }
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        return {"status": "unknown", "error": str(e)}


def check_all_services() -> dict[str, dict[str, Any]]:
    """
    Check health of all external services.

    Returns:
        dict: {
            "api": {...},
            "piper": {...},
            "redis": {...},
            "postgres": {...}
        }
    """
    return {
        "api": check_api_health(),
        "piper": check_piper_health(),
        "redis": check_redis_health(),
        "postgres": check_postgres_health(),
    }


def get_overall_status(services: dict[str, dict[str, Any]]) -> str:
    """
    Get overall system health status.

    Args:
        services: Dict of service health checks

    Returns:
        "healthy" | "degraded" | "unhealthy"
    """
    statuses = [s.get("status") for s in services.values()]

    # Count status types
    healthy_count = statuses.count("healthy")
    unhealthy_count = statuses.count("unhealthy")
    disabled_count = statuses.count("disabled")
    statuses.count("unknown")

    # Calculate active services (excluding disabled)
    active_services = len(statuses) - disabled_count

    # If any critical service is unhealthy (excluding disabled), system is degraded/unhealthy
    if unhealthy_count > 0:
        # If more than half of active services are unhealthy, system is unhealthy
        if unhealthy_count >= (active_services / 2):
            return "unhealthy"
        return "degraded"
    if healthy_count == active_services:
        # All active services are healthy
        return "healthy"
    # Mix of healthy and unknown
    return "degraded"
