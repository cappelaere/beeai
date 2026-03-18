"""
Tests for BI Agent configuration and tools.
"""

import sys
from pathlib import Path

from django.test import TestCase

# Add agents directory to path
_AGENTS_DIR = Path(__file__).parent.parent.parent.parent / "agents"
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))


class BIAgentTests(TestCase):
    """Test BI Agent configuration and integration"""

    def test_bi_agent_import(self):
        """Verify BI Agent can be imported"""
        from agents.bi.agent import BI_AGENT_CONFIG

        self.assertIsNotNone(BI_AGENT_CONFIG)

    def test_bi_agent_config(self):
        """Verify BI Agent configuration"""
        from agents.bi.agent import BI_AGENT_CONFIG

        self.assertEqual(BI_AGENT_CONFIG.name, "BI Agent")
        self.assertEqual(BI_AGENT_CONFIG.icon, "📊")
        self.assertIn("property performance", BI_AGENT_CONFIG.description.lower())
        self.assertIn("metrics", BI_AGENT_CONFIG.description.lower())
        self.assertIsNotNone(BI_AGENT_CONFIG.tools)
        self.assertGreater(len(BI_AGENT_CONFIG.tools), 0)

    def test_bi_agent_has_think_tool(self):
        """Verify BI Agent includes Think tool"""
        from beeai_framework.tools.think import ThinkTool

        from agents.bi.agent import BI_AGENT_CONFIG

        has_think = any(isinstance(tool, ThinkTool) for tool in BI_AGENT_CONFIG.tools)
        self.assertTrue(has_think, "BI Agent should include ThinkTool")

    def test_bi_agent_has_duckduckgo_tool(self):
        """Verify BI Agent includes DuckDuckGo tool"""
        from beeai_framework.tools.search.duckduckgo import DuckDuckGoSearchTool

        from agents.bi.agent import BI_AGENT_CONFIG

        has_duckduckgo = any(
            isinstance(tool, DuckDuckGoSearchTool) for tool in BI_AGENT_CONFIG.tools
        )
        self.assertTrue(has_duckduckgo, "BI Agent should include DuckDuckGoSearchTool")

    def test_bi_agent_has_metrics_tools(self):
        """Verify BI Agent includes metrics tools (by name)"""
        from agents.bi.agent import BI_AGENT_CONFIG

        tool_names = [
            getattr(t, "name", None) or getattr(t, "__name__", str(type(t).__name__))
            for t in BI_AGENT_CONFIG.tools
        ]
        self.assertIn("get_metrics_property_summary", tool_names)
        self.assertIn("get_metrics_property_daily", tool_names)
        self.assertIn("get_metrics_top_properties", tool_names)
        self.assertIn("get_metrics_underperforming", tool_names)
        self.assertIn("get_metrics_properties_with_activity", tool_names)
        self.assertIn("get_metrics_event_types", tool_names)

    def test_bi_agent_instructions(self):
        """Verify BI Agent has proper instructions"""
        from agents.bi.agent import BI_AGENT_CONFIG

        instructions = BI_AGENT_CONFIG.instructions
        self.assertIn("BI Agent", instructions)
        self.assertIn("BidHom", instructions)
        self.assertIn("metrics", instructions.lower())
        self.assertIn("get_metrics_property_summary", instructions)
        self.assertIn("underperforming", instructions.lower())


class BIAgentRegistryTests(TestCase):
    """Test BI Agent is properly registered"""

    def test_bi_agent_in_registry(self):
        """Verify BI Agent is registered in agents.yaml"""
        from agents.registry import load_agents_registry

        registry = load_agents_registry()
        self.assertIn("bi", registry, "BI Agent should be in registry")

    def test_bi_agent_registry_config(self):
        """Verify BI Agent registry entry is correct"""
        from agents.registry import load_agents_registry

        registry = load_agents_registry()
        bi_config = registry.get("bi")

        self.assertIsNotNone(bi_config)
        self.assertEqual(bi_config["name"], "BI Agent")
        self.assertEqual(bi_config["display_name"], "BI")
        self.assertEqual(bi_config["config_module"], "agents.bi.agent")
        self.assertEqual(bi_config["config_name"], "BI_AGENT_CONFIG")

    def test_bi_agent_loadable(self):
        """Verify BI Agent can be loaded from registry"""
        from agents.registry import get_agent_config

        config = get_agent_config("bi")
        self.assertIsNotNone(config)
        self.assertEqual(config.name, "BI Agent")
        self.assertEqual(config.icon, "📊")
