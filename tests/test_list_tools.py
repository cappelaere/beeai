"""Tests for list_available_tools and get_tools_list."""
from tools import list_available_tools, get_tools_list


def test_list_available_tools_returns_list(run_tool_sync):
    result = run_tool_sync(list_available_tools, {})
    out = str(result)
    assert "Available tools" in out
    assert "list_properties" in out
    assert "list_agents_summary" in out
    assert "get_property_detail" in out
    assert "list_available_tools" not in out


def test_get_tools_list_returns_tuples():
    tools_list = get_tools_list()
    assert len(tools_list) >= 15
    names = [n for n, _ in tools_list]
    assert "list_properties" in names
    assert "get_property_detail" in names
    for name, desc in tools_list:
        assert isinstance(name, str)
        assert isinstance(desc, str)
        assert len(name) > 0
