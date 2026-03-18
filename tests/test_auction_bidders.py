"""Tests for auction_bidders tool."""
from unittest.mock import patch

from tools import auction_bidders


def test_returns_output(run_tool_sync, mock_post_ok):
    with patch("tools.auction_bidders.session") as mock_session:
        mock_session.post.return_value = mock_post_ok({
            "error": 0,
            "data": {"data": [], "total": 0, "property_detail": {}},
        })
        result = run_tool_sync(auction_bidders, {
            "property_id": 100, "site_id": 3, "user_id": 1
        })
    out = str(result)
    assert "data" in out
