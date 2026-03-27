"""
Deferred workflow registry DB sync.

Runs workflow registry sync on the first HTTP request so Django does not
access the database during app initialization (avoids RuntimeWarning).
"""

import logging
import threading
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class _SyncState:
    """Holds workflow-sync lifecycle flags and lock ownership."""

    lock: threading.Lock = field(default_factory=threading.Lock)
    done: bool = False
    started: bool = False


_sync_state = _SyncState()


def _sync_in_background() -> None:
    """Run sync without blocking request handling."""
    ok = False
    try:
        from agent_app.workflow_registry import workflow_registry

        workflow_registry._sync_workflow_model()
        ok = True
    except Exception as e:
        logger.warning("Could not sync workflow registry to Workflow model: %s", e)
    finally:
        with _sync_state.lock:
            _sync_state.done = ok
            _sync_state.started = False


def ensure_workflow_registry_synced():
    """Start workflow registry sync once per process, without blocking requests."""
    if _sync_state.done or _sync_state.started:
        return
    with _sync_state.lock:
        if _sync_state.done or _sync_state.started:
            return
        _sync_state.started = True
    threading.Thread(target=_sync_in_background, daemon=True, name="workflow-registry-sync").start()


class WorkflowSyncMiddleware:
    """Runs workflow registry -> DB sync on first request (no DB access during app init)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ensure_workflow_registry_synced()
        return self.get_response(request)
