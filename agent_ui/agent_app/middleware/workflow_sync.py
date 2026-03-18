"""
Deferred workflow registry DB sync.

Runs workflow registry sync on the first HTTP request so Django does not
access the database during app initialization (avoids RuntimeWarning).
"""

import logging

logger = logging.getLogger(__name__)

_done = False


def ensure_workflow_registry_synced():
    """Sync workflow registry to Workflow model once per process. Safe to call from middleware."""
    global _done
    if _done:
        return
    _done = True
    try:
        from agent_app.workflow_registry import workflow_registry

        workflow_registry._sync_workflow_model()
    except Exception as e:
        logger.warning("Could not sync workflow registry to Workflow model: %s", e)


class WorkflowSyncMiddleware:
    """Runs workflow registry -> DB sync on first request (no DB access during app init)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ensure_workflow_registry_synced()
        return self.get_response(request)
