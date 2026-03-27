"""
YAML/metadata schema validation for agents.yaml, workflow metadata.yaml, and BPMN bindings.
Uses simple dict checks (no jsonschema dependency). Returns list of error strings.
"""

from pathlib import Path
from typing import Any


def validate_agents_registry(data: dict[str, Any]) -> list[str]:
    """
    Validate agents.yaml structure. Required: top-level 'agents' dict;
    each agent must have id (key), name, description.
    """
    errors: list[str] = []
    if not isinstance(data, dict):
        errors.append("agents.yaml: root must be a YAML object")
        return errors
    agents = data.get("agents")
    if agents is None:
        errors.append("agents.yaml: missing top-level 'agents' key")
        return errors
    if not isinstance(agents, dict):
        errors.append("agents.yaml: 'agents' must be an object (agent_id -> config)")
        return errors
    for agent_id, config in agents.items():
        if not isinstance(config, dict):
            errors.append(f"agents.yaml: agent '{agent_id}' must be an object")
            continue
        if not config.get("name"):
            errors.append(f"agents.yaml: agent '{agent_id}' missing required 'name'")
        if not config.get("description") and "description" not in config:
            errors.append(f"agents.yaml: agent '{agent_id}' missing required 'description'")
    return errors


def validate_workflow_metadata(data: dict[str, Any], path_hint: str = "") -> list[str]:
    """
    Validate workflow metadata.yaml. Required: id, name, description.
    Optional: workflow_number, input_schema, outputs, icon, category, estimated_duration.
    """
    errors: list[str] = []
    prefix = f"metadata.yaml ({path_hint})" if path_hint else "metadata.yaml"
    if not isinstance(data, dict):
        errors.append(f"{prefix}: root must be a YAML object")
        return errors
    for key in ("id", "name", "description"):
        if key not in data:
            errors.append(f"{prefix}: missing required field '{key}'")
    if "input_schema" in data and not isinstance(data["input_schema"], dict):
        errors.append(f"{prefix}: 'input_schema' must be an object")
    if "outputs" in data and not isinstance(data["outputs"], list):
        errors.append(f"{prefix}: 'outputs' must be a list")
    return errors


def validate_bpmn_bindings(data: dict[str, Any], path_hint: str = "") -> list[str]:
    """
    Validate BPMN bindings YAML. Expected: optional workflow_id, executor,
    serviceTasks (dict), userTasks (dict).
    """
    errors: list[str] = []
    prefix = f"bpmn-bindings.yaml ({path_hint})" if path_hint else "bpmn-bindings.yaml"
    if not isinstance(data, dict):
        errors.append(f"{prefix}: root must be a YAML object")
        return errors
    if "serviceTasks" in data and not isinstance(data["serviceTasks"], dict):
        errors.append(f"{prefix}: 'serviceTasks' must be an object")
    if "userTasks" in data and not isinstance(data["userTasks"], dict):
        errors.append(f"{prefix}: 'userTasks' must be an object")
    return errors


def validate_all_metadata(repo_root: Path | None = None) -> tuple[list[str], list[str]]:
    """
    Run schema validation for agents.yaml and all workflow metadata.yaml files.
    Returns (errors, warnings). Errors are critical; warnings are non-fatal (e.g. optional file missing).
    """
    if repo_root is None:
        # Keep workflow metadata validation aligned with the workflow registry's
        # repo-root resolution instead of deriving it from agents.yaml, which can
        # overshoot by one parent directory.
        from agent_app.workflow_registry import REPO_ROOT as WORKFLOW_REPO_ROOT

        repo_root = WORKFLOW_REPO_ROOT

    from agents.registry import get_registry_path

    errors: list[str] = []
    warnings: list[str] = []

    # Agents registry
    agents_path = get_registry_path()
    if not agents_path.exists():
        errors.append(f"Agent registry not found: {agents_path}")
    else:
        try:
            import yaml

            with agents_path.open() as f:
                data = yaml.safe_load(f)
            errs = validate_agents_registry(data or {})
            errors.extend(errs)
        except Exception as e:
            errors.append(f"agents.yaml: failed to load or validate: {e}")

    # Workflow metadata files (only root metadata.yaml per workflow, not .versions)
    workflows_dir = repo_root / "workflows"
    if not workflows_dir.is_dir():
        errors.append(f"Workflows directory not found: {workflows_dir}")
    else:
        from agent_app.workflow_registry import _should_skip_workflow_path

        for wf_path in workflows_dir.iterdir():
            if _should_skip_workflow_path(wf_path):
                continue
            meta_file = wf_path / "metadata.yaml"
            if not meta_file.exists():
                warnings.append(f"Workflow '{wf_path.name}': no metadata.yaml")
                continue
            try:
                import yaml

                with meta_file.open() as f:
                    data = yaml.safe_load(f)
                errs = validate_workflow_metadata(data or {}, wf_path.name)
                errors.extend(errs)
            except Exception as e:
                errors.append(f"Workflow '{wf_path.name}' metadata.yaml: {e}")

    return (errors, warnings)
