"""
Workflow context helpers for BPMN-aware tooling and editor copilots.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any, Callable
from xml.etree import ElementTree as ET

import yaml

from agent_app.bpmn_conditions import is_supported_condition_syntax

BPMN_MODEL_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
BPMN_NAMESPACES = {
    "bpmn": BPMN_MODEL_NS,
    "bpmndi": "http://www.omg.org/spec/BPMN/20100524/DI",
    "dc": "http://www.omg.org/spec/DD/20100524/DC",
    "di": "http://www.omg.org/spec/DD/20100524/DI",
}

ET.register_namespace("bpmn", BPMN_NAMESPACES["bpmn"])
ET.register_namespace("bpmndi", BPMN_NAMESPACES["bpmndi"])
ET.register_namespace("dc", BPMN_NAMESPACES["dc"])
ET.register_namespace("di", BPMN_NAMESPACES["di"])

_BPMN_EXECUTION_TYPES = {
    "serviceTask",
    "userTask",
    "task",
    "scriptTask",
    "exclusiveGateway",
    "parallelGateway",
    "startEvent",
    "endEvent",
    "intermediateCatchEvent",
}
# PAR-016: subProcess shell is parsed separately (not in _BPMN_EXECUTION_TYPES counts baseline)

_BOUNDARY_ATTACHABLE_TYPES = frozenset(
    {"serviceTask", "userTask", "task", "scriptTask"}
)


def iso8601_duration_to_seconds(duration: str) -> float | None:
    """Parse XSD duration subset used in BPMN (e.g. PT5M, PT1.5S, P1D). Returns None if invalid."""
    if not duration or not isinstance(duration, str):
        return None
    s = duration.strip()
    if not s.startswith("P"):
        return None
    total = 0.0
    if "T" not in s:
        date_part, time_part = s[1:], ""
    else:
        i = s.index("T")
        date_part, time_part = s[1:i], s[i + 1 :]
    m = re.match(r"^(\d+)W$", date_part)
    if m:
        total += int(m.group(1)) * 604800.0
        date_part = ""
    m = re.match(r"^(\d+)D", date_part)
    if m:
        total += int(m.group(1)) * 86400.0
        date_part = date_part[m.end() :]  # noqa: SLF001
    if date_part and date_part != "":
        return None
    for unit, mult in (("H", 3600), ("M", 60), ("S", 1)):
        pat = rf"(\d+(?:\.\d+)?){unit}"
        mm = re.search(pat, time_part)
        if mm:
            total += float(mm.group(1)) * mult
            time_part = time_part.replace(mm.group(0), "", 1)
    if re.sub(r"\s", "", time_part):
        return None
    return total if total > 0 else None


def get_timer_boundary_for_task(bpmn: dict[str, Any], task_id: str) -> dict[str, Any] | None:
    spec = (bpmn.get("boundary_by_task") or {}).get(task_id) or {}
    return spec.get("timer")


def get_error_boundary_for_task(bpmn: dict[str, Any], task_id: str) -> dict[str, Any] | None:
    spec = (bpmn.get("boundary_by_task") or {}).get(task_id) or {}
    return spec.get("error")


def boundary_events_for_task(bpmn: dict[str, Any], task_id: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    spec = (bpmn.get("boundary_by_task") or {}).get(task_id) or {}
    for k in ("timer", "error"):
        b = spec.get(k)
        if isinstance(b, dict):
            out.append(dict(b, kind=k))
    return out


def _parse_one_boundary_event(child: Any, summary: dict[str, Any]) -> None:
    """Register a single boundaryEvent element (PAR-014)."""
    flows = summary.get("sequence_flows") or {}
    bid = child.get("id")
    attached = (child.get("attachedToRef") or "").strip()
    if not bid or not attached:
        return
    cancel_raw = (child.get("cancelActivity") or "true").strip().lower()
    interrupting = cancel_raw != "false"

    timer_def = child.find(f"{{{BPMN_MODEL_NS}}}timerEventDefinition")
    if timer_def is None:
        timer_def = child.find("timerEventDefinition")
    error_def = child.find(f"{{{BPMN_MODEL_NS}}}errorEventDefinition")
    if error_def is None:
        error_def = child.find("errorEventDefinition")

    kind: str | None = None
    duration_iso: str | None = None
    if timer_def is not None:
        kind = "timer"
        td = timer_def.find(f"{{{BPMN_MODEL_NS}}}timeDuration")
        if td is None:
            td = timer_def.find("timeDuration")
        if td is not None and td.text:
            duration_iso = td.text.strip()
    elif error_def is not None:
        kind = "error"
    else:
        kind = "unsupported"

    outs = [f for f in flows.values() if f.get("source") == bid]
    target = (outs[0].get("target") if len(outs) == 1 else None) or ""
    flow_id = (outs[0].get("id") if len(outs) == 1 else None) or ""

    entry = {
        "boundary_id": bid,
        "attached_to": attached,
        "kind": kind,
        "target_element_id": target,
        "flow_id": flow_id,
        "duration_iso": duration_iso,
        "interrupting": interrupting,
        "outgoing_count": len(outs),
    }
    bucket = summary["boundary_by_task"].setdefault(attached, {})
    if kind == "timer":
        if "timer" in bucket:
            summary.setdefault("boundary_duplicate_timers", []).append((attached, bid))
        bucket["timer"] = entry
    elif kind == "error":
        if "error" in bucket:
            summary.setdefault("boundary_duplicate_errors", []).append((attached, bid))
        bucket["error"] = entry
    else:
        summary.setdefault("boundary_unsupported", []).append(entry)


def _walk_parse_boundary_events(el: Any, summary: dict[str, Any]) -> None:
    """Process + nested subProcess (PAR-016)."""
    for child in list(el):
        lt = _local_name(child.tag)
        if lt == "boundaryEvent":
            _parse_one_boundary_event(child, summary)
        elif lt == "subProcess":
            _walk_parse_boundary_events(child, summary)


def _parse_boundary_events_into_summary(process: Any, summary: dict[str, Any]) -> None:
    """Populate summary['boundary_by_task'] from boundaryEvent under process and subProcesses."""
    summary["boundary_by_task"] = {}
    _walk_parse_boundary_events(process, summary)


def _intermediate_catch_fields_from_element(child: Any) -> dict[str, Any]:
    timer_def = child.find(f"{{{BPMN_MODEL_NS}}}timerEventDefinition")
    if timer_def is None:
        timer_def = child.find("timerEventDefinition")
    msg_def = child.find(f"{{{BPMN_MODEL_NS}}}messageEventDefinition")
    if msg_def is None:
        msg_def = child.find("messageEventDefinition")
    catch_kind: str | None = None
    duration_iso = ""
    message_key = ""
    element_id = (child.get("id") or "").strip()
    if timer_def is not None and msg_def is not None:
        catch_kind = "unsupported"
    elif timer_def is not None:
        catch_kind = "timer"
        td = timer_def.find(f"{{{BPMN_MODEL_NS}}}timeDuration")
        if td is None:
            td = timer_def.find("timeDuration")
        if td is not None and td.text:
            duration_iso = td.text.strip()
    elif msg_def is not None:
        catch_kind = "message"
        mr = (msg_def.get("messageRef") or "").strip()
        nm = (child.get("name") or "").strip()
        message_key = mr or nm or element_id
    else:
        catch_kind = "unsupported"
    return {
        "catch_kind": catch_kind,
        "catch_duration_iso": duration_iso,
        "catch_message_key": message_key,
    }


def _parse_container_children(
    container_el: Any, summary: dict[str, Any], container_id: str | None
) -> None:
    """Parse sequenceFlow + activities; container_id is subprocess id for nested elements (PAR-016)."""
    for child in list(container_el):
        lt = _local_name(child.tag)
        eid = child.get("id")

        if lt == "sequenceFlow":
            if not eid:
                continue
            condition_text = ""
            condition = child.find("bpmn:conditionExpression", BPMN_NAMESPACES)
            if condition is not None and condition.text:
                condition_text = condition.text.strip()
            summary["sequence_flows"][eid] = {
                "id": eid,
                "name": child.get("name", ""),
                "source": child.get("sourceRef"),
                "target": child.get("targetRef"),
                "condition": condition_text,
            }
            continue

        if lt == "subProcess":
            if not eid:
                continue
            if container_id is not None:
                summary.setdefault("nested_subprocess_pairs", []).append((container_id, eid))
            sp_elem: dict[str, Any] = {
                "id": eid,
                "name": child.get("name", ""),
                "type": "subProcess",
                "incoming_flow_ids": [],
                "outgoing_flow_ids": [],
                "incoming": [],
                "outgoing": [],
            }
            if container_id is not None:
                sp_elem["subprocess_container"] = container_id
            summary["elements"][eid] = sp_elem
            summary["ordered_element_ids"].append(eid)
            if container_id is None:
                summary.setdefault("subprocess_root_ids", []).append(eid)
            _parse_container_children(child, summary, eid)
            continue

        if lt not in _BPMN_EXECUTION_TYPES or not eid:
            continue

        elem_data: dict[str, Any] = {
            "id": eid,
            "name": child.get("name", ""),
            "type": lt,
            "incoming_flow_ids": [],
            "outgoing_flow_ids": [],
            "incoming": [],
            "outgoing": [],
        }
        if container_id is not None:
            elem_data["subprocess_container"] = container_id
        if lt == "exclusiveGateway":
            elem_data["default_flow_id"] = child.get("default") or None
        if lt == "intermediateCatchEvent":
            elem_data.update(_intermediate_catch_fields_from_element(child))
        summary["elements"][eid] = elem_data
        summary["ordered_element_ids"].append(eid)
        if lt == "serviceTask":
            summary["ordered_service_task_ids"].append(eid)


def _local_name(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[-1]
    return tag


def _read_text(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def _safe_load_yaml(text: str) -> dict[str, Any]:
    if not text.strip():
        return {}
    loaded = yaml.safe_load(text) or {}
    if isinstance(loaded, dict):
        return loaded
    return {}


def normalize_bindings(
    bindings: dict[str, Any], *, workflow_id: str = "", executor: str = ""
) -> dict[str, Any]:
    normalized = dict(bindings or {})
    if workflow_id and not normalized.get("workflow_id"):
        normalized["workflow_id"] = workflow_id
    if executor and not normalized.get("executor"):
        normalized["executor"] = executor
    service_tasks = normalized.get("serviceTasks") or {}
    normalized["serviceTasks"] = service_tasks if isinstance(service_tasks, dict) else {}
    return normalized


def dump_bindings_yaml(bindings: dict[str, Any]) -> str:
    return yaml.safe_dump(
        bindings,
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=True,
    )


def _get_field_description_from_annotation(node: ast.AST) -> str:
    """Extract description from Field(..., description='...') if present."""
    if not isinstance(node, ast.Call):
        return ""
    for keyword in getattr(node, "keywords", []):
        if getattr(keyword, "arg", None) == "description" and isinstance(
            keyword.value, ast.Constant
        ):
            return str(keyword.value.value)
    return ""


def parse_workflow_python(workflow_py: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "workflow_class_name": None,
        "state_class_name": None,
        "state_field_names": [],
        "state_field_descriptions": {},
        "methods": [],
        "handler_names": [],
        "source_available": bool(workflow_py.strip()),
    }
    if not workflow_py.strip():
        return result

    try:
        tree = ast.parse(workflow_py)
    except SyntaxError as exc:
        result["parse_error"] = str(exc)
        return result

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            if node.name.endswith("State") and not result["state_class_name"]:
                result["state_class_name"] = node.name
                # Collect state class field names (and descriptions from Field) for input_schema
                skip = {"workflow_steps", "model_config"}
                for item in node.body:
                    if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                        name = item.target.id
                        if name in skip or name.startswith("_"):
                            continue
                        result["state_field_names"].append(name)
                        if item.value and isinstance(item.value, ast.Call):
                            desc = _get_field_description_from_annotation(item.value)
                            if desc:
                                result["state_field_descriptions"][name] = desc
            if node.name.endswith("Workflow") and not result["workflow_class_name"]:
                result["workflow_class_name"] = node.name
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        args = [arg.arg for arg in item.args.args if arg.arg not in {"self", "cls"}]
                        method = {
                            "name": item.name,
                            "line": getattr(item, "lineno", None),
                            "is_async": isinstance(item, ast.AsyncFunctionDef),
                            "args": args,
                            "docstring": ast.get_docstring(item) or "",
                        }
                        result["methods"].append(method)

    handler_names = []
    for method in result["methods"]:
        if method["name"].startswith("_") or method["name"] == "run":
            continue
        handler_names.append(method["name"])
    result["handler_names"] = handler_names
    return result


def parse_bpmn_xml(bpmn_xml: str) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "process_id": None,
        "process_name": None,
        "elements": {},
        "sequence_flows": {},
        "ordered_element_ids": [],
        "ordered_service_task_ids": [],
        "counts": {},
    }
    if not bpmn_xml.strip():
        summary["counts"] = {kind: 0 for kind in _BPMN_EXECUTION_TYPES}
        return summary

    try:
        root = ET.fromstring(bpmn_xml)
    except ET.ParseError as exc:
        summary["parse_error"] = str(exc)
        summary["counts"] = {kind: 0 for kind in _BPMN_EXECUTION_TYPES}
        return summary

    process = root.find("bpmn:process", BPMN_NAMESPACES)
    if process is None:
        summary["counts"] = {kind: 0 for kind in _BPMN_EXECUTION_TYPES}
        return summary

    summary["process_id"] = process.get("id")
    summary["process_name"] = process.get("name")
    summary["subprocess_root_ids"] = []
    summary["nested_subprocess_pairs"] = []

    _parse_container_children(process, summary, None)

    for flow in summary["sequence_flows"].values():
        source = flow.get("source")
        target = flow.get("target")
        if source in summary["elements"]:
            summary["elements"][source]["outgoing_flow_ids"].append(flow["id"])
            summary["elements"][source]["outgoing"].append(target)
        if target in summary["elements"]:
            summary["elements"][target]["incoming_flow_ids"].append(flow["id"])
            summary["elements"][target]["incoming"].append(source)

    counts: dict[str, int] = {kind: 0 for kind in _BPMN_EXECUTION_TYPES}
    counts["subProcess"] = 0
    for element in summary["elements"].values():
        t = element.get("type") or ""
        counts[t] = counts.get(t, 0) + 1
    summary["counts"] = counts
    _parse_boundary_events_into_summary(process, summary)
    return summary


def resolve_outgoing_flows(bpmn: dict[str, Any], element_id: str) -> list[tuple[str, str, str]]:
    """
    Return list of (flow_id, target_element_id, condition_text) for the element's outgoing flows.
    Order follows outgoing_flow_ids / outgoing so traversal is deterministic.
    """
    elements = bpmn.get("elements") or {}
    flows = bpmn.get("sequence_flows") or {}
    element = elements.get(element_id)
    if not element:
        return []
    flow_ids = element.get("outgoing_flow_ids") or []
    targets = element.get("outgoing") or []
    if len(flow_ids) != len(targets):
        flow_ids = flow_ids or [""] * len(targets)
        targets = targets or []
    result: list[tuple[str, str, str]] = []
    for i, target_id in enumerate(targets):
        flow_id = flow_ids[i] if i < len(flow_ids) else ""
        cond = (flows.get(flow_id) or {}).get("condition", "") or ""
        result.append((flow_id, target_id, cond))
    return result


FlowSelector = Callable[
    [dict[str, Any], str, list[tuple[str, str, str]], Any, dict[str, Any]], str | None
]


def _traverse_until_executable(
    bpmn: dict[str, Any],
    start_element_id: str | None,
    seen: set[str],
    state: Any,
    bindings: dict[str, Any] | None,
    flow_selector: FlowSelector | None,
    *,
    from_completed: bool,
) -> str | None:
    if not start_element_id or start_element_id in seen:
        return None
    seen.add(start_element_id)
    elements = bpmn.get("elements") or {}
    element = elements.get(start_element_id)
    if not element:
        return None
    el_type = element.get("type", "")
    if el_type in {"serviceTask", "userTask", "task", "scriptTask"}:
        out = element.get("outgoing") or []
        if from_completed and len(out) == 1:
            return _traverse_until_executable(
                bpmn,
                out[0],
                seen,
                state,
                bindings,
                flow_selector,
                from_completed=False,
            )
        return start_element_id
    if el_type == "endEvent":
        return "Workflow.END"
    if el_type == "parallelGateway":
        inc = element.get("incoming") or []
        out = element.get("outgoing") or []
        if len(inc) >= 2 and len(out) == 1:
            return f"Workflow.PARALLEL_JOIN:{start_element_id}"
    if el_type == "subProcess":
        sid = subprocess_internal_start_event_id(bpmn, start_element_id)
        if not sid:
            return None
        st_el = elements.get(sid) or {}
        inn = st_el.get("outgoing") or []
        if len(inn) != 1:
            return None
        seen2 = set(seen)
        return _traverse_until_executable(
            bpmn,
            inn[0],
            seen2,
            state,
            bindings,
            flow_selector,
            from_completed=False,
        )
    if el_type == "intermediateCatchEvent":
        ck = element.get("catch_kind")
        if ck in ("timer", "message"):
            return start_element_id
    outgoing = element.get("outgoing") or []
    if len(outgoing) == 1:
        return _traverse_until_executable(
            bpmn,
            outgoing[0],
            seen,
            state,
            bindings,
            flow_selector,
            from_completed=False,
        )
    if (
        len(outgoing) > 1
        and flow_selector is not None
        and state is not None
        and bindings is not None
    ):
        flows = resolve_outgoing_flows(bpmn, start_element_id)
        chosen_target = flow_selector(bpmn, start_element_id, flows, state, bindings)
        if chosen_target:
            return _traverse_until_executable(
                bpmn,
                chosen_target,
                seen,
                state,
                bindings,
                flow_selector,
                from_completed=False,
            )
    return None


def traverse_until_executable(
    bpmn: dict[str, Any],
    start_element_id: str | None,
    seen: set[str],
    state: Any = None,
    bindings: dict[str, Any] | None = None,
    flow_selector: FlowSelector | None = None,
    *,
    from_completed: bool = False,
) -> str | None:
    """
    From start_element_id, follow a single path through non-executable nodes until
    hitting a serviceTask/userTask/task/scriptTask, a supported intermediateCatchEvent
    (timer/message), parallel join sentinel, or endEvent.

    If *from_completed* is True and *start_element_id* is a bound task with exactly one
    outgoing, traversal continues from that successor (so the next stop after task T
    can be an intermediate catch). Recursive hops always use from_completed=False so
    paths from startEvent still resolve to the first task.

    When hitting multiple outgoing (e.g. exclusiveGateway), use flow_selector if provided.
    Returns: element id, "Workflow.END", join sentinel, or None.
    """
    return _traverse_until_executable(
        bpmn,
        start_element_id,
        seen,
        state,
        bindings,
        flow_selector,
        from_completed=from_completed,
    )


def is_intermediate_timer_catch(bpmn: dict[str, Any], element_id: str) -> bool:
    el = (bpmn.get("elements") or {}).get(element_id) or {}
    return el.get("type") == "intermediateCatchEvent" and el.get("catch_kind") == "timer"


def is_intermediate_message_catch(bpmn: dict[str, Any], element_id: str) -> bool:
    el = (bpmn.get("elements") or {}).get(element_id) or {}
    return el.get("type") == "intermediateCatchEvent" and el.get("catch_kind") == "message"


def intermediate_catch_outgoing_target(bpmn: dict[str, Any], element_id: str) -> str | None:
    el = (bpmn.get("elements") or {}).get(element_id) or {}
    if el.get("type") != "intermediateCatchEvent":
        return None
    out = el.get("outgoing") or []
    if len(out) != 1:
        return None
    return str(out[0]).strip() or None


def subprocess_internal_start_event_id(bpmn: dict[str, Any], sp_id: str) -> str | None:
    for eid, el in (bpmn.get("elements") or {}).items():
        if el.get("subprocess_container") == sp_id and el.get("type") == "startEvent":
            return eid
    return None


def subprocess_parent_continuation_target(bpmn: dict[str, Any], sp_id: str) -> str | None:
    el = (bpmn.get("elements") or {}).get(sp_id) or {}
    if el.get("type") != "subProcess":
        return None
    out = el.get("outgoing") or []
    if len(out) != 1:
        return None
    return str(out[0]).strip() or None


def element_subprocess_container(bpmn: dict[str, Any], element_id: str) -> str | None:
    el = (bpmn.get("elements") or {}).get(element_id) or {}
    c = el.get("subprocess_container")
    return str(c).strip() if c else None


def terminal_end_event_on_single_path(
    bpmn: dict[str, Any], from_id: str, forbidden: set[str]
) -> str | None:
    """Follow 0+ single-outgoing hops until endEvent; None if branched or stuck."""
    elements = bpmn.get("elements") or {}
    seen = set(forbidden)
    cur = from_id
    while cur:
        if cur in seen:
            return None
        seen.add(cur)
        el = elements.get(cur) or {}
        if el.get("type") == "endEvent":
            return cur
        outs = el.get("outgoing") or []
        if len(outs) != 1:
            return None
        cur = outs[0]
    return None


def subprocess_container_after_task_completion_path(
    bpmn: dict[str, Any], first_hop_id: str, seen: set[str]
) -> str | None:
    """If single-path from first_hop_id reaches only an internal endEvent, return its subprocess id."""
    te = terminal_end_event_on_single_path(bpmn, first_hop_id, set(seen))
    if not te:
        return None
    return element_subprocess_container(bpmn, te)


def _subprocess_id_when_task_exits_via_internal_end(
    bpmn: dict[str, Any], completed_task_id: str, first_successor_id: str
) -> str | None:
    """
    PAR-016: Task T inside subprocess SP completed; first successor S. If a single-outgoing
    chain from S reaches an endEvent in SP without passing another service/user/script/task,
    the branch is done — return SP for subprocess_internal_end.
    (If S is another task, normal ("task", S) applies.)
    """
    sp_task = element_subprocess_container(bpmn, completed_task_id)
    if not sp_task:
        return None
    elements = bpmn.get("elements") or {}
    bound_types = {"serviceTask", "userTask", "task", "scriptTask"}
    cur: str | None = first_successor_id
    seen: set[str] = {completed_task_id}
    while cur:
        if cur in seen:
            return None
        seen.add(cur)
        el = elements.get(cur) or {}
        et = el.get("type")
        if et == "endEvent":
            if element_subprocess_container(bpmn, cur) == sp_task:
                return sp_task
            return None
        if et in bound_types:
            return None
        outs = el.get("outgoing") or []
        if len(outs) != 1:
            return None
        cur = str(outs[0]).strip() or None
    return None


def is_subprocess_shell(bpmn: dict[str, Any], element_id: str) -> bool:
    return (bpmn.get("elements") or {}).get(element_id, {}).get("type") == "subProcess"


def validate_bpmn_embedded_subprocesses(bpmn: dict[str, Any]) -> list[str]:
    """PAR-016: embedded subprocess shape (v1)."""
    errors: list[str] = []
    elements = bpmn.get("elements") or {}
    flows = bpmn.get("sequence_flows") or {}

    for parent, nested in bpmn.get("nested_subprocess_pairs") or []:
        errors.append(
            f"Nested embedded subprocess '{nested}' inside '{parent}' is not supported in v1. "
            "Suggestion: flatten or use a single subprocess level."
        )

    for sp_id in bpmn.get("subprocess_root_ids") or []:
        sp_el = elements.get(sp_id) or {}
        if sp_el.get("type") != "subProcess":
            continue
        inside = {eid for eid, el in elements.items() if el.get("subprocess_container") == sp_id}
        starts = [eid for eid in inside if (elements.get(eid) or {}).get("type") == "startEvent"]
        if len(starts) != 1:
            errors.append(
                f"Subprocess '{sp_id}': exactly one internal startEvent required (found {len(starts)})."
            )
        ends = [eid for eid in inside if (elements.get(eid) or {}).get("type") == "endEvent"]
        if len(ends) < 1:
            errors.append(
                f"Subprocess '{sp_id}': at least one internal endEvent required."
            )
        inc = sp_el.get("incoming") or []
        out = sp_el.get("outgoing") or []
        if len(inc) != 1:
            errors.append(
                f"Subprocess '{sp_id}': exactly one incoming flow from parent (found {len(inc)})."
            )
        if len(out) != 1:
            errors.append(
                f"Subprocess '{sp_id}': exactly one outgoing flow to parent continuation (found {len(out)})."
            )
        for _fid, fl in flows.items():
            s, t = fl.get("source"), fl.get("target")
            if not s or not t or s not in elements or t not in elements:
                continue
            sc = elements[s].get("subprocess_container")
            tc = elements[t].get("subprocess_container")
            sin = sc == sp_id
            tin = tc == sp_id
            if sin and not tin:
                errors.append(
                    f"Subprocess '{sp_id}': flow from internal element '{s}' to external '{t}' is not allowed; "
                    "complete via an internal endEvent."
                )
            if tin and not sin and t != sp_id and s != sp_id:
                errors.append(
                    f"Subprocess '{sp_id}': flow into internal '{t}' must come from the subprocess boundary "
                    f"(incoming flow targets the subProcess id), not from '{s}'."
                )

        for eid, el in elements.items():
            if el.get("type") != "parallelGateway":
                continue
            gsp = el.get("subprocess_container")
            if not gsp or gsp != sp_id:
                continue
            if not is_parallel_fork_gateway(bpmn, eid):
                continue
            for _flow_id, tgid, _ in resolve_outgoing_flows(bpmn, eid):
                tg = elements.get(tgid) or {}
                if tg.get("type") == "endEvent":
                    errors.append(
                        f"Parallel gateway '{eid}' inside subprocess '{sp_id}': branch cannot connect "
                        f"directly to endEvent '{tgid}'."
                    )

    return errors


def validate_bpmn_intermediate_catch_events(bpmn: dict[str, Any]) -> list[str]:
    """Validate intermediateCatchEvent (timer/message only, one outgoing, reachable path)."""
    errors: list[str] = []
    elements = bpmn.get("elements") or {}
    for eid, el in elements.items():
        if el.get("type") != "intermediateCatchEvent":
            continue
        ck = el.get("catch_kind")
        out = el.get("outgoing") or []
        if ck == "unsupported" or ck not in ("timer", "message"):
            errors.append(
                f"Intermediate catch '{eid}': only timer (timeDuration) or message "
                "(messageEventDefinition) is supported. Suggestion: use a single timer or message catch."
            )
            continue
        if len(out) != 1:
            errors.append(
                f"Intermediate catch '{eid}': must have exactly one outgoing sequence flow "
                f"(found {len(out)}). Suggestion: connect exactly one flow after the catch."
            )
            continue
        if ck == "timer":
            dur = (el.get("catch_duration_iso") or "").strip()
            if not dur:
                errors.append(
                    f"Intermediate catch '{eid}': timer requires bpmn:timeDuration (e.g. PT5M)."
                )
            elif iso8601_duration_to_seconds(dur) is None:
                errors.append(
                    f"Intermediate catch '{eid}': could not parse timeDuration {dur!r}. "
                    "Suggestion: use ISO-8601 duration such as PT1H, PT90S, P1D."
                )
        if ck == "message":
            mk = (el.get("catch_message_key") or "").strip()
            if not mk:
                errors.append(
                    f"Intermediate catch '{eid}': message catch requires messageRef or element name."
                )
        tgt = out[0]
        if tgt and str(tgt).strip() in elements:
            seen: set[str] = set()
            res = traverse_until_executable(
                bpmn, str(tgt).strip(), seen, state=None, bindings=None, flow_selector=None
            )
            if res is None:
                errors.append(
                    f"Intermediate catch '{eid}': path after catch does not reach a single "
                    "next executable task (ambiguous gateway or dead end)."
                )
    return errors


def _follow_single_path(bpmn: dict[str, Any], start_id: str | None, seen: set[str]) -> str | None:
    """Legacy: follow single path; delegates to traverse_until_executable for compatibility."""
    return traverse_until_executable(bpmn, start_id, seen)


def resolve_next_executable_task(
    bpmn: dict[str, Any],
    current_task_id: str,
    state: Any,
    bindings: dict[str, Any],
    flow_selector: FlowSelector | None,
) -> str | None:
    """
    From current_task_id, resolve the next executable task (or Workflow.END).
    If one outgoing flow: traverse from its target. If multiple (e.g. exclusive gateway):
    call flow_selector to get chosen target, then traverse. Returns None when no path or end.
    """
    elements = bpmn.get("elements") or {}
    element = elements.get(current_task_id)
    if not element:
        return None
    flows = resolve_outgoing_flows(bpmn, current_task_id)
    if not flows:
        return None
    if len(flows) == 1:
        _, target_id, _ = flows[0]
        resolved = traverse_until_executable(
            bpmn,
            target_id,
            seen={current_task_id},
            state=state,
            bindings=bindings,
            flow_selector=flow_selector,
        )
        if resolved == "Workflow.END" or not resolved:
            return None
        return resolved
    # Multiple outgoing flows (e.g. exclusive gateway)
    if flow_selector is None:
        return None
    chosen_target = flow_selector(bpmn, current_task_id, flows, state, bindings)
    if not chosen_target:
        return None
    resolved = traverse_until_executable(
        bpmn,
        chosen_target,
        seen={current_task_id},
        state=state,
        bindings=bindings,
        flow_selector=flow_selector,
    )
    if resolved == "Workflow.END" or not resolved:
        return None
    return resolved


def is_parallel_join_gateway(bpmn: dict[str, Any], element_id: str) -> bool:
    """True if parallelGateway with at least two incoming and exactly one outgoing (join)."""
    el = (bpmn.get("elements") or {}).get(element_id) or {}
    if el.get("type") != "parallelGateway":
        return False
    inc = el.get("incoming") or []
    out = el.get("outgoing") or []
    return len(inc) >= 2 and len(out) == 1


def _merge_fork_branch_correlation_outcomes(
    outcomes: list[tuple[str, str | None]], fork_id: str
) -> tuple[str, str | None]:
    """Combine outcomes from exclusive-gateway branches (same join, all end, or invalid)."""
    if not outcomes:
        raise ValueError(f"Fork {fork_id!r}: exclusive gateway has no outgoing paths.")
    ends = [o for o in outcomes if o[0] == "end"]
    joins = [(o[1], o) for o in outcomes if o[0] == "join" and o[1]]
    if len(ends) == len(outcomes):
        return ("end", None)
    if len(joins) == len(outcomes):
        jset = {j for j, _ in joins}
        if len(jset) != 1:
            raise ValueError(
                f"Fork {fork_id!r}: exclusive paths reach different joins {sorted(jset)!r}."
            )
        return ("join", joins[0][0])
    raise ValueError(
        f"Fork {fork_id!r}: exclusive branches mix end-event paths with paths to a join; "
        "all paths through the gateway must reach the same join or all must end."
    )


def _fork_branch_correlation_outcome(
    bpmn: dict[str, Any],
    el_id: str,
    fork_id: str,
    visiting: set[str],
) -> tuple[str, str | None]:
    """
    Static analysis from a fork outgoing target: eventual endEvent vs first reachable
    parallel join. Supports linear chains (multiple tasks), and exclusiveGateway when every
    outgoing path converges to the same join (or all end). Rejects nested parallel forks,
    non-exclusive multi-out gateways, and cycles.
    """
    if el_id in visiting:
        raise ValueError(f"Cycle in branch from fork {fork_id!r} (element {el_id!r} revisited).")
    elements = bpmn.get("elements") or {}
    el = elements.get(el_id)
    if not el:
        raise ValueError(f"Missing element {el_id!r} on branch from fork {fork_id!r}.")
    typ = (el.get("type") or "").strip()
    visiting_next = visiting | {el_id}

    if typ == "endEvent":
        return ("end", None)

    if typ == "parallelGateway":
        inc = el.get("incoming") or []
        out = el.get("outgoing") or []
        if len(inc) >= 2 and len(out) == 1:
            return ("join", el_id)
        if len(inc) == 1 and len(out) >= 2:
            raise ValueError(
                f"Nested parallel fork at {el_id!r} under fork {fork_id!r} is not supported."
            )
        raise ValueError(f"Unsupported parallelGateway {el_id!r} on branch from fork {fork_id!r}.")

    outs = el.get("outgoing") or []
    if len(outs) == 0:
        return ("end", None)

    if len(outs) == 1:
        return _fork_branch_correlation_outcome(bpmn, outs[0], fork_id, visiting_next)

    if typ == "exclusiveGateway":
        sub_outcomes: list[tuple[str, str | None]] = []
        for _fid, tgt, _cond in resolve_outgoing_flows(bpmn, el_id):
            sub_outcomes.append(_fork_branch_correlation_outcome(bpmn, tgt, fork_id, visiting_next))
        return _merge_fork_branch_correlation_outcomes(sub_outcomes, fork_id)

    raise ValueError(
        f"Parallel branch from fork {fork_id!r} has multiple outgoing at {el_id!r} "
        f"({typ}); only exclusiveGateway may split before reconverging to one join."
    )


def join_gateway_for_parallel_fork(bpmn: dict[str, Any], fork_id: str) -> str | None:
    """
    If every fork outgoing branch reaches the same parallel join, return that join id.
    Branches may contain multiple tasks, intermediate single-out nodes, and exclusive
    gateways provided all exclusive paths reach the same join. If every branch ends at
    endEvent before any join, return None (fork-only). Raises ValueError for mixed end/join,
    different joins, nested forks, or ambiguous topology.
    """
    flows = resolve_outgoing_flows(bpmn, fork_id)
    if not flows:
        return None
    outcomes: list[tuple[str, str | None]] = []
    for _flow_id, target_id, _ in flows:
        outcomes.append(_fork_branch_correlation_outcome(bpmn, target_id, fork_id, set()))
    ends = [o for o in outcomes if o[0] == "end"]
    joins = [o[1] for o in outcomes if o[0] == "join" and o[1]]
    if len(ends) == len(outcomes):
        return None
    if len(joins) == len(outcomes):
        jset = set(joins)
        if len(jset) != 1:
            raise ValueError(f"Fork {fork_id!r} branches reach different joins: {sorted(jset)!r}.")
        return joins[0]
    raise ValueError(
        f"Fork {fork_id!r} has mixed branches (some end before join, some reach join); "
        "not supported."
    )


def validate_parallel_fork_join_correlation(bpmn: dict[str, Any]) -> list[str]:
    """
    Save-time: each parallel fork must either fork-only (all branches to end) or correlate
    to a single join per PAR-009 rules. Returns human-readable errors.
    """
    errors: list[str] = []
    elements = bpmn.get("elements") or {}
    for eid in sorted(elements.keys()):
        if not is_parallel_fork_gateway(bpmn, eid):
            continue
        try:
            join_gateway_for_parallel_fork(bpmn, eid)
        except ValueError as ex:
            errors.append(f"parallelForkJoin '{eid}': {ex}")
    return errors


def first_executable_after_join(
    bpmn: dict[str, Any],
    join_element_id: str,
    state: Any,
    bindings: dict[str, Any],
    flow_selector: FlowSelector | None,
) -> str | None:
    """First bound executable task after join gateway (single outgoing), or None / end."""
    el = (bpmn.get("elements") or {}).get(join_element_id) or {}
    outs = el.get("outgoing") or []
    if len(outs) != 1:
        return None
    resolved = traverse_until_executable(
        bpmn,
        outs[0],
        seen={join_element_id},
        state=state,
        bindings=bindings,
        flow_selector=flow_selector,
    )
    if resolved == "Workflow.END" or not resolved:
        return None
    return resolved


def is_parallel_fork_gateway(bpmn: dict[str, Any], element_id: str) -> bool:
    """True if element is parallelGateway with exactly one incoming and at least two outgoing (fork)."""
    el = (bpmn.get("elements") or {}).get(element_id) or {}
    if el.get("type") != "parallelGateway":
        return False
    inc = el.get("incoming") or []
    out = el.get("outgoing") or []
    return len(inc) == 1 and len(out) >= 2


def parallel_join_sentinel(join_element_id: str) -> str:
    return f"Workflow.PARALLEL_JOIN:{join_element_id}"


def parse_parallel_join_sentinel(resolved: str | None) -> str | None:
    """If resolved is a parallel-join sentinel, return join element id; else None."""
    if not resolved or not isinstance(resolved, str):
        return None
    prefix = "Workflow.PARALLEL_JOIN:"
    if resolved.startswith(prefix):
        return resolved[len(prefix) :].strip() or None
    return None


def parallel_fork_branch_entries(
    bpmn: dict[str, Any],
    fork_id: str,
    state: Any,
    bindings: dict[str, Any],
    flow_selector: FlowSelector | None,
) -> list[tuple[str, str | None, str | None]]:
    """
    For a parallel fork gateway, resolve each outgoing branch in BPMN outgoing-flow order.

    Returns list of (branch_id, first_task_id, join_id_if_blocked):
    - branch_id is "{fork_id}:{flow_id}"
    - first_task_id is the first executable task on that branch, or None if the branch
      ends immediately (endEvent) or resolves to nothing
    - join_id_if_blocked is set when the first hop from the fork is a parallel join
      (no task on that branch before the join)
    """
    flows = resolve_outgoing_flows(bpmn, fork_id)
    out: list[tuple[str, str | None, str | None]] = []
    for flow_id, target_id, _ in flows:
        branch_id = f"{fork_id}:{flow_id}"
        seen: set[str] = {fork_id}
        resolved = traverse_until_executable(
            bpmn,
            target_id,
            seen,
            state=state,
            bindings=bindings,
            flow_selector=flow_selector,
        )
        jid = parse_parallel_join_sentinel(resolved)
        if jid:
            out.append((branch_id, None, jid))
        elif resolved == "Workflow.END" or not resolved:
            out.append((branch_id, None, None))
        else:
            out.append((branch_id, resolved, None))
    return out


def resolve_position_after_service_task(  # noqa: C901
    bpmn: dict[str, Any],
    completed_task_id: str,
    state: Any,
    bindings: dict[str, Any],
    flow_selector: FlowSelector | None,
) -> tuple[str, Any]:
    """
    After a bound service task completes, determine the next execution position(s).

    Returns a discriminator tuple:
    - ("end", None) — branch complete (endEvent or no successor task)
    - ("task", next_task_id) — single next executable task
    - ("fork", (fork_id, list[(branch_id, task_id|None)])) — parallel split; only branches
      with non-None task_id get tokens; branch_id stable for resume
    - ("join", join_element_id) — next hop is parallel join (synchronized when fork-registered)
    - ("subprocess_internal_end", sp_id) — internal endEvent consumed token; engine may exit subprocess
    """
    flows = resolve_outgoing_flows(bpmn, completed_task_id)
    if not flows:
        return ("end", None)
    if len(flows) > 1:
        if flow_selector is None:
            return ("end", None)
        chosen = flow_selector(bpmn, completed_task_id, flows, state, bindings)
        if not chosen:
            return ("end", None)
        resolved = traverse_until_executable(
            bpmn,
            chosen,
            seen={completed_task_id},
            state=state,
            bindings=bindings,
            flow_selector=flow_selector,
        )
        jid = parse_parallel_join_sentinel(resolved)
        if jid:
            return ("join", jid)
        if resolved == "Workflow.END" or not resolved:
            spc = subprocess_container_after_task_completion_path(
                bpmn, chosen, {completed_task_id}
            )
            if spc:
                return ("subprocess_internal_end", spc)
            return ("end", None)
        return ("task", resolved)

    _, target_id, _ = flows[0]
    if is_parallel_fork_gateway(bpmn, target_id):
        entries = parallel_fork_branch_entries(bpmn, target_id, state, bindings, flow_selector)
        task_pairs = [(bid, tid) for bid, tid, _j in entries if tid is not None]
        return ("fork", (target_id, task_pairs))

    sp_exit = _subprocess_id_when_task_exits_via_internal_end(
        bpmn, completed_task_id, target_id
    )
    if sp_exit:
        return ("subprocess_internal_end", sp_exit)

    seen = {completed_task_id}
    resolved = traverse_until_executable(
        bpmn,
        target_id,
        seen,
        state=state,
        bindings=bindings,
        flow_selector=flow_selector,
    )
    jid = parse_parallel_join_sentinel(resolved)
    if jid:
        return ("join", jid)
    if resolved == "Workflow.END" or not resolved:
        spc = subprocess_container_after_task_completion_path(bpmn, target_id, seen)
        if spc:
            return ("subprocess_internal_end", spc)
        return ("end", None)
    return ("task", resolved)


def next_step_after_task_completion(
    bpmn: dict[str, Any],
    completed_task_id: str,
    state: Any,
    bindings: dict[str, Any],
    flow_selector: FlowSelector | None,
) -> str | None:
    """
    BPMN element id to run after completed_task_id finishes (for pause/resume next_step).
    For a fork successor, returns the first branch's first executable task in flow order.
    """
    kind, data = resolve_position_after_service_task(
        bpmn, completed_task_id, state, bindings, flow_selector
    )
    if kind == "task":
        return data if isinstance(data, str) else None
    if kind == "fork" and data:
        _fork_id, pairs = data
        for _bid, tid in pairs:
            if tid:
                return tid
    return None


def get_next_step_expression(bpmn: dict[str, Any], element_id: str) -> str:
    element = bpmn.get("elements", {}).get(element_id) or {}
    outgoing = element.get("outgoing") or []
    if not outgoing:
        return "Workflow.END"
    if len(outgoing) > 1:
        return "Workflow.NEXT"
    target = outgoing[0]
    resolved = _follow_single_path(bpmn, target, seen={element_id})
    if resolved == "Workflow.END":
        return "Workflow.END"
    if resolved:
        return repr(resolved)
    return "Workflow.NEXT"


def get_first_task_id(bpmn: dict[str, Any]) -> str | None:
    """Return the first executable service task id reachable from a start event, or None."""
    elements = bpmn.get("elements") or {}
    for eid in bpmn.get("ordered_element_ids") or []:
        el = elements.get(eid)
        if el and el.get("type") == "startEvent":
            resolved = _follow_single_path(bpmn, eid, set())
            if resolved and resolved != "Workflow.END":
                return resolved
            break
    return None


def get_next_task_id(bpmn: dict[str, Any], current_task_id: str) -> str | None:
    """
    Return the next executable service task id after current_task_id by following sequence flow.
    Returns None when the next element is an end event or there is no single path.
    """
    elements = bpmn.get("elements") or {}
    element = elements.get(current_task_id)
    if not element:
        return None
    outgoing = element.get("outgoing") or []
    if not outgoing:
        return None
    if len(outgoing) > 1:
        return None
    resolved = _follow_single_path(bpmn, outgoing[0], seen={current_task_id})
    if resolved == "Workflow.END" or not resolved:
        return None
    return resolved


def get_selected_element_details(
    context: dict[str, Any], selected_element_id: str = ""
) -> dict[str, Any] | None:
    if not selected_element_id:
        return None
    element = context.get("bpmn", {}).get("elements", {}).get(selected_element_id)
    if not element:
        return None
    bindings = context.get("bindings", {}).get("serviceTasks", {})
    binding = bindings.get(selected_element_id) if isinstance(bindings, dict) else None
    return {
        **element,
        "binding": binding or {},
    }


def get_workflow_context(
    workflow_id: str,
    *,
    bpmn_xml_override: str | None = None,
    bindings_yaml_override: str | None = None,
    selected_element_id: str = "",
) -> dict[str, Any]:
    from .workflow_registry import REPO_ROOT, workflow_registry

    workflow = workflow_registry.get(workflow_id)
    if not workflow:
        raise ValueError(f"Workflow '{workflow_id}' not found")

    metadata = workflow["metadata"]
    workflow_path = REPO_ROOT / "workflows" / workflow_id
    assets_path = getattr(metadata, "current_version_path", None) or workflow_path

    metadata_text = _read_text(workflow_path / "metadata.yaml")
    documentation_text = _read_text(workflow_path / "documentation.md")
    user_story_text = _read_text(workflow_path / "USER_STORY.md")
    workflow_py = _read_text(workflow_path / "workflow.py")

    bpmn_xml = (
        bpmn_xml_override
        if bpmn_xml_override is not None
        else _read_text(assets_path / "workflow.bpmn")
    )
    bindings_yaml = (
        bindings_yaml_override
        if bindings_yaml_override is not None
        else _read_text(assets_path / "bpmn-bindings.yaml")
    )

    code_info = parse_workflow_python(workflow_py)
    executor_path = ""
    if code_info.get("workflow_class_name"):
        executor_path = f"workflows.{workflow_id}.workflow.{code_info['workflow_class_name']}"

    bindings = normalize_bindings(
        _safe_load_yaml(bindings_yaml),
        workflow_id=workflow_id,
        executor=executor_path,
    )
    bpmn = parse_bpmn_xml(bpmn_xml)

    context = {
        "workflow": {
            "id": metadata.id,
            "name": metadata.name,
            "description": metadata.description,
            "category": metadata.category,
            "estimated_duration": metadata.estimated_duration,
            "workflow_path": str(workflow_path),
            "assets_path": str(assets_path),
        },
        "files": {
            "metadata_path": str(workflow_path / "metadata.yaml"),
            "workflow_py_path": str(workflow_path / "workflow.py"),
            "bpmn_path": str(assets_path / "workflow.bpmn"),
            "bindings_path": str(assets_path / "bpmn-bindings.yaml"),
        },
        "metadata_yaml": _safe_load_yaml(metadata_text),
        "documentation": documentation_text,
        "user_story": user_story_text,
        "workflow_py": workflow_py,
        "code": code_info,
        "bpmn_xml": bpmn_xml,
        "bpmn": bpmn,
        "bindings_yaml": bindings_yaml,
        "bindings": bindings,
    }
    context["selected_element"] = get_selected_element_details(context, selected_element_id)
    return context


def _reachable_from_start(bpmn: dict[str, Any]) -> set[str]:
    """BFS from parent-scope start only; stays in elements without subprocess_container."""
    elements = bpmn.get("elements") or {}
    starts = [
        eid
        for eid, el in elements.items()
        if el.get("type") == "startEvent" and not el.get("subprocess_container")
    ]
    if not starts:
        return set()
    reachable: set[str] = set()
    stack = [starts[0]]
    while stack:
        nid = stack.pop()
        if nid in reachable:
            continue
        el = elements.get(nid) or {}
        if el.get("subprocess_container"):
            continue
        reachable.add(nid)
        for target in el.get("outgoing") or []:
            if target not in elements:
                continue
            tel = elements.get(target) or {}
            if tel.get("subprocess_container"):
                continue
            if target not in reachable:
                stack.append(target)
    return reachable


def _reachable_inside_subprocess(bpmn: dict[str, Any], sp_id: str) -> set[str]:
    """Nodes inside embedded subprocess sp_id reachable from its single internal start."""
    elements = bpmn.get("elements") or {}
    inside = {
        eid
        for eid, el in elements.items()
        if el.get("subprocess_container") == sp_id
    }
    starts = [eid for eid in inside if (elements.get(eid) or {}).get("type") == "startEvent"]
    if not starts:
        return set()
    reachable: set[str] = set()
    stack = [starts[0]]
    while stack:
        nid = stack.pop()
        if nid in reachable or nid not in inside:
            continue
        reachable.add(nid)
        el = elements.get(nid) or {}
        for target in el.get("outgoing") or []:
            if target in inside and target not in reachable:
                stack.append(target)
    return reachable


def _reachable_from_boundary_targets(bpmn: dict[str, Any]) -> set[str]:
    """Nodes on paths starting at timer/error boundary outgoing targets (PAR-014)."""
    elements = bpmn.get("elements") or {}
    seeds: list[str] = []
    for bucket in (bpmn.get("boundary_by_task") or {}).values():
        if not isinstance(bucket, dict):
            continue
        for kind in ("timer", "error"):
            spec = bucket.get(kind)
            if not isinstance(spec, dict):
                continue
            tgt = (spec.get("target_element_id") or "").strip()
            if tgt in elements:
                seeds.append(tgt)
    seen: set[str] = set()
    stack = list(seeds)
    while stack:
        nid = stack.pop()
        if nid in seen:
            continue
        seen.add(nid)
        el = elements.get(nid) or {}
        for target in el.get("outgoing") or []:
            if target in elements and target not in seen:
                stack.append(target)
    return seen


def validate_bpmn_graph_structure(bpmn: dict[str, Any]) -> list[str]:
    """
    Validate start/end, reachability of service/user tasks, and dead-end executable nodes.
    Parent process and each embedded subprocess are checked separately (PAR-016).
    """
    errors: list[str] = []
    elements = bpmn.get("elements") or {}
    if not elements:
        return errors
    parent_starts = [
        eid
        for eid, el in elements.items()
        if el.get("type") == "startEvent" and not el.get("subprocess_container")
    ]
    ends = [eid for eid, el in elements.items() if el.get("type") == "endEvent"]
    if len(parent_starts) != 1:
        errors.append(
            f"Expected exactly one startEvent in process scope, found {len(parent_starts)}. "
            "Suggestion: ensure a single well-formed start (internal subprocess starts do not count)."
        )
    if not ends:
        errors.append("No endEvent found. Suggestion: add an end event to close the process.")
    reachable = _reachable_from_start(bpmn) | _reachable_from_boundary_targets(bpmn)
    for eid, el in elements.items():
        if el.get("subprocess_container"):
            continue
        t = el.get("type")
        if t in ("serviceTask", "userTask") and eid not in reachable:
            errors.append(
                f"Unreachable node '{eid}' ({t}). Suggestion: connect it from the start event via sequence flows."
            )
    dead_end_types = ("serviceTask", "userTask", "exclusiveGateway", "parallelGateway")
    for eid, el in elements.items():
        if el.get("subprocess_container"):
            continue
        t = el.get("type")
        if t in dead_end_types and not (el.get("outgoing") or []):
            errors.append(
                f"Dead-end '{eid}' ({t}): no outgoing flow. Suggestion: connect to the next task or end event."
            )
    for eid in ends:
        el = elements.get(eid) or {}
        if el.get("subprocess_container"):
            continue
        if eid not in reachable and parent_starts:
            errors.append(
                f"endEvent '{eid}' is not reachable from start. Suggestion: add sequence flows so all ends are reachable."
            )
    for sp_id in bpmn.get("subprocess_root_ids") or []:
        if (elements.get(sp_id) or {}).get("type") != "subProcess":
            continue
        r_in = _reachable_inside_subprocess(bpmn, sp_id)
        inside_tasks = [
            eid
            for eid, el in elements.items()
            if el.get("subprocess_container") == sp_id
            and el.get("type") in ("serviceTask", "userTask")
        ]
        for eid in inside_tasks:
            if eid not in r_in:
                errors.append(
                    f"Subprocess '{sp_id}': internal node '{eid}' is not reachable from the "
                    "internal start event."
                )
        for eid, el in elements.items():
            if el.get("subprocess_container") != sp_id:
                continue
            if el.get("type") != "endEvent":
                continue
            if eid not in r_in:
                errors.append(
                    f"Subprocess '{sp_id}': internal endEvent '{eid}' is not reachable from the internal start."
                )
        for eid, el in elements.items():
            if el.get("subprocess_container") != sp_id:
                continue
            t = el.get("type")
            if t in dead_end_types and not (el.get("outgoing") or []):
                errors.append(
                    f"Subprocess '{sp_id}': dead-end '{eid}' ({t}): no outgoing flow."
                )
    return errors


def validate_parallel_gateway_topology(bpmn: dict[str, Any]) -> list[str]:
    """
    Save-time rules for parallelGateway topology (allowed shapes for future parallel runtime).

    Valid: **fork** — exactly one incoming and at least two outgoing.
    Valid: **join** — at least two incoming and exactly one outgoing.

    All other degree patterns are rejected with gateway id, shape hint, and fix suggestion.
    """
    errors: list[str] = []
    elements = bpmn.get("elements") or {}
    for eid, el in elements.items():
        if el.get("type") != "parallelGateway":
            continue
        inc = el.get("incoming") or []
        out = el.get("outgoing") or []
        ni, no = len(inc), len(out)
        if ni == 0:
            errors.append(
                f"parallelGateway '{eid}' (shape=missing_incoming): no incoming sequence flow. "
                "Suggestion: connect one incoming flow for a fork, or two or more for a join."
            )
        elif no == 0:
            errors.append(
                f"parallelGateway '{eid}' (shape=missing_outgoing): no outgoing sequence flow. "
                "Suggestion: fork needs at least two outgoing branches; join needs exactly one."
            )
        elif ni > 1 and no > 1:
            errors.append(
                f"parallelGateway '{eid}' (shape=ambiguous_join_and_fork): multiple incoming and multiple outgoing. "
                "Suggestion: use separate gateways — one join (2+ in, 1 out) then one fork (1 in, 2+ out), or the reverse."
            )
        elif ni == 1 and no == 1:
            errors.append(
                f"parallelGateway '{eid}' (shape=pass_through): one incoming and one outgoing is not allowed. "
                "Suggestion: model a fork (1 in, 2+ out), a join (2+ in, 1 out), or remove this gateway."
            )
        elif ni == 1 and no >= 2:
            continue  # valid fork
        elif ni >= 2 and no == 1:
            continue  # valid join
        # ni/no are list lengths (non-negative); branches above reject every pair except fork/join.
    return errors


def validate_service_task_bindings_strict(
    bpmn: dict[str, Any], bindings: dict[str, Any]
) -> list[str]:
    """Every serviceTask must have a binding (save-time / runtime alignment)."""
    elements = bpmn.get("elements") or {}
    service_ids = {eid for eid, el in elements.items() if el.get("type") == "serviceTask"}
    bound = set((bindings.get("serviceTasks") or {}).keys())
    errors: list[str] = []
    for sid in sorted(service_ids - bound):
        errors.append(
            f"Service task '{sid}' has no binding in bpmn-bindings.yaml. "
            "Suggestion: add a serviceTasks entry with handler name."
        )
    return errors


def validate_bpmn_boundary_events(bpmn: dict[str, Any]) -> list[str]:
    """PAR-014: interrupting timer/error boundary events only; single outgoing."""
    errors: list[str] = []
    elements = bpmn.get("elements") or {}

    for raw in bpmn.get("boundary_unsupported") or []:
        if not isinstance(raw, dict):
            continue
        bid = raw.get("boundary_id", "?")
        errors.append(
            f"Boundary '{bid}': unsupported event type (only timer and error boundaries are allowed in v1). "
            "Suggestion: remove or replace with boundaryTimerEvent or boundaryErrorEvent."
        )

    for pair in bpmn.get("boundary_duplicate_timers") or []:
        errors.append(
            f"Task '{pair[0]}': multiple timer boundaries are not allowed (second: '{pair[1]}'). "
            "Suggestion: use at most one interrupting timer per task."
        )
    for pair in bpmn.get("boundary_duplicate_errors") or []:
        errors.append(
            f"Task '{pair[0]}': multiple error boundaries are not allowed (second: '{pair[1]}'). "
            "Suggestion: use at most one interrupting error boundary per task."
        )

    for task_id, bucket in (bpmn.get("boundary_by_task") or {}).items():
        if not isinstance(bucket, dict):
            continue
        for kind in ("timer", "error"):
            spec = bucket.get(kind)
            if not isinstance(spec, dict):
                continue
            bid = spec.get("boundary_id", "?")
            if not spec.get("interrupting", True):
                errors.append(
                    f"Boundary '{bid}': non-interrupting boundaries are not supported in v1 "
                    "(cancelActivity must be true or omitted). Suggestion: use interrupting boundary only."
                )
            el = elements.get(task_id) or {}
            et = el.get("type") or ""
            if task_id not in elements:
                errors.append(
                    f"Boundary '{bid}': attachedToRef '{task_id}' is not a known flow node. "
                    "Suggestion: attach to a serviceTask, userTask, task, or scriptTask."
                )
            elif et not in _BOUNDARY_ATTACHABLE_TYPES:
                errors.append(
                    f"Boundary '{bid}': attached task '{task_id}' has type '{et}' — "
                    "only serviceTask, userTask, task, and scriptTask may have boundaries in v1."
                )
            nout = spec.get("outgoing_count")
            if nout != 1:
                errors.append(
                    f"Boundary '{bid}': must have exactly one outgoing sequence flow (found {nout}). "
                    "Suggestion: connect the boundary to a single alternate path."
                )
            tgt = (spec.get("target_element_id") or "").strip()
            if not tgt:
                errors.append(
                    f"Boundary '{bid}': no outgoing target. Suggestion: connect one sequence flow."
                )
            elif tgt not in elements:
                errors.append(
                    f"Boundary '{bid}': outgoing target '{tgt}' is missing from the diagram."
                )
            if kind == "timer":
                dur = spec.get("duration_iso") or ""
                if not dur.strip():
                    errors.append(
                        f"Boundary '{bid}': timer boundary requires bpmn:timeDuration (e.g. PT5M). "
                        "Suggestion: add a timeDuration inside timerEventDefinition."
                    )
                elif iso8601_duration_to_seconds(dur) is None:
                    errors.append(
                        f"Boundary '{bid}': could not parse timeDuration {dur!r}. "
                        "Suggestion: use ISO-8601 duration such as PT1H, PT90S, P1D."
                    )
            if tgt and tgt in elements:
                seen: set[str] = set()
                res = traverse_until_executable(
                    bpmn, tgt, seen, state=None, bindings=None, flow_selector=None
                )
                if res is None:
                    errors.append(
                        f"Boundary '{bid}': alternate path from '{tgt}' does not reach a single "
                        "next executable task (ambiguous gateway or dead end). Suggestion: connect "
                        "to a clear path to the next task or endEvent."
                    )
    return errors


def validate_bpmn_for_save(
    bpmn: dict[str, Any], bindings: dict[str, Any] | None = None
) -> list[str]:
    """All structural validations that should block Workflow Studio save."""
    errors: list[str] = []
    errors.extend(validate_bpmn_graph_structure(bpmn))
    errors.extend(validate_exclusive_gateway_semantics(bpmn))
    errors.extend(validate_parallel_gateway_topology(bpmn))
    errors.extend(validate_parallel_fork_join_correlation(bpmn))
    errors.extend(validate_bpmn_boundary_events(bpmn))
    errors.extend(validate_bpmn_intermediate_catch_events(bpmn))
    errors.extend(validate_bpmn_embedded_subprocesses(bpmn))
    if bindings is not None:
        errors.extend(validate_service_task_bindings_strict(bpmn, bindings))
    return errors


def validate_exclusive_gateway_semantics(bpmn: dict[str, Any]) -> list[str]:
    """
    Validate exclusive gateway structure: multiple outgoing must have conditions or default;
    default flow must exist; no invalid condition syntax. Returns list of error strings.
    """
    errors: list[str] = []
    elements = bpmn.get("elements") or {}
    flows = bpmn.get("sequence_flows") or {}
    for eid, el in elements.items():
        if el.get("type") != "exclusiveGateway":
            continue
        outgoing_flow_ids = el.get("outgoing_flow_ids") or []
        outgoing = el.get("outgoing") or []
        if len(outgoing) <= 1:
            continue
        has_condition = False
        for flow_id in outgoing_flow_ids:
            cond = (flows.get(flow_id) or {}).get("condition", "") or ""
            if cond and cond.strip():
                has_condition = True
                break
        default_flow_id = el.get("default_flow_id")
        if not has_condition and not default_flow_id:
            errors.append(
                f"Gateway '{eid}': multiple outgoing flows but no conditions and no default flow. "
                "Suggestion: add condition expressions to flows (e.g. state.attr == value) or set a default flow."
            )
        if default_flow_id and default_flow_id not in outgoing_flow_ids:
            errors.append(
                f"Gateway '{eid}' flow '{default_flow_id}': default_flow_id is not in outgoing flows. "
                f"Outgoing: {outgoing_flow_ids}. Suggestion: set default to one of the listed flow ids."
            )
        for flow_id in outgoing_flow_ids:
            cond = (flows.get(flow_id) or {}).get("condition", "") or ""
            if not cond.strip():
                continue
            text = cond.strip()
            if not is_supported_condition_syntax(text):
                errors.append(
                    f"Gateway '{eid}' flow '{flow_id}': unparsable condition. "
                    f"Condition: {text!r}. "
                    "Suggestion: use state.<attr> op value or state.<attr> in [...], with <attr> a single identifier (no dots)."
                )
    return errors


def validate_bpmn_bindings_context(context: dict[str, Any]) -> dict[str, Any]:
    bindings = normalize_bindings(
        context.get("bindings") or {},
        workflow_id=context["workflow"]["id"],
    )
    bpmn = context.get("bpmn") or {}
    code = context.get("code") or {}

    elements = bpmn.get("elements") or {}
    service_task_ids = {eid for eid, el in elements.items() if el.get("type") == "serviceTask"}
    user_task_ids = {eid for eid, el in elements.items() if el.get("type") == "userTask"}
    bound_task_ids = set((bindings.get("serviceTasks") or {}).keys())
    handler_names = set(code.get("handler_names") or [])

    errors: list[str] = []
    warnings: list[str] = []
    suggestions: list[str] = []

    errors.extend(validate_exclusive_gateway_semantics(bpmn))
    errors.extend(validate_bpmn_graph_structure(bpmn))
    errors.extend(validate_parallel_gateway_topology(bpmn))
    errors.extend(validate_service_task_bindings_strict(bpmn, bindings))

    missing_bindings = sorted(service_task_ids - bound_task_ids)
    if missing_bindings:
        suggestions.extend(
            [f"Add binding for service task '{task_id}'" for task_id in missing_bindings]
        )

    # Bindings for userTasks are valid (handler runs when human task completes); only warn for other orphans
    orphan_bindings = sorted(bound_task_ids - service_task_ids - user_task_ids)
    if orphan_bindings:
        warnings.append(
            "Bindings that do not match a BPMN service or user task: " + ", ".join(orphan_bindings)
        )

    for task_id, binding in (bindings.get("serviceTasks") or {}).items():
        handler = (binding or {}).get("handler", "").strip()
        if not handler:
            errors.append(f"Binding '{task_id}' is missing a handler name")
            continue
        if handler_names and handler not in handler_names:
            warnings.append(
                f"Binding '{task_id}' points to missing workflow.py handler '{handler}'"
            )
            suggestions.append(f"Generate or add handler '{handler}' in workflow.py")

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "suggestions": suggestions,
        "service_task_count": len(service_task_ids),
        "binding_count": len(bound_task_ids),
        "handler_count": len(handler_names),
    }
