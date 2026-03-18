"""Tests for get_auction_types tool."""
from unittest.mock import patch

from tools import get_auction_types


def test_returns_output(run_tool_sync, mock_post_ok):
    with patch("tools.get_auction_types.session") as mock_session:
        mock_session.post.return_value = mock_post_ok({
            "error": 0,
            "data": {"data": {}, "auction_type": [{"id": 1, "auction_type": "English"}]},
        })
        result = run_tool_sync(get_auction_types, {"site_id": 3})
    out = str(result)
    assert "English" in out
