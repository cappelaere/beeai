"""
BPMN-aware tools for the BPMN Expert agent.
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
from collections import deque
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from beeai_framework.tools import StringToolOutput, tool

_REPO_ROOT = Path(__file__).parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

logger = logging.getLogger(__name__)


def _setup_django():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "agent_ui.settings")
    import django

    if not django.apps.apps.ready:
        django.setup()


def _get_context_module():
    _setup_django()
    from agent_app.workflow_context import (
        BPMN_MODEL_NS,
        BPMN_NAMESPACES,
        dump_bindings_yaml,
        get_next_step_expression,
        get_workflow_context,
        normalize_bindings,
        parse_bpmn_xml,
        validate_bpmn_bindings_context,
    )

    return {
        "BPMN_MODEL_NS": BPMN_MODEL_NS,
        "BPMN_NAMESPACES": BPMN_NAMESPACES,
        "dump_bindings_yaml": dump_bindings_yaml,
        "get_next_step_expression": get_next_step_expression,
        "get_workflow_context": get_workflow_context,
        "normalize_bindings": normalize_bindings,
        "parse_bpmn_xml": parse_bpmn_xml,
        "validate_bpmn_bindings_context": validate_bpmn_bindings_context,
    }


def _json_output(payload: dict[str, Any]) -> StringToolOutput:
    return StringToolOutput(json.dumps(payload, indent=2))


def _slugify_handler_name(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_]+", "_", value.strip().lower())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned or "new_workflow_step"


def _parse_json_list(value: str) -> list[Any]:
    value = (value or "").strip()
    if not value:
        return []
    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return parsed
    except json.JSONDecodeError:
        pass
    return [item.strip() for item in value.split(",") if item.strip()]


def _write_text(path_str: str, content: str):
    path = Path(path_str)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _reload_workflow_registry():
    _setup_django()
    from agent_app.workflow_registry import workflow_registry

    workflow_registry.reload()


def _normalize_bpmn_xml_input(raw: str) -> str:
    """Strip markdown code fences and extract BPMN XML from raw tool input."""
    text = (raw or "").strip()
    if "<?xml" in text:
        start = text.index("<?xml")
    elif "<bpmn:definitions" in text:
        start = text.index("<bpmn:definitions")
        text = '<?xml version="1.0" encoding="UTF-8"?>\n' + text[start:]
        start = 0
    else:
        start = 0
    if "</bpmn:definitions>" in text:
        end = text.index("</bpmn:definitions>") + len("</bpmn:definitions>")
        return text[start:end].strip()
    return text[start:].strip()


def _build_stub(
    context: dict[str, Any], task_id: str, handler_name: str, description: str = ""
) -> str:
    state_class = context.get("code", {}).get("state_class_name")
    annotation = f": {state_class}" if state_class else ""
    next_step = _get_context_module()["get_next_step_expression"](context["bpmn"], task_id)
    docstring = description or f"Generated handler stub for BPMN task '{task_id}'."
    return (
        f"    async def {handler_name}(self, state{annotation}) -> str:\n"
        f'        """{docstring}"""\n'
        f'        state.workflow_steps.append("{task_id}")\n'
        f"        # TODO: Implement task logic.\n"
        f"        return {next_step}\n"
    )


def _insert_handler_stub(workflow_py: str, stub: str, handler_name: str) -> tuple[str, bool]:
    if f"async def {handler_name}(" in workflow_py:
        return workflow_py, False

    match = re.search(r"(?m)^    async def run\(", workflow_py)
    if match:
        updated = workflow_py[: match.start()] + stub + "\n" + workflow_py[match.start() :]
        return updated, True

    updated = workflow_py.rstrip() + "\n\n" + stub + "\n"
    return updated, True


def _find_path(bpmn: dict[str, Any], start_id: str, end_id: str) -> list[str]:
    if start_id == end_id:
        return [start_id]
    queue = deque([(start_id, [start_id])])
    seen = {start_id}
    while queue:
        current, path = queue.popleft()
        element = (bpmn.get("elements") or {}).get(current) or {}
        for target in element.get("outgoing") or []:
            if not target or target in seen:
                continue
            next_path = path + [target]
            if target == end_id:
                return next_path
            seen.add(target)
            queue.append((target, next_path))
    return []


def _update_bpmn_bindings_impl(
    workflow_id: str,
    task_id: str,
    handler_name: str,
    description: str = "",
    inputs_json: str = "",
    outputs_json: str = "",
    apply: bool = False,
) -> dict[str, Any]:
    helpers = _get_context_module()
    context = helpers["get_workflow_context"](workflow_id)
    bindings = helpers["normalize_bindings"](
        context["bindings"],
        workflow_id=workflow_id,
        executor=context["bindings"].get("executor", ""),
    )
    bindings["serviceTasks"][task_id] = {
        "handler": handler_name.strip(),
        "description": description.strip(),
    }
    inputs_list = _parse_json_list(inputs_json)
    outputs_list = _parse_json_list(outputs_json)
    if inputs_list:
        bindings["serviceTasks"][task_id]["inputs"] = inputs_list
    if outputs_list:
        bindings["serviceTasks"][task_id]["outputs"] = outputs_list

    yaml_text = helpers["dump_bindings_yaml"](bindings)
    if apply:
        _write_text(context["files"]["bindings_path"], yaml_text)
        _reload_workflow_registry()

    return {
        "workflow_id": workflow_id,
        "task_id": task_id,
        "apply": apply,
        "bindings_yaml": yaml_text,
    }


def _generate_workflow_handler_impl(
    workflow_id: str,
    task_id: str,
    handler_name: str = "",
    description: str = "",
    apply: bool = False,
) -> dict[str, Any]:
    helpers = _get_context_module()
    context = helpers["get_workflow_context"](workflow_id)
    selected = (context["bpmn"].get("elements") or {}).get(task_id)
    if not selected:
        return {"error": f"BPMN element '{task_id}' not found"}

    resolved_handler = handler_name.strip() or _slugify_handler_name(task_id)
    stub = _build_stub(context, task_id, resolved_handler, description)
    updated_workflow_py, changed = _insert_handler_stub(
        context["workflow_py"], stub, resolved_handler
    )

    if apply and changed:
        _write_text(context["files"]["workflow_py_path"], updated_workflow_py)
        _reload_workflow_registry()

    return {
        "workflow_id": workflow_id,
        "task_id": task_id,
        "handler_name": resolved_handler,
        "apply": apply,
        "changed": changed,
        "stub": stub,
    }


@tool
def get_workflow_context(workflow_id: str, selected_element_id: str = "") -> StringToolOutput:
    """
    Load BPMN, bindings, and workflow.py context for a workflow.
    """
    try:
        helpers = _get_context_module()
        context = helpers["get_workflow_context"](
            workflow_id, selected_element_id=selected_element_id
        )
        payload = {
            "workflow": context["workflow"],
            "files": context["files"],
            "code": context["code"],
            "bpmn": {
                "process_id": context["bpmn"].get("process_id"),
                "process_name": context["bpmn"].get("process_name"),
                "counts": context["bpmn"].get("counts"),
                "ordered_service_task_ids": context["bpmn"].get("ordered_service_task_ids"),
            },
            "bindings": context["bindings"],
            "selected_element": context.get("selected_element"),
        }
        return _json_output(payload)
    except Exception as exc:
        return _json_output({"error": str(exc)})


@tool
def analyze_bpmn_diagram(
    workflow_id: str,
    selected_element_id: str = "",
    question: str = "",
) -> StringToolOutput:
    """
    Analyze a BPMN workflow and summarize structure, bindings, and likely issues.
    """
    try:
        helpers = _get_context_module()
        context = helpers["get_workflow_context"](
            workflow_id, selected_element_id=selected_element_id
        )
        validation = helpers["validate_bpmn_bindings_context"](context)
        payload = {
            "workflow": context["workflow"],
            "question": question,
            "selected_element": context.get("selected_element"),
            "diagram_summary": {
                "counts": context["bpmn"].get("counts"),
                "service_tasks": [
                    {
                        "id": element_id,
                        "name": (context["bpmn"]["elements"].get(element_id) or {}).get("name", ""),
                    }
                    for element_id in context["bpmn"].get("ordered_service_task_ids", [])
                ],
            },
            "binding_validation": validation,
            "handlers": context["code"].get("handler_names", []),
        }
        return _json_output(payload)
    except Exception as exc:
        return _json_output({"error": str(exc)})


@tool
def explain_workflow_path(
    workflow_id: str,
    start_element_id: str = "",
    end_element_id: str = "",
) -> StringToolOutput:
    """
    Explain the execution path between BPMN elements.
    """
    try:
        helpers = _get_context_module()
        context = helpers["get_workflow_context"](workflow_id)
        bpmn = context["bpmn"]
        elements = bpmn.get("elements") or {}

        if not start_element_id:
            start_element_id = next(
                (
                    element_id
                    for element_id, element in elements.items()
                    if element.get("type") == "startEvent"
                ),
                "",
            )
        if not end_element_id:
            end_element_id = next(
                (
                    element_id
                    for element_id, element in elements.items()
                    if element.get("type") == "endEvent"
                ),
                "",
            )

        path = _find_path(bpmn, start_element_id, end_element_id)
        explained = []
        for element_id in path:
            element = elements.get(element_id) or {}
            explained.append(
                {
                    "id": element_id,
                    "type": element.get("type"),
                    "name": element.get("name", ""),
                }
            )
        return _json_output(
            {
                "workflow_id": workflow_id,
                "start_element_id": start_element_id,
                "end_element_id": end_element_id,
                "path_found": bool(path),
                "path": explained,
            }
        )
    except Exception as exc:
        return _json_output({"error": str(exc)})


@tool
def validate_bpmn_bindings(
    workflow_id: str,
    bpmn_xml: str = "",
    bindings_yaml: str = "",
) -> StringToolOutput:
    """
    Validate service task bindings against BPMN ids and workflow handler names.
    Use workflow_id only to validate what is saved on disk. Pass optional bpmn_xml
    and/or bindings_yaml (e.g. from the user's current editor state) to validate
    a diagram the user has just changed before saving.
    """
    try:
        helpers = _get_context_module()
        get_workflow_context = helpers["get_workflow_context"]
        validate = helpers["validate_bpmn_bindings_context"]

        bpmn_override = bpmn_xml.strip() if (bpmn_xml and bpmn_xml.strip()) else None
        bindings_override = (
            bindings_yaml.strip() if (bindings_yaml and bindings_yaml.strip()) else None
        )

        context = get_workflow_context(
            workflow_id,
            bpmn_xml_override=bpmn_override,
            bindings_yaml_override=bindings_override,
        )
        return _json_output(validate(context))
    except Exception as exc:
        return _json_output({"error": str(exc)})


@tool
def suggest_handler_stub(
    workflow_id: str,
    task_id: str,
    handler_name: str = "",
    description: str = "",
) -> StringToolOutput:
    """
    Generate a handler stub for a BPMN task without modifying files.
    """
    try:
        helpers = _get_context_module()
        context = helpers["get_workflow_context"](workflow_id)
        selected = (context["bpmn"].get("elements") or {}).get(task_id)
        if not selected:
            return _json_output({"error": f"BPMN element '{task_id}' not found"})

        resolved_handler = handler_name.strip() or _slugify_handler_name(task_id)
        stub = _build_stub(context, task_id, resolved_handler, description)
        return _json_output(
            {
                "workflow_id": workflow_id,
                "task_id": task_id,
                "handler_name": resolved_handler,
                "next_step": _get_context_module()["get_next_step_expression"](
                    context["bpmn"], task_id
                ),
                "stub": stub,
            }
        )
    except Exception as exc:
        return _json_output({"error": str(exc)})


@tool
def update_bpmn_bindings(
    workflow_id: str,
    task_id: str,
    handler_name: str,
    description: str = "",
    inputs_json: str = "",
    outputs_json: str = "",
    apply: bool = False,
) -> StringToolOutput:
    """
    Add or update a BPMN task binding. By default this returns a proposal; set apply=True to persist it.
    """
    try:
        return _json_output(
            _update_bpmn_bindings_impl(
                workflow_id,
                task_id,
                handler_name,
                description=description,
                inputs_json=inputs_json,
                outputs_json=outputs_json,
                apply=apply,
            )
        )
    except Exception as exc:
        return _json_output({"error": str(exc)})


@tool
def update_workflow_bpmn(
    workflow_id: str,
    element_id: str,
    new_name: str,
    apply: bool = False,
) -> StringToolOutput:
    """
    Rename a BPMN element. By default this returns the updated BPMN XML; set apply=True to persist it.
    """
    try:
        helpers = _get_context_module()
        context = helpers["get_workflow_context"](workflow_id)
        bpmn_xml = context["bpmn_xml"]
        if not bpmn_xml.strip():
            return _json_output({"error": "Workflow has no BPMN XML"})

        root = ET.fromstring(bpmn_xml)
        target = root.find(f".//*[@id='{element_id}']")
        if target is None:
            return _json_output({"error": f"BPMN element '{element_id}' not found"})
        target.set("name", new_name)
        updated_xml = ET.tostring(root, encoding="unicode")
        if updated_xml and not updated_xml.startswith("<?xml"):
            updated_xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + updated_xml
        if apply:
            _write_text(context["files"]["bpmn_path"], updated_xml)
            _reload_workflow_registry()

        return _json_output(
            {
                "workflow_id": workflow_id,
                "element_id": element_id,
                "apply": apply,
                "bpmn_xml": updated_xml,
            }
        )
    except Exception as exc:
        return _json_output({"error": str(exc)})


@tool
def apply_bpmn_diagram(
    workflow_id: str,
    bpmn_xml: str,
    apply: bool = False,
) -> StringToolOutput:
    """
    Validate and optionally apply a full BPMN diagram (structural change). Use for add/remove/move tasks, gateways, or flows.
    By default returns validation summary only; set apply=True to write to workflow.bpmn after user confirmation.
    """
    try:
        helpers = _get_context_module()
        get_workflow_context = helpers["get_workflow_context"]
        parse_bpmn_xml = helpers["parse_bpmn_xml"]

        normalized_xml = _normalize_bpmn_xml_input(bpmn_xml)
        if not normalized_xml.strip():
            return _json_output({"success": False, "error": "No BPMN XML provided"})

        context = get_workflow_context(workflow_id)
        bpmn_path = context["files"]["bpmn_path"]

        summary = parse_bpmn_xml(normalized_xml)
        if summary.get("parse_error"):
            return _json_output(
                {
                    "success": False,
                    "error": f"Invalid BPMN XML: {summary['parse_error']}",
                    "parse_error": summary["parse_error"],
                }
            )
        if not summary.get("process_id") or not summary.get("elements"):
            return _json_output(
                {
                    "success": False,
                    "error": "BPMN XML has no process or no elements; check that it contains bpmn:process with tasks and flows.",
                }
            )
        counts = summary.get("counts") or {}
        if counts.get("startEvent", 0) < 1 or counts.get("endEvent", 0) < 1:
            return _json_output(
                {
                    "success": False,
                    "error": "Diagram must contain at least one startEvent and one endEvent.",
                }
            )

        service_task_ids = list(summary.get("ordered_service_task_ids") or [])
        user_task_ids = [
            eid
            for eid, el in (summary.get("elements") or {}).items()
            if el.get("type") == "userTask"
        ]
        task_ids_note = (
            "Consider adding bindings for any new task ids."
            if (service_task_ids or user_task_ids)
            else ""
        )

        if apply:
            logger.info(
                "[apply_bpmn_diagram] Applying BPMN diagram: workflow_id=%s path=%s xml_len=%d",
                workflow_id,
                bpmn_path,
                len(normalized_xml),
            )
            logger.info(
                "[apply_bpmn_diagram] Diagram summary: process_id=%s service_tasks=%s user_tasks=%s counts=%s",
                summary.get("process_id"),
                service_task_ids,
                user_task_ids,
                counts,
            )
            _write_text(bpmn_path, normalized_xml)
            logger.info("[apply_bpmn_diagram] Wrote %s", bpmn_path)
            _reload_workflow_registry()
            logger.info("[apply_bpmn_diagram] Reloaded workflow registry")
            message = "BPMN diagram applied successfully. " + task_ids_note
        else:
            message = "Validation passed. Call with apply=True to persist. " + task_ids_note

        return _json_output(
            {
                "success": True,
                "message": message.strip(),
                "apply": apply,
                "workflow_id": workflow_id,
                "service_task_ids": service_task_ids,
                "user_task_ids": user_task_ids,
                "counts": counts,
            }
        )
    except ValueError as exc:
        return _json_output({"success": False, "error": str(exc)})
    except Exception as exc:
        logger.exception("apply_bpmn_diagram failed")
        return _json_output({"success": False, "error": str(exc)})


@tool
def generate_workflow_handler(
    workflow_id: str,
    task_id: str,
    handler_name: str = "",
    description: str = "",
    apply: bool = False,
) -> StringToolOutput:
    """
    Generate a workflow.py handler stub. By default this returns a proposal; set apply=True to insert it.
    """
    try:
        return _json_output(
            _generate_workflow_handler_impl(
                workflow_id,
                task_id,
                handler_name=handler_name,
                description=description,
                apply=apply,
            )
        )
    except Exception as exc:
        return _json_output({"error": str(exc)})


@tool
def sync_task_to_handler(
    workflow_id: str,
    task_id: str,
    handler_name: str = "",
    description: str = "",
    apply: bool = False,
) -> StringToolOutput:
    """
    Ensure a BPMN task has both a binding entry and a workflow.py handler stub.
    """
    try:
        resolved_handler = handler_name.strip() or _slugify_handler_name(task_id)
        binding_result = _update_bpmn_bindings_impl(
            workflow_id,
            task_id,
            resolved_handler,
            description=description,
            apply=apply,
        )
        handler_result = _generate_workflow_handler_impl(
            workflow_id,
            task_id,
            handler_name=resolved_handler,
            description=description,
            apply=apply,
        )
        return _json_output(
            {
                "workflow_id": workflow_id,
                "task_id": task_id,
                "handler_name": resolved_handler,
                "apply": apply,
                "binding_result": binding_result,
                "handler_result": handler_result,
            }
        )
    except Exception as exc:
        return _json_output({"error": str(exc)})


def _get_fallback_bpmn(workflow_id: str, name: str) -> str:
    """Minimal valid BPMN 2.0 with one start, one serviceTask, one end."""
    process_id = workflow_id.replace("_", " ").title().replace(" ", "") + "_Process"
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:di="http://www.omg.org/spec/DD/20100524/DI" id="Definitions_{workflow_id}" targetNamespace="http://bpmn.io/schema/bpmn">
  <bpmn:process id="{process_id}" name="{name}" isExecutable="true">
    <bpmn:startEvent id="StartEvent_1" name="Start" />
    <bpmn:sequenceFlow id="Flow_start_to_main" sourceRef="StartEvent_1" targetRef="main_step" />
    <bpmn:serviceTask id="main_step" name="Main step" />
    <bpmn:sequenceFlow id="Flow_main_to_end" sourceRef="main_step" targetRef="EndEvent_1" />
    <bpmn:endEvent id="EndEvent_1" name="End" />
  </bpmn:process>
  <bpmndi:BPMNDiagram id="BPMNDiagram_1">
    <bpmndi:BPMNPlane id="BPMNPlane_1" bpmnElement="{process_id}">
      <bpmndi:BPMNShape id="StartEvent_1_di" bpmnElement="StartEvent_1">
        <dc:Bounds x="152" y="102" width="36" height="36" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="main_step_di" bpmnElement="main_step">
        <dc:Bounds x="240" y="80" width="100" height="80" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="EndEvent_1_di" bpmnElement="EndEvent_1">
        <dc:Bounds x="382" y="102" width="36" height="36" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNEdge id="Flow_start_to_main_di" bpmnElement="Flow_start_to_main">
        <di:waypoint x="188" y="120" />
        <di:waypoint x="240" y="120" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow_main_to_end_di" bpmnElement="Flow_main_to_end">
        <di:waypoint x="340" y="120" />
        <di:waypoint x="382" y="120" />
      </bpmndi:BPMNEdge>
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</bpmn:definitions>"""


def create_new_bpmn_impl(
    workflow_id: str,
    name: str,
    description: str,
    requirements_prompt: str,
    model_short_key: str = "claude-sonnet-4",
) -> tuple[str, list[str]]:
    """
    Generate BPMN 2.0 XML for a new workflow (greenfield). Used by the BPMN Expert
    tool and by the Workflow Studio. Returns (bpmn_xml, service_task_ids).
    """
    from agents.base import run_generation_prompt_sync

    process_id = workflow_id.replace("_", " ").title().replace(" ", "") + "_Process"
    bpmn_prompt = f"""You are a BPMN 2.0 expert. Generate a valid BPMN 2.0 XML diagram for this workflow.

Workflow Name: {name}
Workflow ID: {workflow_id}
Description: {description}

User requirements (steps and logic):
{requirements_prompt}

Requirements:
- Output valid BPMN 2.0 XML only. Use standard namespaces: xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL", xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI", xmlns:dc="http://www.omg.org/spec/DD/20100524/DC", xmlns:di="http://www.omg.org/spec/DD/20100524/DI".
- Process id must be: {process_id}.
- Include exactly one startEvent (id="StartEvent_1") and one endEvent (id="EndEvent_1").
- Model each automated step as a bpmn:serviceTask with id in snake_case (e.g. validate_input, title_search). These ids will map to Python method names.
- Connect all elements with bpmn:sequenceFlow (sourceRef/targetRef).
- Include a bpmndi:BPMNDiagram with bpmndi:BPMNPlane and bpmndi:BPMNShape for each element (dc:Bounds with x, y, width, height) and bpmndi:BPMNEdge for each flow.
- Do not use Mermaid or any other format. Output only the BPMN XML, no markdown code fence."""

    try:
        raw = run_generation_prompt_sync(bpmn_prompt, model_short_key, max_tokens=6000)
        if "<?xml" in raw:
            start = raw.index("<?xml")
        elif "<bpmn:definitions" in raw:
            start = raw.index("<bpmn:definitions")
            raw = '<?xml version="1.0" encoding="UTF-8"?>\n' + raw[start:]
            start = 0
        else:
            start = 0
        if "</bpmn:definitions>" in raw:
            end = raw.index("</bpmn:definitions>") + len("</bpmn:definitions>")
            bpmn_xml = raw[start:end].strip()
        else:
            bpmn_xml = raw[start:].strip()
        task_ids = re.findall(r'<bpmn:serviceTask\s+id="([^"]+)"', bpmn_xml)
        return bpmn_xml, task_ids
    except Exception as e:
        logger.exception("Failed to generate BPMN")
        return _get_fallback_bpmn(workflow_id, name), ["main_step"]


@tool
def create_new_bpmn_diagram(
    workflow_id: str,
    name: str,
    description: str,
    requirements_prompt: str,
    model_short_key: str = "claude-sonnet-4",
) -> StringToolOutput:
    """
    Generate a new BPMN 2.0 diagram for a workflow that does not exist yet (greenfield).
    Use this when the user wants to create a new workflow from a description. Returns
    the BPMN XML and the list of service task ids for bindings.
    """
    try:
        bpmn_xml, service_task_ids = create_new_bpmn_impl(
            workflow_id,
            name,
            description,
            requirements_prompt,
            model_short_key=model_short_key,
        )
        return _json_output(
            {
                "workflow_id": workflow_id,
                "bpmn_xml": bpmn_xml,
                "service_task_ids": service_task_ids,
            }
        )
    except Exception as exc:
        return _json_output({"error": str(exc)})
