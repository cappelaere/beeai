"""Tests for property_registration_graph tool."""
from unittest.mock import patch

from tools import property_registration_graph


def test_returns_output(run_tool_sync, mock_post_ok):
    with patch("tools.property_registration_graph.session") as mock_session:
        mock_session.post.return_value = mock_post_ok({
            "error": 0,
            "data": [{"day": "2025-01-01", "count": 5}],
        })
        result = run_tool_sync(property_registration_graph, {"site_id": 3})
    out = str(result)
    assert "count" in out
