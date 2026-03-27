"""
Middleware for first-party website analytics.
"""

from __future__ import annotations

from .services import should_consider_request_for_pageview, try_create_page_view_event


class WebsiteAnalyticsMiddleware:
    """
    Capture page-view events for tracked pages.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if should_consider_request_for_pageview(request, response):
            try_create_page_view_event(request)
        return response

