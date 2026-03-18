"""Tests for admin_dashboard tool."""
from unittest.mock import patch

from tools import admin_dashboard


def test_returns_output(run_tool_sync, mock_post_ok):
    with patch("tools.admin_dashboard.session") as mock_session:
        mock_session.post.return_value = mock_post_ok({
            "error": 0,
            "data": {"total_property": 10, "total_agent": 2},
        })
        result = run_tool_sync(admin_dashboard, {"site_id": 3})
    out = str(result)
    assert "total" in out
