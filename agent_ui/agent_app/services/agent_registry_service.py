"""
Agent registry service: business logic for agent admin operations.
Uses atomic registry writes and raises domain exceptions for views to map to HTTP.
"""

import logging
import re
import shutil
from pathlib import Path

import yaml

from agent_app.exceptions import AgentNotFoundError, ConflictError, ValidationError

logger = logging.getLogger(__name__)


def _repo_root() -> Path:
    from agents.registry import get_registry_path

    return get_registry_path().parent.parent


def _load_full_registry() -> tuple[dict, Path]:
    from agents.registry import get_registry_path, load_agents_registry

    load_agents_registry.cache_clear()
    path = get_registry_path()
    if not path.exists():
        raise FileNotFoundError(f"Agent registry not found: {path}")
    with path.open() as f:
        data = yaml.safe_load(f)
    if not data:
        data = {"agents": {}}
    if "agents" not in data:
        data["agents"] = {}
    return data, path


def _save_registry(data: dict, path: Path) -> None:
    from agents.registry import load_agents_registry, write_registry_yaml

    write_registry_yaml(data, path)
    load_agents_registry.cache_clear()


def set_default_agent(agent_id: str) -> None:
    """Set the default agent. Raises AgentNotFoundError if agent_id not in registry."""
    data, path = _load_full_registry()
    registry = data.get("agents", {})
    if agent_id not in registry:
        raise AgentNotFoundError(agent_id)
    for aid in registry:
        registry[aid]["default"] = aid == agent_id
    _save_registry(data, path)


def update_agent_metadata(agent_id: str, name: str, description: str) -> None:
    """Update agent name and description. Raises AgentNotFoundError if not found."""
    if not name or not description:
        raise ValidationError("Name and description required")
    data, path = _load_full_registry()
    registry = data.get("agents", {})
    if agent_id not in registry:
        raise AgentNotFoundError(agent_id)
    registry[agent_id]["name"] = name
    registry[agent_id]["display_name"] = name
    registry[agent_id]["description"] = description
    _save_registry(data, path)


def create_agent(
    agent_id: str,
    name: str,
    description: str,
    icon: str,
    prompt: str,
    *,
    skills_content: str | None = None,
) -> None:
    """
    Create agent directory, SKILLS.md, config, and add to registry.
    Raises ValidationError for invalid input or if agent already exists.
    """
    if not all([name, agent_id, icon, description, prompt]):
        raise ValidationError("All fields are required")
    if not re.match(r"^[a-z][a-z0-9_]*$", agent_id):
        raise ValidationError("Invalid agent ID format")

    from agents.registry import load_agents_registry

    load_agents_registry.cache_clear()
    registry = load_agents_registry()
    if agent_id in registry:
        raise ValidationError(f'Agent "{agent_id}" already exists')

    repo_root = _repo_root()
    agent_dir = repo_root / "agents" / agent_id
    if agent_dir.exists():
        raise ValidationError("Agent directory already exists")

    agent_dir.mkdir(parents=True, exist_ok=True)
    (agent_dir / "__init__.py").write_text(f'"""Agent: {name}"""\n')

    if skills_content is None:
        skills_content = f"""# {name}

{description}

## Overview

This agent provides specialized capabilities for {description.lower()}.

## Core Capabilities

- Custom agent functionality
- Specialized task handling

## Usage

This agent can be accessed through the agent interface.
"""
    (agent_dir / "SKILLS.md").write_text(skills_content)

    config_content = f'''"""Configuration for {name} agent"""

from agents.base import AgentConfig

config = AgentConfig(
    name="{name}",
    description="{description}",
    system_prompt="""You are {name}, {description}""",
)
'''
    (agent_dir / "config.py").write_text(config_content)

    data, path = _load_full_registry()
    data["agents"][agent_id] = {
        "name": name,
        "display_name": name,
        "icon": icon,
        "description": description,
        "config_module": f"agents.{agent_id}.config",
        "config_name": "config",
        "default": False,
    }
    _save_registry(data, path)


def remove_agent(agent_id: str) -> None:
    """Remove agent from registry and delete its folder. Raises AgentNotFoundError or ConflictError."""
    data, path = _load_full_registry()
    registry = data.get("agents", {})
    if agent_id not in registry:
        raise AgentNotFoundError(agent_id)
    if registry[agent_id].get("default", False):
        raise ConflictError("Cannot remove default agent")

    repo_root = _repo_root()
    agent_dir = repo_root / "agents" / agent_id
    if agent_dir.exists() and agent_dir.is_dir():
        try:
            shutil.rmtree(agent_dir)
            logger.info("Deleted agent directory: %s", agent_dir)
        except OSError as e:
            logger.warning("Failed to delete agent directory %s: %s", agent_dir, e)

    del registry[agent_id]
    _save_registry(data, path)
