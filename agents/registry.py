"""
Agent Registry - Single Source of Truth
Loads agent metadata from agents.yaml and provides helper functions
"""

import importlib
import os
import tempfile
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

# Path to agents.yaml (in repo root)
_REPO_ROOT = Path(__file__).parent.parent
_REGISTRY_FILE = _REPO_ROOT / "agents.yaml"


def write_registry_yaml(data: dict[str, Any], registry_path: Path) -> None:
    """
    Write registry data to agents.yaml atomically (temp file + replace).
    Reduces risk of corrupting the registry on partial write or crash.
    """
    registry_path = Path(registry_path)
    dir_path = registry_path.parent
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".tmp",
            prefix=registry_path.name + ".",
            dir=dir_path,
            delete=False,
        ) as fd:
            tmp_path = Path(fd.name)
            yaml.dump(data, fd, default_flow_style=False, sort_keys=False)
            fd.flush()
            if hasattr(os, "fdatasync"):
                os.fdatasync(fd.fileno())
        tmp_path.replace(registry_path)
        tmp_path = None
    finally:
        if tmp_path is not None:
            tmp_path.unlink(missing_ok=True)


def get_registry_path() -> Path:
    """
    Get the path to the agents registry file.

    Returns:
        Path: Absolute path to agents.yaml
    """
    return _REGISTRY_FILE


@lru_cache(maxsize=1)
def load_agents_registry() -> dict[str, dict[str, Any]]:
    """
    Load agents registry from agents.yaml.
    Cached to avoid repeated file reads.

    Returns:
        dict: Dictionary mapping agent_id -> agent metadata
    """
    if not _REGISTRY_FILE.exists():
        raise FileNotFoundError(f"Agent registry not found: {_REGISTRY_FILE}")

    with _REGISTRY_FILE.open() as f:
        data = yaml.safe_load(f)

    if not data or "agents" not in data:
        raise ValueError("Invalid agents.yaml: missing 'agents' key")

    return data["agents"]


def get_all_agent_ids() -> list[str]:
    """
    Get list of all agent IDs.

    Returns:
        list: Agent IDs (e.g., ["gres", "sam", "ofac", ...])
    """
    registry = load_agents_registry()
    return list(registry.keys())


def get_agent_metadata(agent_id: str) -> dict[str, Any]:
    """
    Get metadata for a specific agent.

    Args:
        agent_id: Agent identifier (e.g., "gres", "sam")

    Returns:
        dict: Agent metadata from agents.yaml

    Raises:
        KeyError: If agent_id not found
    """
    registry = load_agents_registry()
    if agent_id not in registry:
        raise KeyError(
            f"Agent '{agent_id}' not found in registry. Available: {list(registry.keys())}"
        )
    return registry[agent_id]


def get_agent_config(agent_id: str):
    """
    Load and return the AgentConfig object for the specified agent.
    Dynamically imports the agent module and retrieves the config.

    Args:
        agent_id: Agent identifier (e.g., "gres", "sam")

    Returns:
        AgentConfig: The agent's configuration object

    Raises:
        KeyError: If agent_id not found in registry
        ImportError: If agent module cannot be imported
        AttributeError: If config_name not found in module
    """
    metadata = get_agent_metadata(agent_id)

    # Import the agent module dynamically
    module_path = metadata["config_module"]
    config_name = metadata["config_name"]

    try:
        module = importlib.import_module(module_path)
        config = getattr(module, config_name)
        return config
    except ImportError as e:
        raise ImportError(f"Failed to import agent module '{module_path}': {e}") from e
    except AttributeError as e:
        raise AttributeError(
            f"Config '{config_name}' not found in module '{module_path}': {e}"
        ) from e


def get_default_agent_id() -> str:
    """
    Get the default agent ID.

    Returns:
        str: Agent ID marked as default in registry (e.g., "gres")
    """
    registry = load_agents_registry()
    for agent_id, metadata in registry.items():
        if metadata.get("default", False):
            return agent_id

    # Fallback to first agent if no default specified
    return list(registry.keys())[0]


def get_django_agent_choices() -> list[tuple[str, str]]:
    """
    Generate Django model field choices from registry.
    Used for agent_type fields in models.

    Returns:
        list: List of tuples (agent_id, display_name)
              e.g., [("gres", "GRES Agent"), ("sam", "SAM.gov Exclusions"), ...]
    """
    registry = load_agents_registry()
    choices = [(agent_id, metadata["name"]) for agent_id, metadata in registry.items()]

    # Add special "all" option used by AssistantCard
    choices.append(("all", "All Agents"))

    return choices


def get_agents_for_template() -> list[dict[str, Any]]:
    """
    Generate agent list for Django templates.
    Used by context processor to provide AVAILABLE_AGENTS in all templates.

    Returns:
        list: List of dicts with keys: id, name, display_name, icon, description, default
              e.g., [
                  {
                      "id": "gres",
                      "name": "GRES Agent",
                      "display_name": "GRES",
                      "icon": "🏢",
                      "description": "GSA Real Estate...",
                      "default": True
                  },
                  ...
              ]
    """
    registry = load_agents_registry()
    agents = []

    for agent_id, metadata in registry.items():
        agents.append(
            {
                "id": agent_id,
                "name": metadata["name"],
                "display_name": metadata["display_name"],
                "icon": metadata["icon"],
                "description": metadata["description"],
                "default": metadata.get("default", False),
            }
        )

    return agents


def get_agent_skills_path(agent_id: str) -> Path | None:
    """
    Get the path to an agent's SKILLS.md file.

    Args:
        agent_id: Agent identifier

    Returns:
        Path: Absolute path to SKILLS.md file, or None if not specified
    """
    metadata = get_agent_metadata(agent_id)
    skills_file = metadata.get("skills_file")

    if not skills_file:
        return None

    # Convert relative path to absolute
    return _REPO_ROOT / skills_file


def _check_required_metadata_fields(agent_id, metadata, results):
    """Check that agent metadata has all required fields."""
    required_fields = [
        "name",
        "display_name",
        "icon",
        "description",
        "config_module",
        "config_name",
    ]
    for field in required_fields:
        if field not in metadata:
            results["errors"].append(f"Agent '{agent_id}': Missing required field '{field}'")
            results["valid"] = False


def _check_agent_folder(agent_id, results):
    """Check that agent folder exists and is a directory."""
    agent_folder = _REPO_ROOT / "agents" / agent_id
    if not agent_folder.exists():
        results["errors"].append(f"Agent '{agent_id}': Folder not found at {agent_folder}")
        results["valid"] = False
        return False

    if not agent_folder.is_dir():
        results["errors"].append(
            f"Agent '{agent_id}': Path exists but is not a directory: {agent_folder}"
        )
        results["valid"] = False
        return False

    return True


def _check_agent_files(agent_id, results):
    """Check that required agent files exist."""
    agent_folder = _REPO_ROOT / "agents" / agent_id
    init_file = agent_folder / "__init__.py"
    agent_file = agent_folder / "agent.py"

    if not init_file.exists():
        results["warnings"].append(
            f"Agent '{agent_id}': Missing __init__.py (optional but recommended)"
        )

    if not agent_file.exists():
        results["errors"].append(f"Agent '{agent_id}': Missing agent.py configuration file")
        results["valid"] = False


def _check_agent_skills(agent_id, results):
    """Check that agent skills file exists if specified."""
    skills_path = get_agent_skills_path(agent_id)
    if skills_path and not skills_path.exists():
        results["warnings"].append(f"Agent '{agent_id}': Skills file not found: {skills_path}")


def _validate_agent_config(agent_id, results):
    """Try to import and validate agent config."""
    try:
        config = get_agent_config(agent_id)
        if not hasattr(config, "name"):
            results["errors"].append(f"Agent '{agent_id}': Config missing 'name' attribute")
            results["valid"] = False
    except ImportError as e:
        results["errors"].append(f"Agent '{agent_id}': Failed to import config module: {e}")
        results["valid"] = False
    except AttributeError as e:
        results["errors"].append(f"Agent '{agent_id}': Config attribute not found: {e}")
        results["valid"] = False
    except Exception as e:
        results["errors"].append(f"Agent '{agent_id}': Unexpected error loading config: {e}")
        results["valid"] = False


def _remove_orphaned_agents(agents_to_remove, results):
    """Remove orphaned agent entries from registry file."""
    import logging

    import yaml

    logger = logging.getLogger(__name__)

    with _REGISTRY_FILE.open() as f:
        data = yaml.safe_load(f)

    for agent_id in agents_to_remove:
        if agent_id in data.get("agents", {}):
            del data["agents"][agent_id]
            results["fixed"] += 1
            logger.warning(f"Removed orphaned agent entry: {agent_id}")

    with _REGISTRY_FILE.open("w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    load_agents_registry.cache_clear()

    results["warnings"].append(f"Automatically removed {results['fixed']} orphaned agent entries")


def validate_registry_integrity(fix_issues: bool = False) -> dict[str, Any]:
    """
    Validate agents.yaml integrity and agent folder structure.
    Checks that all agents in registry have corresponding folders and files.

    Args:
        fix_issues: If True, attempts to fix issues (remove orphaned entries)

    Returns:
        dict: Validation results with errors, warnings, and summary
    """
    results = {"valid": True, "errors": [], "warnings": [], "checked": 0, "fixed": 0}

    try:
        registry = load_agents_registry()
        results["checked"] = len(registry)
        agents_to_remove = []

        for agent_id, metadata in registry.items():
            _check_required_metadata_fields(agent_id, metadata, results)

            folder_valid = _check_agent_folder(agent_id, results)
            if not folder_valid:
                agents_to_remove.append(agent_id)
                continue

            _check_agent_files(agent_id, results)
            _check_agent_skills(agent_id, results)
            _validate_agent_config(agent_id, results)

        if fix_issues and agents_to_remove:
            _remove_orphaned_agents(agents_to_remove, results)

    except Exception as e:
        results["valid"] = False
        results["errors"].append(f"Registry validation failed: {e}")

    return results


def validate_registry():
    """
    Validate that all agents in registry can be loaded.
    Useful for testing and debugging.

    Raises:
        Exception: If any agent fails validation
    """
    results = validate_registry_integrity(fix_issues=False)

    if not results["valid"]:
        error_msg = "Registry validation failed:\n" + "\n".join(
            f"  - {e}" for e in results["errors"]
        )
        raise ValueError(error_msg)

    return True


# Convenience function for getting display name
def get_agent_display_name(agent_id: str, fallback: str = "RealtyIQ Agent") -> str:
    """
    Get display name for an agent, with fallback.

    Args:
        agent_id: Agent identifier
        fallback: Fallback name if agent not found

    Returns:
        str: Agent's display name
    """
    try:
        metadata = get_agent_metadata(agent_id)
        return metadata["name"]
    except KeyError:
        return fallback
