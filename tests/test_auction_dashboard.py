"""Tests for auction_dashboard tool."""
from unittest.mock import patch

from tools import auction_dashboard


def test_returns_output(run_tool_sync, mock_post_ok):
    with patch("tools.auction_dashboard.session") as mock_session:
        mock_session.post.return_value = mock_post_ok({
            "error": 0,
            "data": {"data": [], "total": 0},
        })
        result = run_tool_sync(auction_dashboard, {
            "domain_id": 3, "user_id": 1, "page": 1, "page_size": 10
        })
    out = str(result)
    assert "data" in out
