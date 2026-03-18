"""Tests for list_asset_types tool."""
from unittest.mock import patch

from tools import list_asset_types


def test_returns_output(run_tool_sync, mock_post_ok):
    with patch("tools.list_asset_types.session") as mock_session:
        mock_session.post.return_value = mock_post_ok({
            "error": 0,
            "data": [{"id": 1, "name": "Land"}],
        })
        result = run_tool_sync(list_asset_types, {})
    out = str(result)
    assert "Land" in out
