"""Tests for property_count_summary tool."""
from unittest.mock import patch

from tools import property_count_summary


def test_returns_output(run_tool_sync, mock_post_ok):
    with patch("tools.property_count_summary.session") as mock_session:
        mock_session.post.return_value = mock_post_ok({
            "error": 0,
            "data": {"data": {"data": [], "total": 42}},
        })
        result = run_tool_sync(property_count_summary, {"site_id": 3})
    out = str(result)
    assert "42" in out
    assert "total" in out
