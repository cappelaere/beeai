"""Tests for bid_history tool."""
from unittest.mock import patch

from tools import bid_history


def test_returns_output(run_tool_sync, mock_post_ok):
    with patch("tools.bid_history.session") as mock_session:
        mock_session.post.return_value = mock_post_ok({
            "error": 0,
            "data": {"data": []},
        })
        result = run_tool_sync(bid_history, {"property_id": 100, "domain_id": 3})
    out = str(result)
    assert "data" in out
