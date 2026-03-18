"""Tests for get_site_detail tool."""
from unittest.mock import patch

from tools import get_site_detail


def test_returns_output(run_tool_sync, mock_post_ok):
    with patch("tools.get_site_detail.session") as mock_session:
        mock_session.post.return_value = mock_post_ok({
            "error": 0,
            "data": {"id": 1, "domain_name": "example.com"},
        })
        result = run_tool_sync(get_site_detail, {"domain": "example.com"})
    out = str(result)
    assert "example" in out
