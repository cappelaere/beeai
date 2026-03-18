"""
Django Channels WebSocket routing for workflow execution
"""

from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/workflow/(?P<run_id>[a-z0-9]{8})/$", consumers.WorkflowConsumer.as_asgi()),
    re_path(r"ws/workflows/(?P<run_id>[a-z0-9]{8})/$", consumers.WorkflowConsumer.as_asgi()),
]
