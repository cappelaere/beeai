"""
Base Agent Configuration and Model Definitions
"""

import asyncio
from dataclasses import dataclass
from typing import Any

from beeai_framework.agents.requirement import RequirementAgent
from beeai_framework.backend import ChatModel, UserMessage


@dataclass
class AgentConfig:
    """Base configuration for an agent"""

    name: str
    description: str
    instructions: str
    tools: list[Any]
    icon: str  # Emoji or icon identifier


# Available models (2026 - Latest)
AVAILABLE_MODELS = {
    "gpt-4o": {
        "id": "openai:gpt-4o",
        "name": "GPT-4o",
        "description": "OpenAI's most capable multimodal model with strong coding ability (128K context)",
    },
    "gpt-5": {
        "id": "openai:gpt-5",
        "name": "GPT-5",
        "description": "OpenAI's latest and most advanced model with enhanced reasoning (128K context)",
    },
    "gpt-5-nano": {
        "id": "openai:gpt-5-nano",
        "name": "GPT-5 Nano",
        "description": "OpenAI's fastest and most efficient GPT-5 model for quick tasks (128K context)",
    },
    "llama3": {
        "id": "ollama:llama3:latest",
        "name": "Llama 3 (Local)",
        "description": "Meta's Llama 3 running locally via Ollama (fast, private, no API costs)",
    },
    "claude-opus-4": {
        "id": "anthropic:claude-opus-4-6",
        "name": "Claude Opus 4.6",
        "description": "Most intelligent model for building agents and coding (200K context, 128K output)",
    },
    "claude-sonnet-4": {
        "id": "anthropic:claude-sonnet-4-5",
        "name": "Claude Sonnet 4.5",
        "description": "Best balance of speed and intelligence for everyday tasks (200K context, 64K output)",
    },
    "claude-haiku-4": {
        "id": "anthropic:claude-haiku-4-5",
        "name": "Claude Haiku 4.5",
        "description": "Fastest model with near-frontier intelligence (200K context, 64K output)",
    },
    # Legacy model mappings for backwards compatibility
    "claude-3-5-sonnet": {
        "id": "anthropic:claude-sonnet-4-5",
        "name": "Claude Sonnet 4.6",
        "description": "Latest Sonnet (legacy alias)",
    },
    "claude-3-5-opus": {
        "id": "anthropic:claude-opus-4-6",
        "name": "Claude Opus 4.6",
        "description": "Latest Opus (legacy alias)",
    },
    "claude-3-haiku": {
        "id": "anthropic:claude-haiku-4-5",
        "name": "Claude Haiku 4.5",
        "description": "Latest Haiku (legacy alias - Haiku 3 deprecated April 2026)",
    },
}

# Default model key
DEFAULT_MODEL = "gpt-4o"


# Helper functions to generate model-related data from AVAILABLE_MODELS
def get_django_model_choices():
    """Generate Django model field choices from AVAILABLE_MODELS.
    Returns list of tuples (key, display_name) for current models only."""
    current_models = [
        "gpt-4o",
        "gpt-5",
        "gpt-5-nano",
        "llama3",
        "claude-opus-4",
        "claude-sonnet-4",
        "claude-haiku-4",
    ]
    return [(key, AVAILABLE_MODELS[key]["name"]) for key in current_models]


def get_all_model_keys():
    """Get all model keys including legacy aliases for CLI/validation."""
    return list(AVAILABLE_MODELS.keys())


def get_model_id_from_short_key(short_key: str) -> str:
    """Convert short model key to full API model ID.
    Args:
        short_key: Short key like 'claude-haiku-4' or 'claude-3-5-sonnet'
    Returns:
        Full API ID like 'anthropic:claude-haiku-4-5'
    """
    model_info = AVAILABLE_MODELS.get(short_key)
    if model_info:
        return model_info["id"]
    # Fallback to default if not found
    return AVAILABLE_MODELS[DEFAULT_MODEL]["id"]


def get_model_display_name(model_id: str) -> str:
    """Get display name from full API model ID.
    Args:
        model_id: Full API ID like 'anthropic:claude-haiku-4-5'
    Returns:
        Display name like 'Claude Haiku 4.5'
    """
    # Search for matching model by ID
    for model_info in AVAILABLE_MODELS.values():
        if model_info["id"] == model_id:
            return model_info["name"]
    # Fallback: format the model_id nicely
    return model_id.replace("anthropic:", "").replace("-", " ").title()


def get_model_options_for_template():
    """Generate model options for HTML template.
    Returns list of dicts with 'key', 'name', and 'default' fields."""
    current_models = [
        "gpt-4o",
        "gpt-5",
        "gpt-5-nano",
        "llama3",
        "claude-opus-4",
        "claude-sonnet-4",
        "claude-haiku-4",
    ]
    return [
        {"key": key, "name": AVAILABLE_MODELS[key]["name"], "default": (key == DEFAULT_MODEL)}
        for key in current_models
    ]


def get_workflow_studio_model_options():
    """Model options for Workflow Studio (recommend capable models for code/BPMN generation)."""
    studio_models = [
        "claude-sonnet-4",
        "claude-opus-4",
        "gpt-4o",
        "gpt-5",
        "claude-haiku-4",
    ]
    return [
        {"key": key, "name": AVAILABLE_MODELS[key]["name"], "default": (key == "claude-sonnet-4")}
        for key in studio_models
    ]


def run_generation_prompt_sync(
    prompt: str,
    model_short_key: str,
    max_tokens: int = 8000,
) -> str:
    """Run a single user prompt with the chosen LLM and return the assistant text (sync for Django).
    Uses BeeAI ChatModel and the app's model registry."""
    model_id = get_model_id_from_short_key(model_short_key)
    llm = ChatModel.from_name(model_id)

    async def _run():
        result = await llm.run([UserMessage(prompt)], max_tokens=max_tokens)
        return result.get_text_content() or ""

    return asyncio.run(_run())


def load_skills_documentation(agent_id: str) -> str:
    """
    Load SKILLS.md documentation for an agent if it exists.

    Args:
        agent_id: Agent identifier (e.g., "gres", "sam")

    Returns:
        str: SKILLS.md content, or empty string if file doesn't exist
    """
    from agents.registry import get_agent_skills_path

    skills_path = get_agent_skills_path(agent_id)
    if not skills_path or not skills_path.exists():
        return ""

    try:
        with open(skills_path, encoding="utf-8") as f:
            content = f.read()
        return content.strip()
    except Exception as e:
        print(f"Warning: Failed to load SKILLS.md for {agent_id}: {e}")
        return ""


def create_agent(
    config: AgentConfig, model_id: str, agent_id: str = None, load_skills: bool = True
) -> RequirementAgent:
    """
    Create agent instance with specified model.

    Args:
        config: Agent configuration
        model_id: Model identifier
        agent_id: Optional agent ID for loading SKILLS.md
        load_skills: If True, automatically load SKILLS.md into instructions

    Returns:
        RequirementAgent instance
    """
    instructions = config.instructions

    # Load and prepend SKILLS.md if available
    if load_skills and agent_id:
        skills_content = load_skills_documentation(agent_id)
        if skills_content:
            instructions = f"{skills_content}\n\n---\n\n{instructions}"

    llm = ChatModel.from_name(model_id)
    return RequirementAgent(llm=llm, tools=config.tools, instructions=instructions)
