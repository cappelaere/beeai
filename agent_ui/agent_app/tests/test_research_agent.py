"""
Tests for Research Agent and DuckDuckGo Search Tool
"""

import sys
from pathlib import Path

from django.test import TestCase

# Add agents directory to path
_AGENTS_DIR = Path(__file__).parent.parent.parent.parent / "agents"
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))


class DuckDuckGoToolTests(TestCase):
    """Test DuckDuckGo search tool availability and basic functionality"""

    def test_duckduckgo_tool_import(self):
        """Verify DuckDuckGo tool can be imported"""
        from beeai_framework.tools.search.duckduckgo import DuckDuckGoSearchTool

        self.assertIsNotNone(DuckDuckGoSearchTool)

    def test_duckduckgo_tool_instantiation(self):
        """Verify DuckDuckGo tool can be instantiated with configuration"""
        from beeai_framework.tools.search.duckduckgo import DuckDuckGoSearchTool

        tool = DuckDuckGoSearchTool(max_results=10, safe_search="STRICT")

        self.assertIsNotNone(tool)
        self.assertEqual(tool.name, "DuckDuckGo")
        self.assertIn("search", tool.description.lower())
        self.assertEqual(tool.max_results, 10)
        self.assertEqual(tool.safe_search, "STRICT")

    def test_duckduckgo_tool_config_options(self):
        """Test different configuration options"""
        from beeai_framework.tools.search.duckduckgo import DuckDuckGoSearchTool

        # Test with different max_results
        tool1 = DuckDuckGoSearchTool(max_results=5)
        self.assertEqual(tool1.max_results, 5)

        # Test with different safe_search
        tool2 = DuckDuckGoSearchTool(safe_search="MODERATE")
        self.assertEqual(tool2.safe_search, "MODERATE")

    def test_duckduckgo_input_schema(self):
        """Verify input schema has query field"""
        from beeai_framework.tools.search.duckduckgo import DuckDuckGoSearchToolInput

        # Check that input schema has query field
        schema = DuckDuckGoSearchToolInput.model_json_schema()
        self.assertIn("properties", schema)
        self.assertIn("query", schema["properties"])
        self.assertEqual(schema["properties"]["query"]["type"], "string")


class ResearchAgentTests(TestCase):
    """Test Research Agent configuration and integration"""

    def test_research_agent_import(self):
        """Verify Research Agent can be imported"""
        from agents.research.agent import RESEARCH_AGENT_CONFIG

        self.assertIsNotNone(RESEARCH_AGENT_CONFIG)

    def test_research_agent_config(self):
        """Verify Research Agent configuration"""
        from agents.research.agent import RESEARCH_AGENT_CONFIG

        self.assertEqual(RESEARCH_AGENT_CONFIG.name, "Research Agent")
        self.assertEqual(RESEARCH_AGENT_CONFIG.icon, "🔍")
        self.assertIn("web search", RESEARCH_AGENT_CONFIG.description.lower())
        self.assertIsNotNone(RESEARCH_AGENT_CONFIG.tools)
        self.assertGreater(len(RESEARCH_AGENT_CONFIG.tools), 0)

    def test_research_agent_has_duckduckgo_tool(self):
        """Verify Research Agent includes DuckDuckGo tool"""
        from beeai_framework.tools.search.duckduckgo import DuckDuckGoSearchTool

        from agents.research.agent import RESEARCH_AGENT_CONFIG

        # Check that DuckDuckGo tool is in the tools list
        has_duckduckgo = any(
            isinstance(tool, DuckDuckGoSearchTool) for tool in RESEARCH_AGENT_CONFIG.tools
        )
        self.assertTrue(has_duckduckgo, "Research Agent should include DuckDuckGoSearchTool")

    def test_research_agent_has_think_tool(self):
        """Verify Research Agent includes Think tool"""
        from beeai_framework.tools.think import ThinkTool

        from agents.research.agent import RESEARCH_AGENT_CONFIG

        # Check that Think tool is in the tools list
        has_think = any(isinstance(tool, ThinkTool) for tool in RESEARCH_AGENT_CONFIG.tools)
        self.assertTrue(has_think, "Research Agent should include ThinkTool")

    def test_research_agent_instructions(self):
        """Verify Research Agent has proper instructions"""
        from agents.research.agent import RESEARCH_AGENT_CONFIG

        instructions = RESEARCH_AGENT_CONFIG.instructions
        self.assertIn("Research Agent", instructions)
        self.assertIn("search", instructions.lower())
        self.assertIn("DuckDuckGo", instructions)


class FloAgentDuckDuckGoTests(TestCase):
    """Test Flo Agent integration with DuckDuckGo tool"""

    def test_flo_agent_has_duckduckgo_tool(self):
        """Verify Flo Agent includes DuckDuckGo tool"""
        from beeai_framework.tools.search.duckduckgo import DuckDuckGoSearchTool

        from agents.flo.agent import FLO_AGENT_CONFIG

        # Check that DuckDuckGo tool is in the tools list
        has_duckduckgo = any(
            isinstance(tool, DuckDuckGoSearchTool) for tool in FLO_AGENT_CONFIG.tools
        )
        self.assertTrue(has_duckduckgo, "Flo Agent should include DuckDuckGoSearchTool")

    def test_flo_agent_duckduckgo_config(self):
        """Verify Flo Agent's DuckDuckGo tool is configured for fewer results"""
        from beeai_framework.tools.search.duckduckgo import DuckDuckGoSearchTool

        from agents.flo.agent import FLO_AGENT_CONFIG

        # Find the DuckDuckGo tool
        ddg_tool = None
        for tool in FLO_AGENT_CONFIG.tools:
            if isinstance(tool, DuckDuckGoSearchTool):
                ddg_tool = tool
                break

        self.assertIsNotNone(ddg_tool, "DuckDuckGo tool should be present in Flo Agent")
        self.assertEqual(ddg_tool.max_results, 5, "Flo Agent should use 5 max results")
        self.assertEqual(ddg_tool.safe_search, "STRICT", "Flo Agent should use STRICT safe search")


class AgentRegistryTests(TestCase):
    """Test Research Agent is properly registered"""

    def test_research_agent_in_registry(self):
        """Verify Research Agent is registered in agents.yaml"""
        from agents.registry import load_agents_registry

        registry = load_agents_registry()
        self.assertIn("research", registry, "Research Agent should be in registry")

    def test_research_agent_registry_config(self):
        """Verify Research Agent registry entry is correct"""
        from agents.registry import load_agents_registry

        registry = load_agents_registry()
        research_config = registry.get("research")

        self.assertIsNotNone(research_config)
        self.assertEqual(research_config["name"], "Research Agent")
        self.assertEqual(research_config["display_name"], "Research")
        self.assertEqual(research_config["icon"], "🔍")
        self.assertEqual(research_config["config_module"], "agents.research.agent")
        self.assertEqual(research_config["config_name"], "RESEARCH_AGENT_CONFIG")

    def test_research_agent_loadable(self):
        """Verify Research Agent can be loaded from registry"""
        from agents.registry import get_agent_config

        config = get_agent_config("research")
        self.assertIsNotNone(config)
        self.assertEqual(config.name, "Research Agent")
        self.assertEqual(config.icon, "🔍")
