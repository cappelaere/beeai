"""
Multi-Agent System for BeeAI Platform

Available Agents:
- GRES Agent (default) - GSA Real Estate Sales auctions
- SAM.gov Agent - Federal contract exclusions
- IDV Agent (future) - Identity verification
"""

from .base import AVAILABLE_MODELS, AgentConfig, create_agent

__all__ = ["AgentConfig", "AVAILABLE_MODELS", "create_agent"]
