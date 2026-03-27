"""
Analytics models stored under agent_app.
"""

from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone


class TrackedPage(models.Model):
    """
    Explicit registry of pages eligible for analytics event capture.
    """

    key = models.SlugField(max_length=100, unique=True, db_index=True)
    canonical_path = models.CharField(max_length=255, unique=True, db_index=True)
    name = models.CharField(max_length=255, blank=True)
    enabled = models.BooleanField(default=True, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["canonical_path"]
        indexes = [
            models.Index(fields=["enabled", "canonical_path"]),
        ]

    def __str__(self):
        return f"{self.canonical_path} ({'enabled' if self.enabled else 'disabled'})"


class TrackedPageQueryParam(models.Model):
    """
    Allowlisted query params to keep for a tracked page.
    """

    tracked_page = models.ForeignKey(
        TrackedPage, on_delete=models.CASCADE, related_name="allowed_query_params"
    )
    param_name = models.CharField(max_length=100, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["param_name"]
        unique_together = [["tracked_page", "param_name"]]
        indexes = [
            models.Index(fields=["tracked_page", "param_name"]),
        ]

    def save(self, *args, **kwargs):
        self.param_name = (self.param_name or "").strip().lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.tracked_page.canonical_path}?{self.param_name}=..."


class PageViewEvent(models.Model):
    """
    Raw analytics event for page views.
    """

    SOURCE_PROXY_HEADER = "proxy_header"
    SOURCE_CLIENT = "client"
    SOURCE_UNKNOWN = "unknown"
    LOCATION_SOURCE_CHOICES = [
        (SOURCE_PROXY_HEADER, "Proxy header"),
        (SOURCE_CLIENT, "Client"),
        (SOURCE_UNKNOWN, "Unknown"),
    ]

    event_time = models.DateTimeField(default=timezone.now, db_index=True)
    tracked_page = models.ForeignKey(TrackedPage, on_delete=models.CASCADE, related_name="events")
    canonical_path = models.CharField(max_length=255, db_index=True)

    # Attribution (privacy-conscious, no IP).
    session_key_hash = models.CharField(max_length=64, blank=True, db_index=True)
    visitor_id = models.CharField(max_length=128, blank=True, db_index=True)
    app_user_id = models.IntegerField(null=True, blank=True, db_index=True)
    auth_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )

    # Request metadata.
    referrer = models.CharField(max_length=512, blank=True)
    user_agent = models.CharField(max_length=512, blank=True)
    query_params_filtered = models.JSONField(default=dict, blank=True)

    # Location (no IP storage).
    location_city = models.CharField(max_length=120, blank=True)
    location_state = models.CharField(max_length=120, blank=True)
    location_country = models.CharField(max_length=120, blank=True, db_index=True)
    location_source = models.CharField(
        max_length=20, choices=LOCATION_SOURCE_CHOICES, default=SOURCE_UNKNOWN
    )

    class Meta:
        ordering = ["-event_time"]
        indexes = [
            models.Index(fields=["tracked_page", "-event_time"]),
            models.Index(fields=["canonical_path", "-event_time"]),
            models.Index(fields=["app_user_id", "-event_time"]),
            models.Index(fields=["visitor_id", "-event_time"]),
        ]

    def __str__(self):
        return f"{self.canonical_path} @ {self.event_time.isoformat()}"
