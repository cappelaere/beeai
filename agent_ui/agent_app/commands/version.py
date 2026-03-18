"""
/version command handler - Display application version
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def get_version():
    """Read version from VERSION file in project root."""
    try:
        version_file = Path(__file__).resolve().parent.parent.parent.parent.parent / "VERSION"
        if version_file.exists():
            return version_file.read_text().strip()
    except Exception as e:
        logger.debug("Could not read VERSION file: %s", e)
    return "1.0.0"


def handle_version(request, args, session_key):
    """
    Display application version.

    Args:
        request: Django HTTP request
        args: Command arguments (unused)
        session_key: User session key

    Returns:
        Dictionary with content and metadata
    """
    version = get_version()

    return {
        "content": f"BeeAI RealtyIQ Agent v{version}",
        "metadata": {"command": "version", "version": version},
    }
