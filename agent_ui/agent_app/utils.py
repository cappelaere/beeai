"""
Utility functions for agent_app
"""

import uuid


def generate_short_run_id():
    """
    Generate a unique 8-character run identifier for workflow executions.

    Returns:
        str: 8-character lowercase alphanumeric identifier (e.g., "a1b2c3d4")

    Raises:
        RuntimeError: If unable to generate unique ID after 10 attempts
    """
    from .models import WorkflowRun

    max_attempts = 10
    for _ in range(max_attempts):
        # Generate 8-character ID from UUID4
        run_id = uuid.uuid4().hex[:8]

        # Check for uniqueness
        if not WorkflowRun.objects.filter(run_id=run_id).exists():
            return run_id

    raise RuntimeError(f"Failed to generate unique run_id after {max_attempts} attempts")
