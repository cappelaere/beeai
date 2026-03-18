"""Tests for get_property_detail tool."""
from unittest.mock import patch

from tools import get_property_detail


def test_returns_output(run_tool_sync, mock_post_ok):
    with patch("tools.get_property_detail.session") as mock_session:
        mock_session.post.return_value = mock_post_ok({
            "error": 0,
            "data": {"id": 100, "name": "Detail Prop", "status": 1},
        })
        result = run_tool_sync(get_property_detail, {"property_id": 100, "site_id": 3})
    out = str(result)
    assert "100" in out
    assert "Detail" in out
