"""Tests for list_properties tool."""
from unittest.mock import patch

from tools import list_properties


def test_returns_output(run_tool_sync, mock_post_ok):
    with patch("tools.list_properties.session") as mock_session:
        mock_session.post.return_value = mock_post_ok({
            "error": 0,
            "data": {"data": [{"id": 1, "name": "Prop A", "city": "NYC"}], "total": 1},
        })
        result = run_tool_sync(list_properties, {"site_id": 3, "page_size": 5, "page": 1})
    out = str(result)
    assert "site_id" in out
    assert "properties" in out
