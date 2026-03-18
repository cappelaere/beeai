"""
Workflow service: business logic for workflow creation, save, and versioning.
Views in api_workflows delegate here and map domain exceptions to HTTP.
"""

import json
import logging
import re
from pathlib import Path
from typing import Any

import yaml

from agent_app.exceptions import ValidationError, WorkflowExistsError, WorkflowNotFoundError
from agent_app.workflow_context import (
    get_first_task_id,
    normalize_bindings,
    parse_bpmn_xml,
    parse_workflow_python,
    validate_bpmn_bindings_context,
)

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def _bindings_dict_from_yaml(text: str) -> dict[str, Any]:
    if not text or not str(text).strip():
        return {}
    loaded = yaml.safe_load(text) or {}
    return loaded if isinstance(loaded, dict) else {}


USER_STORY_TEMPLATE = """You must follow this exact structure. Start with Business Value; keep sections in this order.

# User Story: {title}

## Business Value

### Primary Benefits

- List 3–5 concrete benefits (who gets what value, one line each).
- Use clear, outcome-focused bullets.

### Success Metrics

- List 2–4 measurable success criteria (e.g. completion time, output completeness, auditability).

---

## As a...

**One or two roles / personas** (e.g. Program Manager, Real Estate Specialist).

## I want to...

One sentence: what the user can do (the capability).

## So that...

One sentence: the outcome or benefit they get.

---

## Acceptance Criteria

- For each workflow step listed below, add one acceptance criterion in Given/When/Then form, or as a short bullet.
- Steps to cover: {steps}
"""


def validate_workflow_input(data: dict) -> tuple:
    """Validate workflow creation input. Returns (name, workflow_id, icon, category, description, prompt, model). Raises ValidationError."""
    name = (data.get("name") or "").strip()
    workflow_id = (data.get("workflow_id") or "").strip()
    icon = (data.get("icon") or "").strip()
    category = (data.get("category") or "").strip()
    description = (data.get("description") or "").strip()
    prompt = (data.get("prompt") or "").strip()
    model = (data.get("model") or "").strip() or "claude-sonnet-4"
    if not all([name, workflow_id, icon, category, description, prompt]):
        raise ValidationError("All fields are required")
    if not re.match(r"^[a-z][a-z0-9_]*$", workflow_id):
        raise ValidationError("Invalid workflow ID format")
    return (name, workflow_id, icon, category, description, prompt, model)


def _create_workflow_directory(workflow_id: str) -> Path:
    """Create workflow directory structure. Raises WorkflowExistsError if dir exists."""
    workflow_dir = REPO_ROOT / "workflows" / workflow_id
    if workflow_dir.exists():
        raise WorkflowExistsError("Workflow directory already exists")
    workflow_dir.mkdir(parents=True, exist_ok=True)
    (workflow_dir / "__init__.py").write_text(f'"""Workflow: {workflow_id}"""\n')
    return workflow_dir


def _load_context_files(repo_root: Path) -> tuple[str, str]:
    context_path = repo_root / "context" / "CONTEXT.md"
    workflow_guidelines_path = repo_root / "context" / "WORKFLOW_GUIDELINES.md"
    context_content = context_path.read_text()[:3000] if context_path.exists() else ""
    workflow_guidelines = (
        workflow_guidelines_path.read_text()[:3000] if workflow_guidelines_path.exists() else ""
    )
    return context_content, workflow_guidelines


def _get_fallback_workflow_code(workflow_id: str, name: str, description: str, prompt: str) -> str:
    return f'''"""
{name}
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class {workflow_id.title().replace("_", "")}Workflow:
    """
    {description}
    """

    def __init__(self):
        self.name = "{workflow_id}"
        self.description = "{description}"

    async def execute(self, context: dict) -> dict:
        logger.info(f"Starting workflow {{self.name}}")
        return {{'status': 'success', 'message': 'Workflow completed', 'data': {{}}}}
'''


def _generate_workflow_code(
    model_short_key: str,
    name: str,
    workflow_id: str,
    category: str,
    description: str,
    prompt: str,
    context_content: str,
    workflow_guidelines: str,
) -> str:
    from agents.base import run_generation_prompt_sync

    workflow_generation_prompt = f"""Generate a complete BeeAI Framework workflow implementation for RealtyIQ with the following specifications:

Workflow Name: {name}
Workflow ID: {workflow_id}
Category: {category}
Description: {description}

User Requirements:
{prompt}

CONTEXT:
{context_content}

WORKFLOW GUIDELINES:
{workflow_guidelines}

Generate a complete workflow.py file that includes:
1. Proper imports (BeeAI Framework, logging, pathlib, etc.)
2. Workflow class inheriting from appropriate base
3. Execute method with proper async/await
4. Step functions for each workflow step (method names must be valid Python identifiers matching the BPMN serviceTask ids you will use: use snake_case, e.g. get_active_properties, validate_input)
5. Error handling and validation
6. Human task creation when needed
7. State management
8. Comprehensive logging
9. Proper return values (status, message, data)

The code should follow RealtyIQ patterns. Format as valid Python code with proper docstrings. Output only the Python code, optionally wrapped in ```python ... ```."""

    try:
        workflow_code = run_generation_prompt_sync(
            workflow_generation_prompt, model_short_key, max_tokens=8000
        )
        if "```python" in workflow_code:
            workflow_code = workflow_code.split("```python", 1)[1]
        if "```" in workflow_code:
            workflow_code = workflow_code.rsplit("```", 1)[0]
        return workflow_code.strip()
    except Exception as e:
        logger.exception("Failed to generate workflow.py: %s", e)
        return _get_fallback_workflow_code(workflow_id, name, description, prompt)


def _get_fallback_readme(
    name: str, category: str, description: str, workflow_id: str, prompt: str
) -> str:
    return f"""# {name}

## Overview

{description}

## Category

{category}

## Usage

Execute this workflow using the Flo agent: run workflow {workflow_id} for [parameters].
"""


def _generate_readme(
    model_short_key: str, name: str, workflow_id: str, category: str, description: str, prompt: str
) -> str:
    from agents.base import run_generation_prompt_sync

    readme_prompt = f"""Generate a comprehensive README.md for this RealtyIQ workflow:

Workflow Name: {name}
Workflow ID: {workflow_id}
Category: {category}
Description: {description}

Requirements:
{prompt}

Create a README.md that includes overview, how to execute, required parameters, steps, expected outputs, example usage, troubleshooting. Format as professional markdown."""

    try:
        return run_generation_prompt_sync(readme_prompt, model_short_key, max_tokens=3000)
    except Exception as e:
        logger.exception("Failed to generate README.md: %s", e)
        return _get_fallback_readme(name, category, description, workflow_id, prompt)


def _get_fallback_user_story(name: str, description: str, prompt: str) -> str:
    return f"""# User Story: {name}

## Business Value

### Primary Benefits
- Delivers the capability described below in a single workflow run.

### Success Metrics
- Workflow completes successfully for valid inputs.

---

## As a... **User of this workflow**

## I want to... {description}

## So that... I can achieve the intended outcome.

---

## Acceptance Criteria
- [ ] Workflow accepts required inputs and runs to completion.
"""


def _generate_user_story(
    model_short_key: str,
    name: str,
    workflow_id: str,
    category: str,
    description: str,
    prompt: str,
    service_task_ids: list[str],
) -> str:
    from agents.base import run_generation_prompt_sync

    steps_str = ", ".join(service_task_ids) if service_task_ids else "workflow steps"
    instructions = USER_STORY_TEMPLATE.format(title=name, steps=steps_str)
    user_story_prompt = f"""Generate a first-cut user story for this workflow. {instructions}

Workflow Name: {name}
Workflow ID: {workflow_id}
Category: {category}
Description: {description}

User requirements:
{prompt}

Output only the USER_STORY.md content in markdown. Start with the heading "# User Story:"."""

    try:
        content = run_generation_prompt_sync(user_story_prompt, model_short_key, max_tokens=2500)
        content = content.strip()
        if not content.startswith("# User Story:"):
            content = f"# User Story: {name}\n\n{content}"
        return content
    except Exception as e:
        logger.exception("Failed to generate USER_STORY.md via LLM: %s", e)
        return _get_fallback_user_story(name, description, prompt)


def _generate_bpmn(
    model_short_key: str, name: str, workflow_id: str, description: str, prompt: str
) -> tuple[str, list[str]]:
    from tools.bpmn_tools import create_new_bpmn_impl

    return create_new_bpmn_impl(
        workflow_id,
        name,
        description,
        prompt,
        model_short_key=model_short_key,
    )


def _derive_input_schema_from_workflow(workflow_code: str) -> str:
    """
    Derive a minimal input_schema YAML block from the workflow's state class, or return
    a generic request_data schema. Used so metadata.yaml has a valid, editable schema.
    """
    code_info = parse_workflow_python(workflow_code)
    field_names = code_info.get("state_field_names") or []
    descriptions = code_info.get("state_field_descriptions") or {}
    if not field_names:
        return """  request_data:
    type: string
    description: Workflow input data (define specific fields in state class and update this schema)
"""
    lines = []
    for name in field_names:
        desc = descriptions.get(name) or name.replace("_", " ").title()
        lines.append(f"  {name}:")
        lines.append(f"    type: string")
        lines.append(f"    description: {desc!r}")
    return "\n".join(lines)


def _get_handler_descriptions(workflow_code: str, service_task_ids: list[str]) -> dict[str, str]:
    """Map each service task id to a short description (docstring first line or human-readable id)."""
    code_info = parse_workflow_python(workflow_code)
    method_docstrings = {
        m["name"]: (m.get("docstring") or "").strip().split("\n")[0].strip()
        for m in (code_info.get("methods") or [])
    }
    result = {}
    for task_id in service_task_ids:
        doc = method_docstrings.get(task_id)
        if doc and doc.rstrip("."):
            result[task_id] = doc.rstrip(".")
        else:
            result[task_id] = task_id.replace("_", " ").title()
    return result


def _validate_generated_bpmn_and_bindings(
    bpmn_xml: str, service_task_ids: list[str], workflow_id: str, workflow_code: str
) -> None:
    """
    Validate that generated BPMN and bindings are consistent before writing files.
    Raises ValueError if first task is missing or not bound, or if context validation fails.
    """
    parsed = parse_bpmn_xml(bpmn_xml)
    if parsed.get("parse_error"):
        raise ValueError(f"Generated BPMN XML is invalid: {parsed['parse_error']}")
    first_task = get_first_task_id(parsed)
    if not first_task:
        raise ValueError(
            "Generated BPMN has no reachable first service task (check start event and sequence flow)"
        )
    task_set = set(service_task_ids)
    if first_task not in task_set:
        raise ValueError(
            f"First BPMN task '{first_task}' is not in generated bindings (service task ids: {list(service_task_ids)})"
        )
    code_info = parse_workflow_python(workflow_code)
    bindings = {
        "workflow_id": workflow_id,
        "serviceTasks": {
            tid: {
                "handler": tid,
                "description": _get_handler_descriptions(workflow_code, service_task_ids).get(
                    tid, ""
                ),
            }
            for tid in service_task_ids
        },
    }
    context = {
        "workflow": {"id": workflow_id},
        "bpmn": parsed,
        "bindings": bindings,
        "code": code_info,
    }
    validation = validate_bpmn_bindings_context(context)
    if not validation.get("valid"):
        errors = validation.get("errors") or []
        raise ValueError(f"Generated BPMN/bindings validation failed: {'; '.join(errors)}")


def get_service_task_ids_for_workflow(workflow_id: str) -> list[str]:
    """Public: read service task IDs from workflow bpmn-bindings (for user story generation)."""
    workflow_dir = REPO_ROOT / "workflows" / workflow_id
    for bindings_path in (
        workflow_dir / "currentVersion" / "bpmn-bindings.yaml",
        workflow_dir / "bpmn-bindings.yaml",
    ):
        if bindings_path.exists():
            try:
                data = yaml.safe_load(bindings_path.read_text()) or {}
                tasks = data.get("serviceTasks") or {}
                return list(tasks.keys())
            except Exception as e:
                logger.warning("Could not parse %s: %s", bindings_path, e)
    return []


def _create_workflow_files(
    workflow_dir: Path,
    workflow_code: str,
    readme_content: str,
    user_story_content: str,
    name: str,
    workflow_id: str,
    icon: str,
    category: str,
    description: str,
    bpmn_xml: str,
    service_task_ids: list[str],
) -> None:
    (workflow_dir / "workflow.py").write_text(workflow_code)
    (workflow_dir / "README.md").write_text(readme_content)
    input_schema_block = _derive_input_schema_from_workflow(workflow_code)
    metadata_content = f"""id: {workflow_id}
name: {name}
description: {description}
icon: {icon}
category: {category}
version: "1.0"
estimated_duration: "To be determined"

input_schema:
{input_schema_block}
output_schema:
  status:
    type: string
    description: Workflow execution status
  message:
    type: string
    description: Human-readable result message
  data:
    type: object
    description: Workflow output data
"""
    (workflow_dir / "metadata.yaml").write_text(metadata_content)
    (workflow_dir / "USER_STORY.md").write_text(user_story_content.strip() + "\n")
    step_descriptions = _get_handler_descriptions(workflow_code, service_task_ids)
    step_bullets = "\n".join(
        f"- **{tid}**: {step_descriptions.get(tid, tid)}" for tid in service_task_ids
    )
    doc_content = f"""# {name} – Documentation

This document describes the **{name}** workflow: purpose, diagram, and step-by-step behavior.

## Workflow Overview

{description}

**Inputs:** See `metadata.yaml` `input_schema` and the workflow state class in `workflow.py`.

**Outputs:** See `output_schema` in `metadata.yaml` and state fields used as results.

## Step Descriptions

{step_bullets if step_bullets else "- (No service tasks defined.)"}
"""
    (workflow_dir / "documentation.md").write_text(doc_content.strip() + "\n")
    current_version = workflow_dir / "currentVersion"
    current_version.mkdir(parents=True, exist_ok=True)
    (current_version / "workflow.bpmn").write_text(bpmn_xml)
    class_name = workflow_id.title().replace("_", "") + "Workflow"
    executor_module = f"workflows.{workflow_id}.workflow"
    bindings_lines = [
        "# BPMN element → handler bindings",
        f"workflow_id: {workflow_id}",
        f"executor: {executor_module}.{class_name}",
        "",
        "serviceTasks:",
    ]
    for task_id in service_task_ids:
        desc = step_descriptions.get(task_id, task_id.replace("_", " ").title())
        desc_safe = desc.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ").strip()
        bindings_lines.append(f"  {task_id}:")
        bindings_lines.append(f"    handler: {task_id}")
        bindings_lines.append(f'    description: "{desc_safe}"')
    (current_version / "bpmn-bindings.yaml").write_text("\n".join(bindings_lines) + "\n")


def create_workflow(
    name: str,
    workflow_id: str,
    icon: str,
    category: str,
    description: str,
    prompt: str,
    model_short_key: str = "claude-sonnet-4",
) -> str:
    """
    Create a new workflow: directory, LLM-generated files, registry reload.
    Raises ValidationError, WorkflowExistsError. Returns workflow_id.
    """
    workflow_dir = _create_workflow_directory(workflow_id)  # raises WorkflowExistsError
    context_content, workflow_guidelines = _load_context_files(REPO_ROOT)
    workflow_code = _generate_workflow_code(
        model_short_key,
        name,
        workflow_id,
        category,
        description,
        prompt,
        context_content,
        workflow_guidelines,
    )
    readme_content = _generate_readme(
        model_short_key, name, workflow_id, category, description, prompt
    )
    bpmn_xml, service_task_ids = _generate_bpmn(
        model_short_key, name, workflow_id, description, prompt
    )
    _validate_generated_bpmn_and_bindings(bpmn_xml, service_task_ids, workflow_id, workflow_code)
    user_story_content = _generate_user_story(
        model_short_key, name, workflow_id, category, description, prompt, service_task_ids
    )
    _create_workflow_files(
        workflow_dir,
        workflow_code,
        readme_content,
        user_story_content,
        name,
        workflow_id,
        icon,
        category,
        description,
        bpmn_xml,
        service_task_ids,
    )
    from agent_app.workflow_registry import workflow_registry

    workflow_registry.reload()
    return workflow_id


def save_workflow(
    workflow_id: str,
    metadata_updates: dict,
    file_updates: dict,
    bindings_json: Any,
    version_info: dict,
    user_id: int,
) -> tuple[Any, dict]:
    """
    Update workflow metadata and files, validate BPMN context, create version, reload registry.
    Returns (version, validation). Raises WorkflowNotFoundError, ValueError.
    """
    from agent_app.workflow_context import (
        dump_bindings_yaml,
        get_workflow_context,
        normalize_bindings,
        parse_bpmn_xml,
        validate_bpmn_bindings_context,
        validate_bpmn_for_save,
    )
    from agent_app.version_manager import version_manager
    from agent_app.workflow_registry import workflow_registry

    workflow = workflow_registry.get(workflow_id)
    if not workflow:
        raise WorkflowNotFoundError(workflow_id)

    workflow_path = REPO_ROOT / "workflows" / workflow_id
    meta = workflow.get("metadata")
    assets_path = getattr(meta, "current_version_path", None) or workflow_path

    if bindings_json is not None:
        file_updates = dict(file_updates)
        normalized_bindings = normalize_bindings(bindings_json, workflow_id=workflow_id)
        file_updates["bpmn-bindings.yaml"] = dump_bindings_yaml(normalized_bindings)

    # Save-time BPMN validation (graph, gateways, bindings) before writing files
    if "workflow.bpmn" in file_updates:
        bpmn_xml = file_updates["workflow.bpmn"]
        if bpmn_xml and isinstance(bpmn_xml, str):
            bpmn = parse_bpmn_xml(bpmn_xml)
            if "parse_error" not in bpmn:
                bindings_for_check: dict | None = None
                if "bpmn-bindings.yaml" in file_updates:
                    bindings_for_check = normalize_bindings(
                        _bindings_dict_from_yaml(file_updates["bpmn-bindings.yaml"]),
                        workflow_id=workflow_id,
                    )
                else:
                    p = assets_path / "bpmn-bindings.yaml"
                    if p.exists():
                        bindings_for_check = normalize_bindings(
                            _bindings_dict_from_yaml(p.read_text(encoding="utf-8")),
                            workflow_id=workflow_id,
                        )
                save_errors = validate_bpmn_for_save(bpmn, bindings_for_check)
                if save_errors:
                    raise ValueError(
                        "Invalid BPMN or bindings. Fix before saving: " + " ".join(save_errors)
                    )

    metadata_file = workflow_path / "metadata.yaml"
    if metadata_file.exists():
        with open(metadata_file, encoding="utf-8") as f:
            metadata_dict = yaml.safe_load(f)
        metadata_dict["name"] = metadata_updates.get("name", metadata_dict.get("name"))
        metadata_dict["description"] = metadata_updates.get(
            "description", metadata_dict.get("description")
        )
        metadata_dict["icon"] = metadata_updates.get("icon", metadata_dict.get("icon"))
        metadata_dict["category"] = metadata_updates.get("category", metadata_dict.get("category"))
        metadata_dict["estimated_duration"] = metadata_updates.get(
            "estimated_duration", metadata_dict.get("estimated_duration")
        )
        if "input_schema" in metadata_updates and isinstance(
            metadata_updates["input_schema"], dict
        ):
            metadata_dict["input_schema"] = metadata_updates["input_schema"]
        if "outputs" in metadata_updates and isinstance(metadata_updates["outputs"], list):
            metadata_dict["outputs"] = metadata_updates["outputs"]
        with open(metadata_file, "w", encoding="utf-8") as f:
            yaml.dump(metadata_dict, f, default_flow_style=False, allow_unicode=True)

    bpmn_files = {"workflow.bpmn", "bpmn-bindings.yaml"}
    for filename, content in file_updates.items():
        base = assets_path if filename in bpmn_files else workflow_path
        file_path = base / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")

    validation = validate_bpmn_bindings_context(get_workflow_context(workflow_id))
    version = version_manager.create_version(
        workflow_id=workflow_id,
        user_id=user_id,
        comment=version_info.get("comment", ""),
        tag=version_info.get("tag"),
    )
    workflow_registry.reload()
    return (version, validation)


def restore_version(workflow_id: str, version_number: int, user_id: int) -> Any:
    """Restore workflow to specific version. Raises ValueError if version not found."""
    from agent_app.version_manager import version_manager

    return version_manager.restore_version(workflow_id, version_number, user_id)


def tag_version(workflow_id: str, version_number: int, tag: str) -> None:
    """Add or update tag for version. Raises ValueError if version not found."""
    from agent_app.version_manager import version_manager

    version_manager.tag_version(workflow_id, version_number, tag)


def get_version_files(workflow_id: str, version_number: int) -> dict:
    """Get file contents for specific version. Raises ValueError if not found."""
    from agent_app.version_manager import version_manager

    return version_manager.get_version_files(workflow_id, version_number)


def generate_user_story_content(
    model_short_key: str,
    name: str,
    workflow_id: str,
    category: str,
    description: str,
    prompt: str,
    service_task_ids: list[str],
) -> str:
    """Generate USER_STORY.md content via LLM (or fallback). Used by generate_workflow_user_story view."""
    return _generate_user_story(
        model_short_key, name, workflow_id, category, description, prompt, service_task_ids
    )
