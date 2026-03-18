"""Tests for list_agents_summary tool."""
from unittest.mock import patch

from tools import list_agents_summary


def test_returns_output(run_tool_sync, mock_post_ok):
    with patch("tools.list_agents.session") as mock_session:
        mock_session.post.return_value = mock_post_ok({
            "data": {"data": {"data": [], "total": 0}},
        })
        result = run_tool_sync(list_agents_summary, {"site_id": 3, "page_size": 10})
    out = str(result)
    assert "site_id" in out
