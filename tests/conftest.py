"""Pytest config: path/env setup and shared fixtures. Loaded before tests."""
import asyncio
import os
import sys
from unittest.mock import Mock

import pytest

# Project root and env before any test imports tools
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

# Load .env file first (before setting defaults)
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(_root, ".env"))
except ImportError:
    pass

# Set defaults only if not already set (will use .env values if loaded)
os.environ.setdefault("API_URL", "http://127.0.0.1:8000")
os.environ.setdefault("AUTH_TOKEN", "test-token")
os.environ.setdefault("USER_ID", "1")


@pytest.fixture
def run_tool_sync():
    """Run a BeeAI tool synchronously; returns the tool output."""

    def _run(tool, input_dict: dict):
        run = tool.run(input_dict)

        async def _await_run():
            return await run

        return asyncio.run(_await_run())

    return _run


@pytest.fixture
def mock_post_ok():
    """Return a Mock response with .raise_for_status() and .json() returning the given data."""

    def _mock(json_data):
        m = Mock()
        m.raise_for_status = Mock()
        m.json.return_value = json_data
        return m

    return _mock
