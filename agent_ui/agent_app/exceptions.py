"""
Domain exceptions for agent_app. Views map these to HTTP status and body.
"""


class AgentNotFoundError(Exception):
    """Raised when an agent id is not in the registry."""


class ValidationError(Exception):
    """Raised when request or registry data fails validation."""


class ConflictError(Exception):
    """Raised when an operation would conflict with current state (e.g. remove default agent)."""


class WorkflowNotFoundError(Exception):
    """Raised when a workflow id is not in the registry."""


class WorkflowExistsError(Exception):
    """Raised when a workflow directory already exists on create."""
