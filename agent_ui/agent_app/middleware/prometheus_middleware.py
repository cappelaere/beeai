"""
Prometheus Metrics Middleware

Automatically tracks HTTP requests and response times.
"""

import time

from agent_app.metrics_collector import http_request_duration_seconds, http_requests_total


class PrometheusMiddleware:
    """
    Middleware to track HTTP request metrics for Prometheus.

    Tracks:
    - Total HTTP requests by method, endpoint, and status
    - HTTP request duration by method and endpoint
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip metrics endpoints to avoid self-tracking
        if request.path in ("/metrics/", "/metrics/bi/"):
            return self.get_response(request)

        # Start timer
        start_time = time.time()

        # Process request
        response = self.get_response(request)

        # Calculate duration
        duration = time.time() - start_time

        # Get endpoint (simplified path without IDs)
        endpoint = self._get_endpoint(request.path)

        # Track metrics
        http_requests_total.labels(
            method=request.method, endpoint=endpoint, status=response.status_code
        ).inc()

        http_request_duration_seconds.labels(method=request.method, endpoint=endpoint).observe(
            duration
        )

        return response

    def _get_endpoint(self, path):
        """
        Simplify path to endpoint pattern.
        Replaces IDs and UUIDs with placeholders.
        """
        import re

        # Replace UUIDs with {uuid}
        path = re.sub(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", "{uuid}", path
        )

        # Replace numeric IDs with {id}
        path = re.sub(r"/\d+/", "/{id}/", path)

        # Replace log file names with {filename}
        if "/api/logs/" in path and path != "/api/logs/":
            path = "/api/logs/{filename}/"

        return path
