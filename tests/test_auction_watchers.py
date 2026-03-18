"""Tests for auction_watchers tool."""
from unittest.mock import patch

from tools import auction_watchers


def test_returns_output(run_tool_sync, mock_post_ok):
    with patch("tools.auction_watchers.session") as mock_session:
        mock_session.post.return_value = mock_post_ok({
            "error": 0,
            "data": {"data": [], "total": 0, "total_watcher": 0},
        })
        result = run_tool_sync(auction_watchers, {
            "property_id": 100, "site_id": 3, "user_id": 1
        })
    out = str(result)
    assert "data" in out
