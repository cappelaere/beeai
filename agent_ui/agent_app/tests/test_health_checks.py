"""
Tests for service health checks
"""

import os
from unittest.mock import MagicMock, patch

from django.test import Client, TestCase

from agent_app.health_checks import (
    check_all_services,
    check_api_health,
    check_piper_health,
    check_postgres_health,
    check_redis_health,
    get_overall_status,
)


class TestHealthChecks(TestCase):
    """Test service health check functions"""

    def test_postgres_health_check(self):
        """Test PostgreSQL health check"""
        result = check_postgres_health()

        # Should succeed since test database is available (or might be unhealthy in test env)
        self.assertIn("status", result)
        self.assertIn(result["status"], ["healthy", "unhealthy", "unknown"])

        # If healthy, should have expected fields
        if result["status"] == "healthy":
            self.assertIn("database", result)
            self.assertIn("response_time_ms", result)
            self.assertIn("version", result)
        else:
            # If unhealthy, should have error
            self.assertIn("error", result)

    @patch("cache.get_cache")
    def test_redis_health_check_healthy(self, mock_get_cache):
        """Test Redis health check when healthy"""
        # Mock cache with healthy stats
        mock_cache = MagicMock()
        mock_cache.get_stats.return_value = {
            "connected": True,
            "redis_version": "7.0.0",
            "memory_used": "1.5MB",
            "cached_prompts": 42,
            "hit_rate": 85.5,
        }
        mock_get_cache.return_value = mock_cache

        # Set environment variable
        with patch.dict(os.environ, {"REDIS_ENABLED": "true"}):
            result = check_redis_health()

        self.assertEqual(result["status"], "healthy")
        self.assertIn("version", result)
        self.assertEqual(result["cached_items"], 42)
        self.assertEqual(result["hit_rate"], 85.5)

    @patch("cache.get_cache")
    def test_redis_health_check_unhealthy(self, mock_get_cache):
        """Test Redis health check when unhealthy"""
        # Mock cache with disconnected status
        mock_cache = MagicMock()
        mock_cache.get_stats.return_value = {"connected": False, "error": "Connection refused"}
        mock_get_cache.return_value = mock_cache

        with patch.dict(os.environ, {"REDIS_ENABLED": "true"}):
            result = check_redis_health()

        self.assertEqual(result["status"], "unhealthy")
        self.assertIn("error", result)

    def test_redis_health_check_disabled(self):
        """Test Redis health check when disabled"""
        with patch.dict(os.environ, {"REDIS_ENABLED": "false"}):
            result = check_redis_health()

        self.assertEqual(result["status"], "disabled")
        self.assertIn("error", result)
        self.assertIn("REDIS_ENABLED=false", result["error"])

    @patch("agent_app.health_checks.requests.get")
    def test_piper_health_check_healthy(self, mock_get):
        """Test Piper TTS health check when healthy"""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok", "engine": "piper", "version": "1.0.0"}
        mock_get.return_value = mock_response

        result = check_piper_health()

        self.assertEqual(result["status"], "healthy")
        self.assertEqual(result["version"], "1.0.0")
        self.assertEqual(result["engine"], "piper")
        self.assertIn("response_time_ms", result)

    @patch("agent_app.health_checks.requests.get")
    def test_piper_health_check_unhealthy(self, mock_get):
        """Test Piper TTS health check when unhealthy"""
        import requests

        # Mock connection error
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")

        result = check_piper_health()

        self.assertEqual(result["status"], "unhealthy")
        self.assertIn("error", result)
        self.assertIn("Connection refused", result["error"])

    @patch("agent_app.health_checks.requests.get")
    def test_api_health_check_timeout(self, mock_get):
        """Test API health check with timeout"""
        import requests

        # Mock timeout
        mock_get.side_effect = requests.exceptions.Timeout("Connection timeout")

        result = check_api_health()

        self.assertEqual(result["status"], "unhealthy")
        self.assertIn("Timeout", result["error"])

    def test_check_all_services(self):
        """Test checking all services"""
        result = check_all_services()

        # Should return dict with all service keys
        self.assertIn("api", result)
        self.assertIn("piper", result)
        self.assertIn("redis", result)
        self.assertIn("postgres", result)

        # Each service should have a status
        for _service_name, service_data in result.items():
            self.assertIn("status", service_data)
            self.assertIn(service_data["status"], ["healthy", "unhealthy", "unknown", "disabled"])

    def test_get_overall_status_all_healthy(self):
        """Test overall status when all services are healthy"""
        services = {
            "api": {"status": "healthy"},
            "piper": {"status": "healthy"},
            "redis": {"status": "healthy"},
            "postgres": {"status": "healthy"},
        }

        status = get_overall_status(services)
        self.assertEqual(status, "healthy")

    def test_get_overall_status_one_unhealthy(self):
        """Test overall status when one service is unhealthy"""
        services = {
            "api": {"status": "healthy"},
            "piper": {"status": "unhealthy"},
            "redis": {"status": "healthy"},
            "postgres": {"status": "healthy"},
        }

        status = get_overall_status(services)
        self.assertEqual(status, "degraded")

    def test_get_overall_status_multiple_unhealthy(self):
        """Test overall status when multiple services are unhealthy"""
        services = {
            "api": {"status": "unhealthy"},
            "piper": {"status": "unhealthy"},
            "redis": {"status": "healthy"},
            "postgres": {"status": "healthy"},
        }

        status = get_overall_status(services)
        self.assertEqual(status, "unhealthy")

    def test_get_overall_status_with_disabled(self):
        """Test overall status with disabled services"""
        services = {
            "api": {"status": "healthy"},
            "piper": {"status": "healthy"},
            "redis": {"status": "disabled"},
            "postgres": {"status": "healthy"},
        }

        status = get_overall_status(services)
        self.assertEqual(status, "healthy")


class TestDashboardHealthDisplay(TestCase):
    """Test dashboard displays service health"""

    def setUp(self):
        """Set up test client"""
        self.client = Client()

    @patch("agent_app.health_checks.check_all_services")
    def test_dashboard_includes_service_health(self, mock_check_all):
        """Test that dashboard view includes service health data"""
        # Mock service health
        mock_check_all.return_value = {
            "api": {"status": "healthy", "url": "http://localhost:8000"},
            "piper": {"status": "healthy", "url": "http://localhost:8088"},
            "redis": {"status": "healthy", "url": "redis://localhost:6379/0"},
            "postgres": {"status": "healthy", "database": "test_db"},
        }

        response = self.client.get("/dashboard/")
        self.assertEqual(response.status_code, 200)

        # Verify service health is in context
        self.assertIn("services", response.context)
        self.assertIn("overall_status", response.context)

        # Verify all services are present
        services = response.context["services"]
        self.assertIn("api", services)
        self.assertIn("piper", services)
        self.assertIn("redis", services)
        self.assertIn("postgres", services)

    @patch("agent_app.health_checks.check_all_services")
    def test_metrics_command_includes_service_health(self, mock_check_all):
        """Test that /metrics command includes service health"""
        # Mock service health
        mock_check_all.return_value = {
            "api": {"status": "healthy", "response_time_ms": 10},
            "piper": {"status": "unhealthy", "error": "Connection refused"},
            "redis": {"status": "healthy", "response_time_ms": 5},
            "postgres": {"status": "healthy", "response_time_ms": 2},
        }

        response = self.client.post(
            "/api/chat/",
            data='{"prompt": "/metrics", "agent": "gres", "model": "claude-3-5-sonnet"}',
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertTrue(data.get("is_command"))

        # Verify service health is in response
        content = data["response"]
        self.assertIn("Service Health", content)
        self.assertIn("BidHom API", content)
        self.assertIn("Piper TTS", content)
        self.assertIn("Redis Cache", content)
        self.assertIn("Database", content)

        # Verify metadata includes services
        metadata = data.get("metadata", {})
        self.assertIn("overall_status", metadata)
        self.assertIn("services", metadata)
