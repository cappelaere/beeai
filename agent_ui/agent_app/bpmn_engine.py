"""
BPMN-driven workflow execution engine.

Runs workflows by traversing the BPMN diagram and invoking handler methods
bound in bpmn-bindings.yaml. The diagram is the source of truth for execution order.

Engine state is separate from workflow business state: it lives in state.__dict__["_bpmn_engine_state"]
and in progress_data["engine_state"] for resume. See BPMN_ENGINE_REVIEW.md for persistence expectations.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any

from agent_app.bpmn_conditions import (
    evaluate_condition as _eval_parsed_condition,
)
from agent_app.bpmn_conditions import (
    parse_condition,
)
from agent_app.bpmn_parallel import (
    PendingJoinInfo,
    append_token,
    clear_pending_join,
    get_pending_join,
    is_join_satisfied,
    mark_branch_arrived_at_join,
    register_pending_join,
    remove_token_at_index,
    remove_tokens_by_branch_ids,
    replace_token_at_index,
    replace_token_at_index_with_tokens,
)
from agent_app.task_service import (
    BpmnIntermediateWaitError,
    BpmnModeledBoundaryError,
    BpmnRetryableTaskError,
    TaskPendingError,
)
from agent_app.workflow_context import (
    element_subprocess_container,
    first_executable_after_join,
    get_error_boundary_for_task,
    get_first_task_id,
    get_timer_boundary_for_task,
    get_workflow_context,
    intermediate_catch_outgoing_target,
    is_intermediate_message_catch,
    is_intermediate_timer_catch,
    iso8601_duration_to_seconds,
    join_gateway_for_parallel_fork,
    next_step_after_task_completion,
    normalize_bindings,
    parse_parallel_join_sentinel,
    resolve_outgoing_flows,
    resolve_position_after_service_task,
    subprocess_parent_continuation_target,
    traverse_until_executable,
)

logger = logging.getLogger(__name__)

BPMN_ENGINE_VERSION = "2"


def _normalize_optional_str_id(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        s = value.strip()
        return s if s else None
    return str(value).strip() or None


def _normalize_pending_joins(raw: Any) -> dict[str, dict[str, Any]]:
    """Coerce pending_joins to join_id -> PendingJoinInfo-shaped dicts; skip bad entries."""
    if not isinstance(raw, dict):
        return {}
    result: dict[str, dict[str, Any]] = {}
    for key, val in raw.items():
        join_id = str(key).strip() if key is not None else ""
        if not join_id:
            continue
        if not isinstance(val, dict):
            continue
        merged = dict(val)
        if not (merged.get("join_element_id") or "").strip():
            merged["join_element_id"] = join_id
        try:
            result[join_id] = PendingJoinInfo.from_dict(merged).to_dict()
        except (TypeError, ValueError):
            result[join_id] = PendingJoinInfo(
                fork_id=str(merged.get("fork_id") or ""),
                join_element_id=join_id,
                expected_branch_ids=[],
                arrived_branch_ids=[],
            ).to_dict()
    return result


def _normalize_active_tokens(
    raw_tokens: Any, fallback_current_node_ids: list[Any]
) -> list[dict[str, Any]]:
    tokens = raw_tokens if isinstance(raw_tokens, list) else []
    norm_tokens: list[dict[str, Any]] = []
    for token in tokens:
        if isinstance(token, dict):
            norm_tokens.append(
                {
                    "current_element_id": _normalize_optional_str_id(
                        token.get("current_element_id")
                    ),
                    "branch_id": _normalize_optional_str_id(token.get("branch_id")),
                }
            )
        else:
            norm_tokens.append({"current_element_id": None, "branch_id": None})
    if not norm_tokens or all(
        t["current_element_id"] is None and t["branch_id"] is None for t in norm_tokens
    ):
        cur = (fallback_current_node_ids or [None])[0]
        cur_n = _normalize_optional_str_id(cur) if cur is not None else None
        return [asdict(BpmnToken(current_element_id=cur_n))]
    return norm_tokens


def _normalize_int_map(raw_map: Any) -> dict[str, int]:
    if not isinstance(raw_map, dict):
        return {}
    clean: dict[str, int] = {}
    for k, v in raw_map.items():
        try:
            clean[str(k)] = int(v)
        except (TypeError, ValueError):
            continue
    return clean


def _normalize_float_map(raw_map: Any) -> dict[str, float]:
    if not isinstance(raw_map, dict):
        return {}
    return {str(k): float(v) for k, v in raw_map.items() if isinstance(v, (int, float))}


def _normalize_optional_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _normalize_dict_list(value: Any, *, limit: int | None = None) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    items = value[-limit:] if isinstance(limit, int) and limit > 0 else value
    return [dict(x) for x in items if isinstance(x, dict)]


def _normalize_subprocess_stack(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    clean_ss: list[dict[str, Any]] = []
    for x in value[:20]:
        if not isinstance(x, dict):
            continue
        clean_ss.append(
            {
                "subprocess_id": str(x.get("subprocess_id") or "").strip(),
                "name": str(x.get("name") or "").strip(),
                "entered_at": str(x.get("entered_at") or "").strip(),
                "parent_branch_id": _normalize_optional_str_id(x.get("parent_branch_id")),
            }
        )
    return [f for f in clean_ss if f.get("subprocess_id")]


def _normalize_satisfied_messages(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(x).strip() for x in value if isinstance(x, (str, int)) and str(x).strip()]


def normalize_engine_state(raw: dict[str, Any] | None) -> dict[str, Any]:
    """
    Normalize persisted or partial engine_state to the v2+ contract (single- and multi-token).
    Single place for backward compatibility with older progress payloads.
    See BPMN_ENGINE_REVIEW.md for the full normalized key set.
    """
    if not raw or not isinstance(raw, dict):
        return _make_engine_state()
    out = dict(raw)
    if out.get("engine_version") is None:
        out["engine_version"] = BPMN_ENGINE_VERSION
    for key in ("completed_node_ids", "current_node_ids", "failed_node_ids"):
        v = out.get(key)
        out[key] = list(v) if isinstance(v, list) else []
    out["active_tokens"] = _normalize_active_tokens(
        out.get("active_tokens"), out.get("current_node_ids") or []
    )

    out["pending_joins"] = _normalize_pending_joins(out.get("pending_joins"))
    out["condition_failure_metadata"] = _normalize_optional_dict(
        out.get("condition_failure_metadata")
    )
    out["failed_node_id"] = _normalize_optional_str_id(out.get("failed_node_id"))
    out["failure_reason"] = _normalize_optional_str_id(out.get("failure_reason"))
    out["last_successful_node_id"] = _normalize_optional_str_id(out.get("last_successful_node_id"))
    out["task_retry_counts"] = _normalize_int_map(out.get("task_retry_counts"))
    out["last_retryable_error"] = (
        _normalize_optional_dict(out.get("last_retryable_error"))
        if isinstance(out.get("last_retryable_error"), dict)
        else None
    )
    out["task_entry_monotonic"] = _normalize_float_map(out.get("task_entry_monotonic"))
    out["boundary_transitions"] = _normalize_dict_list(out.get("boundary_transitions"))
    out["last_boundary_transition"] = (
        _normalize_optional_dict(out.get("last_boundary_transition"))
        if isinstance(out.get("last_boundary_transition"), dict)
        else None
    )
    out["bpmn_event_wait"] = _normalize_optional_dict(out.get("bpmn_event_wait"))
    out["satisfied_intermediate_messages"] = _normalize_satisfied_messages(
        out.get("satisfied_intermediate_messages")
    )
    out["intermediate_catch_transitions"] = _normalize_dict_list(
        out.get("intermediate_catch_transitions")
    )
    out["subprocess_stack"] = _normalize_subprocess_stack(out.get("subprocess_stack"))
    out["subprocess_transitions"] = _normalize_dict_list(
        out.get("subprocess_transitions"), limit=50
    )
    return out


def current_node_ids_for_progress(engine_state: dict[str, Any] | None) -> list[str]:
    """
    Active BPMN element ids for progress/UI (0..N). Uses active_tokens in order when present;
    otherwise engine_state current_node_ids. Aligns persisted progress with multi-branch state.
    """
    if not engine_state or not isinstance(engine_state, dict):
        return []
    tokens = engine_state.get("active_tokens")
    out: list[str] = []
    if isinstance(tokens, list):
        for t in tokens:
            if isinstance(t, dict):
                cid = t.get("current_element_id")
                if cid is not None and str(cid).strip():
                    out.append(str(cid).strip())
    if out:
        return out
    cur = engine_state.get("current_node_ids") or []
    if isinstance(cur, list):
        return [str(x).strip() for x in cur if x is not None and str(x).strip()]
    return []


class BpmnEngineError(ValueError):
    """Raised when the BPMN engine fails; carries state and failure details for progress."""

    def __init__(
        self,
        message: str,
        state: Any,
        failure_reason: str,
        failed_node_id: str | None = None,
        condition_failure_metadata: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.state = state
        self.failure_reason = failure_reason
        self.failed_node_id = failed_node_id
        self.condition_failure_metadata = condition_failure_metadata or {}


@dataclass(frozen=True)
class BpmnToken:
    """Single token: one current element. branch_id reserved for future parallel gateways."""

    current_element_id: str | None
    branch_id: str | None = None


@dataclass
class BpmnEngineStateSchema:
    """
    Typed schema aligned with normalize_engine_state() / _make_engine_state().
    Runtime value is a dict on state._bpmn_engine_state and progress_data['engine_state'].
    """

    engine_version: str
    active_tokens: list[dict[str, Any]]  # each: current_element_id, branch_id
    completed_node_ids: list[str]
    current_node_ids: list[str]
    failed_node_ids: list[str]
    pending_joins: dict[str, dict[str, Any]] = field(default_factory=dict)
    failed_node_id: str | None = None
    failure_reason: str | None = None
    last_successful_node_id: str | None = None
    condition_failure_metadata: dict[str, Any] = field(default_factory=dict)


def _make_engine_state(
    *,
    completed_node_ids: list[str] | None = None,
    current_node_ids: list[str] | None = None,
    failed_node_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Build v2 engine runtime state dict (normalized shape incl. pending_joins + failure slots)."""
    current = (current_node_ids or [None])[0]
    cur_n = _normalize_optional_str_id(current) if current is not None else None
    token = BpmnToken(current_element_id=cur_n)
    return {
        "engine_version": BPMN_ENGINE_VERSION,
        "active_tokens": [asdict(token)],
        "completed_node_ids": list(completed_node_ids or []),
        "current_node_ids": list(current_node_ids or []),
        "failed_node_ids": list(failed_node_ids or []),
        "pending_joins": {},
        "failed_node_id": None,
        "failure_reason": None,
        "last_successful_node_id": None,
        "condition_failure_metadata": {},
        "task_retry_counts": {},
        "last_retryable_error": None,
        "task_entry_monotonic": {},
        "boundary_transitions": [],
        "last_boundary_transition": None,
        "subprocess_stack": [],
        "subprocess_transitions": [],
    }


def _ensure_engine_state(
    state: Any,
    *,
    completed_node_ids: list[str] | None = None,
    current_node_id: str | None = None,
) -> dict[str, Any]:
    """
    Ensure state has _bpmn_engine_state (from resume or new). Returns the engine state dict.
    If state already has _bpmn_engine_state, use it and optionally merge in completed/current.
    """
    existing = getattr(state, "_bpmn_engine_state", None)
    if existing and isinstance(existing, dict):
        eng = normalize_engine_state(existing)
        if completed_node_ids is not None:
            eng["completed_node_ids"] = list(completed_node_ids)
        if current_node_id is not None:
            eng["current_node_ids"] = [current_node_id]
            if eng.get("active_tokens"):
                eng["active_tokens"] = [{"current_element_id": current_node_id, "branch_id": None}]
        state.__dict__["_bpmn_engine_state"] = eng
        return eng
    completed = list(completed_node_ids or [])
    current = [current_node_id] if current_node_id else []
    eng = _make_engine_state(
        completed_node_ids=completed,
        current_node_ids=current,
    )
    if hasattr(state, "__dict__"):
        state.__dict__["_bpmn_engine_state"] = eng
    return eng


def update_token_state(
    engine_state: dict[str, Any],
    completed_id: str,
    next_current_id: str | None,
    failed_id: str | None = None,
) -> None:
    """Update engine state after a task: append completed, set current, optionally set failed. Token shape matches BpmnToken."""
    if completed_id and completed_id not in engine_state.get("completed_node_ids", []):
        engine_state.setdefault("completed_node_ids", []).append(completed_id)
    engine_state["current_node_ids"] = [next_current_id] if next_current_id else []
    token = BpmnToken(current_element_id=next_current_id)
    engine_state["active_tokens"] = [asdict(token)]
    if failed_id:
        engine_state.setdefault("failed_node_ids", []).append(failed_id)


def _append_completed_node(engine_state: dict[str, Any], node_id: str | None) -> None:
    if not node_id:
        return
    c = engine_state.setdefault("completed_node_ids", [])
    if node_id not in c:
        c.append(node_id)


def _merge_parallel_join(
    engine_state: dict[str, Any],
    join_id: str,
    bpmn: dict[str, Any],
    state: Any,
    bindings: dict[str, Any],
    flow_selector: Any,
) -> None:
    """All branches arrived at join: remove waiters, clear pending_joins, one downstream token."""
    from agent_app.bpmn_parallel import ensure_active_tokens

    pj = get_pending_join(engine_state, join_id)
    if not pj:
        return
    expected = set(pj.get("expected_branch_ids") or [])
    remove_tokens_by_branch_ids(engine_state, expected)
    toks = ensure_active_tokens(engine_state)
    jid = str(join_id).strip()
    engine_state["active_tokens"] = [
        t
        for t in toks
        if isinstance(t, dict) and str(t.get("current_element_id") or "").strip() != jid
    ]
    clear_pending_join(engine_state, join_id)
    _append_completed_node(engine_state, join_id)
    downstream = first_executable_after_join(bpmn, join_id, state, bindings, flow_selector)
    if downstream:
        append_token(engine_state, downstream, None)


def _sync_current_node_ids_from_tokens(engine_state: dict[str, Any]) -> None:
    toks = engine_state.get("active_tokens") or []
    engine_state["current_node_ids"] = [
        str(t["current_element_id"]).strip()
        for t in toks
        if isinstance(t, dict) and t.get("current_element_id")
    ]


_BPMN_BOUND_TASK_TYPES = frozenset({"serviceTask", "userTask", "task", "scriptTask"})


def _pick_token_for_execution(
    engine_state: dict[str, Any],
    bpmn: dict[str, Any],
    service_tasks: dict[str, Any],
) -> tuple[int | None, str | None]:
    """
    Return (token_index, None) for the next bound task to run (list order).
    If an earlier token sits on an executable BPMN task type without a binding,
    return (index, "missing_binding") so the engine can raise before no_runnable.
    """
    elements = bpmn.get("elements") or {}
    for i, t in enumerate(engine_state.get("active_tokens") or []):
        if not isinstance(t, dict):
            continue
        cid = t.get("current_element_id")
        if not cid or not str(cid).strip():
            continue
        eid = str(cid).strip()
        if eid in service_tasks:
            return i, None
        el = elements.get(eid) or {}
        if el.get("type") in _BPMN_BOUND_TASK_TYPES:
            return i, "missing_binding"
    for i, t in enumerate(engine_state.get("active_tokens") or []):
        if not isinstance(t, dict):
            continue
        cid = t.get("current_element_id")
        if not cid or not str(cid).strip():
            continue
        eid = str(cid).strip()
        if is_intermediate_timer_catch(bpmn, eid) or is_intermediate_message_catch(bpmn, eid):
            return i, "intermediate_catch"
    return None, "no_runnable_token"


def _init_engine_state_for_bpmn_run(
    state: Any,
    bpmn: dict[str, Any],
    start_from_task_id: str | None,
) -> dict[str, Any] | None:
    """
    Fresh run: single token at first (or resume) task.
    Resume with persisted multi-token state: preserve active_tokens (do not collapse).
    """
    existing = getattr(state, "_bpmn_engine_state", None)
    if start_from_task_id and existing and isinstance(existing, dict):
        eng = normalize_engine_state(dict(existing))
        tok = eng.get("active_tokens") or []
        if isinstance(tok, list) and len(tok) > 0:
            if hasattr(state, "__dict__"):
                state.__dict__["_bpmn_engine_state"] = eng
            _sync_current_node_ids_from_tokens(eng)
            return eng
    current = start_from_task_id or get_first_task_id(bpmn)
    if not current:
        return None
    return _ensure_engine_state(state, current_node_id=current)


def _task_retry_key(branch_id: str | None, node_id: str | None) -> str:
    br = (str(branch_id).strip() if branch_id else "") or "_"
    nd = str(node_id).strip() if node_id else ""
    return f"{br}|{nd}"


def _clear_task_entry_monotonic(
    engine_state: dict[str, Any],
    branch_id: str | None,
    node_id: str | None,
) -> None:
    """Drop deadline anchor so a later re-entry at this (branch, task) gets a fresh timer (PAR-014)."""
    key = _task_retry_key(branch_id, node_id)
    tem = engine_state.get("task_entry_monotonic")
    if isinstance(tem, dict) and key in tem:
        del tem[key]


def _clear_task_retry_slot(
    engine_state: dict[str, Any],
    branch_id: str | None,
    node_id: str | None,
) -> None:
    key = _task_retry_key(branch_id, node_id)
    trc = engine_state.get("task_retry_counts")
    if isinstance(trc, dict) and key in trc:
        del trc[key]
    lre = engine_state.get("last_retryable_error")
    if isinstance(lre, dict):
        lk = _task_retry_key(lre.get("branch_id"), lre.get("node_id"))
        if lk == key:
            engine_state["last_retryable_error"] = None


def _set_engine_failure(
    engine_state: dict[str, Any],
    failed_node_id: str | None,
    failure_reason: str,
    condition_failure_metadata: dict[str, Any] | None = None,
) -> None:
    """Record failure details on engine state for UI and logs."""
    engine_state.pop("_pending_timer_skip_reentry_queue", None)
    engine_state["failed_node_id"] = failed_node_id
    engine_state["failure_reason"] = failure_reason
    completed = engine_state.get("completed_node_ids") or []
    engine_state["last_successful_node_id"] = completed[-1] if completed else None
    if condition_failure_metadata:
        engine_state["condition_failure_metadata"] = condition_failure_metadata


def evaluate_condition(condition_text: str, state: Any) -> bool:
    """
    Evaluate a minimal condition expression against workflow state. Single parse/eval path
    via bpmn_conditions. Raises ValueError for unsupported or invalid condition syntax.
    """
    if not condition_text or not condition_text.strip():
        return False
    parsed = parse_condition(condition_text.strip())
    return _eval_parsed_condition(parsed, state)


def select_exclusive_flow(
    bpmn: dict[str, Any],
    gateway_element_id: str,
    state: Any,
    bindings: dict[str, Any],
) -> str | None:
    """
    For an exclusive gateway, evaluate conditions on outgoing flows; return the target
    of the first matching flow, or the default flow if no condition matches, or raise
    if no valid path.
    """
    elements = bpmn.get("elements") or {}
    element = elements.get(gateway_element_id)
    if not element or element.get("type") != "exclusiveGateway":
        return None
    flows = resolve_outgoing_flows(bpmn, gateway_element_id)
    if not flows:
        logger.warning("Exclusive gateway %r has no outgoing flows", gateway_element_id)
        return None
    default_flow_id = element.get("default_flow_id")
    evaluated = []
    for flow_id, target_id, condition_text in flows:
        cond_snippet = (condition_text or "").strip()[:80]
        try:
            result = bool(condition_text and evaluate_condition(condition_text, state))
        except Exception as e:
            result = False
            evaluated.append(
                {
                    "flow_id": flow_id,
                    "target_id": target_id,
                    "condition": cond_snippet,
                    "result": False,
                    "error": str(e),
                }
            )
            continue
        evaluated.append(
            {
                "flow_id": flow_id,
                "target_id": target_id,
                "condition": cond_snippet,
                "result": result,
            }
        )
        if result:
            logger.info(
                "BPMN gateway %r: matched flow %r -> %r (evaluated: %s)",
                gateway_element_id,
                flow_id,
                target_id,
                ", ".join(f"{x['flow_id']}={x.get('result', '?')}" for x in evaluated),
            )
            return target_id
    if default_flow_id:
        for flow_id, target_id, _ in flows:
            if flow_id == default_flow_id:
                logger.info(
                    "BPMN gateway %r: no condition matched, using default flow %r -> %r (evaluated: %s)",
                    gateway_element_id,
                    flow_id,
                    target_id,
                    ", ".join(f"{x['flow_id']}={x.get('result', '?')}" for x in evaluated),
                )
                return target_id
        logger.warning(
            "BPMN gateway %r: default_flow_id %r not in outgoing flows (outgoing: %s)",
            gateway_element_id,
            default_flow_id,
            [f["flow_id"] for f in evaluated],
        )
    logger.error(
        "BPMN gateway %r: no matching condition and no default flow (evaluated: %s)",
        gateway_element_id,
        ", ".join(f"{x['flow_id']}={x.get('result', '?')}" for x in evaluated),
    )
    raise ValueError(
        f"Exclusive gateway '{gateway_element_id}' has no matching condition and no default flow."
    )


def _get_bindings_and_bpmn(workflow_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """Load BPMN and bindings for a workflow. Returns (bpmn_dict, bindings_dict)."""
    context = get_workflow_context(workflow_id)
    bpmn = context.get("bpmn") or {}
    bindings = normalize_bindings(
        context.get("bindings") or {},
        workflow_id=workflow_id,
        executor=context.get("bindings", {}).get("executor", ""),
    )
    return bpmn, bindings


def can_run_with_bpmn_engine(workflow_id: str) -> bool:
    """
    Cheap readiness check: True if the workflow looks BPMN-runnable before a run.

    Uses ``get_workflow_context`` to verify BPMN XML is present, bindings normalize
    to a non-empty ``serviceTasks`` map, the registry exposes a ``state_class_name``,
    and the first executable element after the start is either a bound service task
    or an allowed intermediate timer/message catch (same rules as run startup).

    The runner, WebSocket consumer, and tools call this to **fail fast** with a clear
    message. It is **not** a full static validator: invalid diagrams can still fail
    later in ``run_bpmn_workflow`` or at save time. The runtime is **BPMN-only**—there
    is no legacy path when this returns False.
    """
    try:
        context = get_workflow_context(workflow_id)
        bpmn = context.get("bpmn") or {}
        bindings = normalize_bindings(
            context.get("bindings") or {},
            workflow_id=workflow_id,
            executor=context.get("bindings", {}).get("executor", ""),
        )
        code = context.get("code") or {}
        if not code.get("state_class_name"):
            return False
    except Exception as e:
        logger.debug("can_run_with_bpmn_engine check failed: %s", e, exc_info=True)
        return False
    service_tasks = bindings.get("serviceTasks") or {}
    if not service_tasks:
        return False
    first = get_first_task_id(bpmn)
    if not first:
        return False
    if first in service_tasks:
        return True
    return bool(
        is_intermediate_timer_catch(bpmn, first) or is_intermediate_message_catch(bpmn, first)
    )


def _normalize_max_task_retries(max_task_retries: int) -> int:
    try:
        return max(0, int(max_task_retries))
    except (TypeError, ValueError):
        return 0


_PARALLEL_JOIN_PREFIX = "Workflow.PARALLEL_JOIN:"


def _tokens_remain_in_subprocess(
    engine_state: dict[str, Any], bpmn: dict[str, Any], sp_id: str
) -> bool:
    for t in engine_state.get("active_tokens") or []:
        if not isinstance(t, dict):
            continue
        cid = str(t.get("current_element_id") or "").strip()
        if cid and element_subprocess_container(bpmn, cid) == sp_id:
            return True
    return False


def _push_subprocess_frame(
    engine_state: dict[str, Any],
    sp_id: str,
    bpmn: dict[str, Any],
    *,
    parent_branch_id: str | None,
) -> None:
    stack = engine_state.setdefault("subprocess_stack", [])
    if stack and str(stack[-1].get("subprocess_id") or "").strip() == sp_id:
        return
    el = (bpmn.get("elements") or {}).get(sp_id) or {}
    name = (el.get("name") or "").strip() or sp_id
    now = datetime.now(UTC).isoformat()
    stack.append(
        {
            "subprocess_id": sp_id,
            "name": name,
            "entered_at": now,
            "parent_branch_id": _normalize_optional_str_id(parent_branch_id),
        }
    )
    engine_state.setdefault("subprocess_transitions", []).append(
        {
            "subprocess_id": sp_id,
            "action": "entered",
            "at": now,
        }
    )


async def _complete_subprocess_exit(
    engine_state: dict[str, Any],
    sp_id: str,
    bpmn: dict[str, Any],
    state: Any,
    bindings: dict[str, Any],
    flow_selector: Callable[
        [dict[str, Any], str, set[str], Any, dict[str, Any]],
        str | None,
    ],
) -> None:
    stack = engine_state.setdefault("subprocess_stack", [])
    parent_branch: str | None = None
    while stack and str(stack[-1].get("subprocess_id") or "").strip() == sp_id:
        fr = stack.pop()
        parent_branch = _normalize_optional_str_id(fr.get("parent_branch_id"))
    engine_state.setdefault("subprocess_transitions", []).append(
        {
            "subprocess_id": sp_id,
            "action": "completed",
            "at": datetime.now(UTC).isoformat(),
        }
    )
    tgt = subprocess_parent_continuation_target(bpmn, sp_id)
    if not tgt:
        _raise_engine_failure(
            message=(
                f"Subprocess {sp_id!r} has no parent continuation target "
                "(single outgoing from subprocess boundary)."
            ),
            state=state,
            engine_state=engine_state,
            failure_reason="subprocess_exit_routing_failed",
            failed_node_id=sp_id,
            condition_failure_metadata={},
        )
    seen: set[str] = {sp_id}
    resolved = traverse_until_executable(bpmn, tgt, seen, state, bindings, flow_selector)
    bid = str(parent_branch or "").strip()
    if resolved is None:
        _raise_engine_failure(
            message=(
                f"After subprocess {sp_id!r}, path from {tgt!r} does not resolve "
                "to a runnable task or end."
            ),
            state=state,
            engine_state=engine_state,
            failure_reason="subprocess_exit_routing_failed",
            failed_node_id=sp_id,
            condition_failure_metadata={"continuation_target": tgt},
        )
    if resolved == "Workflow.END":
        return
    jid = parse_parallel_join_sentinel(str(resolved))
    if jid:
        append_token(engine_state, jid, parent_branch)
        if mark_branch_arrived_at_join(engine_state, jid, bid):
            _merge_parallel_join(engine_state, jid, bpmn, state, bindings, flow_selector)
    else:
        nxt = str(resolved).strip()
        append_token(engine_state, nxt, parent_branch)
        sp_new = element_subprocess_container(bpmn, nxt)
        if sp_new:
            _push_subprocess_frame(engine_state, sp_new, bpmn, parent_branch_id=parent_branch)
    _sync_current_node_ids_from_tokens(engine_state)


def _record_boundary_transition(
    engine_state: dict[str, Any],
    *,
    boundary_id: str,
    boundary_type: str,
    attached_to: str,
    reason: str,
) -> None:
    now_iso = datetime.now(UTC).isoformat()
    rec: dict[str, Any] = {
        "boundary_event_id": boundary_id,
        "boundary_type": boundary_type,
        "attached_to_task_id": attached_to,
        "reason": reason,
        "at": now_iso,
    }
    engine_state.setdefault("boundary_transitions", []).append(rec)
    engine_state["last_boundary_transition"] = rec


async def _route_token_through_boundary(
    *,
    engine_state: dict[str, Any],
    token_index: int,
    branch_id: str | None,
    bpmn: dict[str, Any],
    state: Any,
    bindings: dict[str, Any],
    flow_selector: Callable[
        [dict[str, Any], str, list[tuple[str, str, str]], Any, dict[str, Any]],
        str | None,
    ],
    target_element_id: str,
    boundary_id: str,
    boundary_type: str,
    attached_to: str,
    reason: str,
    send_message: Callable[[str, Any], Any] | None,
) -> None:
    _record_boundary_transition(
        engine_state,
        boundary_id=boundary_id,
        boundary_type=boundary_type,
        attached_to=attached_to,
        reason=reason,
    )
    resolved = traverse_until_executable(
        bpmn, target_element_id, set(), state, bindings, flow_selector
    )
    bid = str(branch_id or "").strip()
    idx = token_index
    if resolved is None:
        _raise_engine_failure(
            message=(
                f"Boundary {boundary_id!r} alternate path from {target_element_id!r} "
                "does not resolve to a runnable task or end."
            ),
            state=state,
            engine_state=engine_state,
            failure_reason="boundary_routing_failed",
            failed_node_id=attached_to,
            condition_failure_metadata={
                "boundary_event_id": boundary_id,
                "target_element_id": target_element_id,
            },
        )
    if resolved == "Workflow.END":
        remove_token_at_index(engine_state, idx)
    elif isinstance(resolved, str) and resolved.startswith(_PARALLEL_JOIN_PREFIX):
        join_id = resolved[len(_PARALLEL_JOIN_PREFIX) :]
        replace_token_at_index(engine_state, idx, join_id, branch_id)
        if mark_branch_arrived_at_join(engine_state, join_id, bid):
            _merge_parallel_join(engine_state, join_id, bpmn, state, bindings, flow_selector)
    else:
        replace_token_at_index(engine_state, idx, str(resolved), branch_id)
    _clear_task_entry_monotonic(engine_state, branch_id, attached_to)
    # Next time this (branch, task) is scheduled, skip one timer check (merge-back loop).
    if boundary_type == "timer":
        q = engine_state.setdefault("_pending_timer_skip_reentry_queue", [])
        if isinstance(q, list):
            q.append(_task_retry_key(branch_id, attached_to))
    _sync_current_node_ids_from_tokens(engine_state)
    if send_message:
        await send_message(
            "progress",
            {
                "completed_node_ids": list(engine_state.get("completed_node_ids", [])),
                "current_node_ids": current_node_ids_for_progress(engine_state),
                "engine_state": engine_state,
            },
        )


def _record_intermediate_catch_transition(
    engine_state: dict[str, Any],
    *,
    event_id: str,
    catch_type: str,
) -> None:
    now_iso = datetime.now(UTC).isoformat()
    engine_state.setdefault("intermediate_catch_transitions", []).append(
        {"event_id": event_id, "catch_type": catch_type, "at": now_iso}
    )


async def _advance_past_intermediate_catch(
    *,
    engine_state: dict[str, Any],
    token_index: int,
    branch_id: str | None,
    event_id: str,
    catch_type: str,
    out_target: str,
    bpmn: dict[str, Any],
    state: Any,
    bindings: dict[str, Any],
    flow_selector: Callable[
        [dict[str, Any], str, list[tuple[str, str, str]], Any, dict[str, Any]],
        str | None,
    ],
    send_message: Callable[[str, Any], Awaitable[Any]] | None,
) -> None:
    _append_completed_node(engine_state, event_id)
    _record_intermediate_catch_transition(engine_state, event_id=event_id, catch_type=catch_type)
    engine_state["bpmn_event_wait"] = {}
    resolved = traverse_until_executable(bpmn, out_target, set(), state, bindings, flow_selector)
    idx = token_index
    if resolved is None:
        _raise_engine_failure(
            message=(
                f"After intermediate catch {event_id!r}, path from {out_target!r} "
                "does not resolve to a runnable task or end."
            ),
            state=state,
            engine_state=engine_state,
            failure_reason="intermediate_catch_routing_failed",
            failed_node_id=event_id,
            condition_failure_metadata={"out_target": out_target},
        )
    if resolved == "Workflow.END":
        remove_token_at_index(engine_state, idx)
    elif isinstance(resolved, str) and resolved.startswith(_PARALLEL_JOIN_PREFIX):
        join_id = resolved[len(_PARALLEL_JOIN_PREFIX) :]
        replace_token_at_index(engine_state, idx, join_id, branch_id)
        bid = str(branch_id or "").strip()
        if mark_branch_arrived_at_join(engine_state, join_id, bid):
            _merge_parallel_join(engine_state, join_id, bpmn, state, bindings, flow_selector)
    else:
        replace_token_at_index(engine_state, idx, str(resolved), branch_id)
    _sync_current_node_ids_from_tokens(engine_state)
    if send_message:
        await send_message(
            "progress",
            {
                "completed_node_ids": list(engine_state.get("completed_node_ids", [])),
                "current_node_ids": current_node_ids_for_progress(engine_state),
                "engine_state": engine_state,
            },
        )


def _get_intermediate_catch_token_context(
    *,
    engine_state: dict[str, Any],
    token_index: int,
    bpmn: dict[str, Any],
    state: Any,
) -> tuple[dict[str, Any], str, str | None, str]:
    toks = engine_state.get("active_tokens") or []
    if len(toks) != 1:
        _raise_engine_failure(
            message=(
                "Intermediate timer/message catch with multiple active tokens is not supported "
                "(PAR-015 v1). Use a single-token path through the catch event."
            ),
            state=state,
            engine_state=engine_state,
            failure_reason="intermediate_catch_parallel_not_supported",
            failed_node_id=None,
            condition_failure_metadata={"token_count": len(toks)},
        )
    tok = toks[token_index]
    eid = str(tok.get("current_element_id") or "").strip()
    branch_id = tok.get("branch_id") if isinstance(tok, dict) else None
    out_tgt = intermediate_catch_outgoing_target(bpmn, eid)
    if not out_tgt:
        _raise_engine_failure(
            message=f"Intermediate catch {eid!r} has no single outgoing target.",
            state=state,
            engine_state=engine_state,
            failure_reason="intermediate_catch_invalid",
            failed_node_id=eid,
        )
    return tok, eid, branch_id, out_tgt


async def _handle_intermediate_timer_catch(
    *,
    engine_state: dict[str, Any],
    token_index: int,
    bpmn: dict[str, Any],
    state: Any,
    bindings: dict[str, Any],
    flow_selector: Callable[
        [dict[str, Any], str, list[tuple[str, str, str]], Any, dict[str, Any]], str | None
    ],
    send_message: Callable[[str, Any], Awaitable[Any]] | None,
    eid: str,
    branch_id: str | None,
    out_tgt: str,
) -> bool:
    el = (bpmn.get("elements") or {}).get(eid) or {}
    dur = iso8601_duration_to_seconds(str(el.get("catch_duration_iso") or "")) or 0.0
    wait = engine_state.get("bpmn_event_wait") or {}
    if (
        isinstance(wait, dict)
        and str(wait.get("waiting_event_id") or "") == eid
        and wait.get("waiting_event_type") == "timer"
    ):
        try:
            deadline = float(wait.get("timer_deadline_ts") or 0)
        except (TypeError, ValueError):
            deadline = 0.0
        if time.time() >= deadline:
            await _advance_past_intermediate_catch(
                engine_state=engine_state,
                token_index=token_index,
                branch_id=branch_id,
                event_id=eid,
                catch_type="timer",
                out_target=out_tgt,
                bpmn=bpmn,
                state=state,
                bindings=bindings,
                flow_selector=flow_selector,
                send_message=send_message,
            )
            return True
    deadline = time.time() + max(dur, 0.001)
    engine_state["bpmn_event_wait"] = {
        "waiting_event_id": eid,
        "waiting_event_type": "timer",
        "timer_deadline_ts": deadline,
        "timer_deadline_iso": datetime.fromtimestamp(deadline, UTC).isoformat(),
        "branch_id": branch_id,
    }
    if hasattr(state, "__dict__"):
        state.__dict__["_bpmn_engine_state"] = normalize_engine_state(engine_state)
        state.__dict__["_bpmn_next_step"] = eid
    raise BpmnIntermediateWaitError(state, eid, "timer")


async def _handle_intermediate_message_catch(
    *,
    engine_state: dict[str, Any],
    token_index: int,
    bpmn: dict[str, Any],
    state: Any,
    bindings: dict[str, Any],
    flow_selector: Callable[
        [dict[str, Any], str, list[tuple[str, str, str]], Any, dict[str, Any]], str | None
    ],
    send_message: Callable[[str, Any], Awaitable[Any]] | None,
    eid: str,
    branch_id: str | None,
    out_tgt: str,
) -> bool:
    el = (bpmn.get("elements") or {}).get(eid) or {}
    mk = str(el.get("catch_message_key") or "").strip()
    satisfied_raw = engine_state.get("satisfied_intermediate_messages") or []
    sat_set = {
        str(x).strip() for x in satisfied_raw if isinstance(x, (str, int)) and str(x).strip()
    }
    if mk and mk in sat_set:
        sat_set.discard(mk)
        engine_state["satisfied_intermediate_messages"] = sorted(sat_set)
        await _advance_past_intermediate_catch(
            engine_state=engine_state,
            token_index=token_index,
            branch_id=branch_id,
            event_id=eid,
            catch_type="message",
            out_target=out_tgt,
            bpmn=bpmn,
            state=state,
            bindings=bindings,
            flow_selector=flow_selector,
            send_message=send_message,
        )
        return True
    engine_state["bpmn_event_wait"] = {
        "waiting_event_id": eid,
        "waiting_event_type": "message",
        "message_key": mk,
        "branch_id": branch_id,
    }
    if hasattr(state, "__dict__"):
        state.__dict__["_bpmn_engine_state"] = normalize_engine_state(engine_state)
        state.__dict__["_bpmn_next_step"] = eid
    raise BpmnIntermediateWaitError(state, eid, "message")


async def _process_intermediate_catch_token(
    *,
    engine_state: dict[str, Any],
    token_index: int,
    bpmn: dict[str, Any],
    state: Any,
    bindings: dict[str, Any],
    flow_selector: Callable[
        [dict[str, Any], str, list[tuple[str, str, str]], Any, dict[str, Any]],
        str | None,
    ],
    send_message: Callable[[str, Any], Awaitable[Any]] | None,
) -> None:
    _, eid, branch_id, out_tgt = _get_intermediate_catch_token_context(
        engine_state=engine_state,
        token_index=token_index,
        bpmn=bpmn,
        state=state,
    )

    if is_intermediate_timer_catch(bpmn, eid):
        await _handle_intermediate_timer_catch(
            engine_state=engine_state,
            token_index=token_index,
            bpmn=bpmn,
            state=state,
            bindings=bindings,
            flow_selector=flow_selector,
            send_message=send_message,
            eid=eid,
            branch_id=branch_id,
            out_tgt=out_tgt,
        )
        return

    if is_intermediate_message_catch(bpmn, eid):
        await _handle_intermediate_message_catch(
            engine_state=engine_state,
            token_index=token_index,
            bpmn=bpmn,
            state=state,
            bindings=bindings,
            flow_selector=flow_selector,
            send_message=send_message,
            eid=eid,
            branch_id=branch_id,
            out_tgt=out_tgt,
        )
        return

    _raise_engine_failure(
        message=f"Unsupported intermediate catch at {eid!r}.",
        state=state,
        engine_state=engine_state,
        failure_reason="intermediate_catch_invalid",
        failed_node_id=eid,
    )


def _raise_engine_failure(
    *,
    message: str,
    state: Any,
    engine_state: dict[str, Any],
    failure_reason: str,
    failed_node_id: str | None,
    condition_failure_metadata: dict[str, Any] | None = None,
    cause: Exception | None = None,
) -> None:
    _set_engine_failure(
        engine_state,
        failed_node_id,
        failure_reason,
        condition_failure_metadata=condition_failure_metadata,
    )
    exc = BpmnEngineError(
        message,
        state=state,
        failure_reason=failure_reason,
        failed_node_id=failed_node_id,
        condition_failure_metadata=condition_failure_metadata,
    )
    if cause is not None:
        raise exc from cause
    raise exc


def _resolve_task_execution_context(
    *,
    engine_state: dict[str, Any],
    token_index: int,
    pick_err: str | None,
    service_tasks: dict[str, Any],
    executor_instance: Any,
    state: Any,
    bpmn: dict[str, Any],
    bindings: dict[str, Any],
    flow_selector: Callable[
        [dict[str, Any], str, list[tuple[str, str, str]], Any, dict[str, Any]], str | None
    ],
) -> tuple[dict[str, Any], str, str | None, Callable[[Any], Awaitable[Any]], str | None]:
    tok = engine_state["active_tokens"][token_index]
    current = tok.get("current_element_id")
    branch_id = tok.get("branch_id") if isinstance(tok, dict) else None
    current_key = str(current).strip()

    if pick_err == "missing_binding":
        _raise_engine_failure(
            message=f"No binding for BPMN task '{current_key}' in bpmn-bindings.yaml",
            state=state,
            engine_state=engine_state,
            failure_reason="missing_binding",
            failed_node_id=current_key,
        )

    binding = service_tasks.get(current_key)
    if not binding:
        _raise_engine_failure(
            message=f"No binding for BPMN task '{current}' in bpmn-bindings.yaml",
            state=state,
            engine_state=engine_state,
            failure_reason="missing_binding",
            failed_node_id=current,
        )
    handler_name = (binding.get("handler") or "").strip()
    if not handler_name:
        _raise_engine_failure(
            message=f"Binding for task '{current}' has no handler name",
            state=state,
            engine_state=engine_state,
            failure_reason="missing_binding",
            failed_node_id=current,
        )

    method = getattr(executor_instance, handler_name, None)
    if method is None:
        _raise_engine_failure(
            message=(
                f"Handler '{handler_name}' for task '{current}' not found on executor "
                f"({type(executor_instance).__name__})"
            ),
            state=state,
            engine_state=engine_state,
            failure_reason="missing_handler",
            failed_node_id=current,
        )

    try:
        next_for_pause = next_step_after_task_completion(
            bpmn, current, state, bindings, flow_selector
        )
    except ValueError as e:
        _raise_engine_failure(
            message=str(e),
            state=state,
            engine_state=engine_state,
            failure_reason="invalid_gateway",
            failed_node_id=current,
            condition_failure_metadata={"message": str(e)},
            cause=e,
        )

    return tok, current_key, branch_id, method, next_for_pause


async def _invoke_task_method(
    *,
    method: Callable[[Any], Awaitable[Any]],
    state: Any,
    current: str,
    next_for_pause: str | None,
    send_message: Callable[[str, Any], Any] | None,
) -> Any:
    if send_message:
        await send_message("step", current)
    await asyncio.sleep(0.05)

    result = await method(state)
    if (
        result is not None
        and isinstance(result, str)
        and result.strip()
        and next_for_pause
        and result.strip() != next_for_pause
    ):
        logger.debug(
            "Task %r returned %r; ignoring for routing (BPMN next is %r)",
            current,
            result.strip(),
            next_for_pause,
        )
    try:
        out = getattr(state, "model_dump", None)
        if callable(out):
            logger.info("Task %r completed. State output: %s", current, out())
        else:
            logger.info("Task %r completed. Returned: %s", current, result)
    except Exception as e:
        logger.debug("Failed to get state output for logging: %s", e)
        logger.info("Task %r completed. Returned: %s", current, result)
    return result


async def _handle_retryable_task_error(
    *,
    error: BpmnRetryableTaskError,
    engine_state: dict[str, Any],
    branch_id: str | None,
    current_key: str,
    max_task_retries: int,
    send_message: Callable[[str, Any], Any] | None,
    state: Any,
) -> None:
    trc = engine_state.setdefault("task_retry_counts", {})
    if not isinstance(trc, dict):
        trc = {}
        engine_state["task_retry_counts"] = trc
    rkey = _task_retry_key(branch_id, current_key)
    nfail = int(trc.get(rkey, 0)) + 1
    trc[rkey] = nfail
    now_iso = datetime.now(UTC).isoformat()
    engine_state["last_retryable_error"] = {
        "message": str(error),
        "node_id": current_key,
        "branch_id": branch_id,
        "attempt": nfail,
        "at": now_iso,
    }
    if nfail > max_task_retries:
        meta = {
            "retry_attempts": nfail,
            "bpmn_max_task_retries": max_task_retries,
            "last_error": str(error),
            "branch_id": branch_id,
        }
        _raise_engine_failure(
            message=(
                f"Task {current_key!r} exceeded retry limit "
                f"({max_task_retries} re-attempts after first failure)."
            ),
            state=state,
            engine_state=engine_state,
            failure_reason="retry_exhausted",
            failed_node_id=current_key,
            condition_failure_metadata=meta,
            cause=error,
        )

    _sync_current_node_ids_from_tokens(engine_state)
    if send_message:
        await send_message(
            "progress",
            {
                "completed_node_ids": list(engine_state.get("completed_node_ids", [])),
                "current_node_ids": current_node_ids_for_progress(engine_state),
                "engine_state": engine_state,
                "retrying_task_id": current_key,
                "retry_attempt": nfail,
                "bpmn_max_task_retries": max_task_retries,
            },
        )


async def run_bpmn_workflow(  # noqa: C901
    executor_instance: Any,
    state: Any,
    bpmn: dict[str, Any],
    bindings: dict[str, Any],
    *,
    start_from_task_id: str | None = None,
    send_message: Callable[[str, Any], Any] | None = None,
    execution_check: Callable[[], Awaitable[str | None]] | None = None,
    max_task_retries: int = 0,
) -> Any:
    """
    Execute workflow by following the BPMN diagram and invoking bound handlers.

    Args:
        executor_instance: Workflow class instance with handler methods.
        state: State object (must have workflow_steps list, appended to as tasks run).
        bpmn: Parsed BPMN summary from parse_bpmn_xml().
        bindings: Normalized bindings dict with serviceTasks[task_id].handler.
        start_from_task_id: If set, start from this task (for resume). Otherwise start from first.
        send_message: Optional async callback (msg_type, payload) for progress.
        execution_check: Optional async callable returning None to continue, or \"cancelled\" /
            \"timeout\" to abort cooperatively at the start of the next token iteration.
        max_task_retries: Max extra invocations after first BpmnRetryableTaskError per (branch, node).

    Returns:
        The state object after execution.

    Raises:
        TaskPendingError: When a handler pauses for a human task (re-raise to let runner save progress).
        BpmnIntermediateWaitError: Timer/message catch not satisfied (PAR-015); runner persists and resumes.
        BpmnEngineError: On engine failures including cooperative cancel/timeout.
        ValueError: When a bound handler is missing on the executor.
    """
    service_tasks = bindings.get("serviceTasks") or {}

    def _flow_selector(_bpmn, element_id, _flows, _state, _bindings):
        el = (_bpmn.get("elements") or {}).get(element_id) or {}
        if el.get("type") == "exclusiveGateway":
            return select_exclusive_flow(_bpmn, element_id, _state, _bindings)
        return None

    engine_state = _init_engine_state_for_bpmn_run(state, bpmn, start_from_task_id)
    if engine_state is None:
        logger.warning("BPMN engine: no first task found in diagram")
        return state

    max_tr = _normalize_max_task_retries(max_task_retries)

    while True:
        if execution_check:
            abort_reason = await execution_check()
            if abort_reason == "cancelled":
                now_iso = datetime.now(UTC).isoformat()
                meta = {"cancelled_at": now_iso}
                _set_engine_failure(engine_state, None, "cancelled", meta)
                raise BpmnEngineError(
                    "Workflow execution was cancelled.",
                    state=state,
                    failure_reason="cancelled",
                    failed_node_id=None,
                    condition_failure_metadata=meta,
                )
            if abort_reason == "timeout":
                toks = engine_state.get("active_tokens") or []
                if len(toks) == 1 and isinstance(toks[0], dict):
                    tid = str(toks[0].get("current_element_id") or "").strip()
                    br = toks[0].get("branch_id")
                    tb = get_timer_boundary_for_task(bpmn, tid)
                    dur = (
                        iso8601_duration_to_seconds(str(tb.get("duration_iso") or ""))
                        if tb
                        else None
                    ) or 0.0
                    if tb and dur > 0:
                        await _route_token_through_boundary(
                            engine_state=engine_state,
                            token_index=0,
                            branch_id=br,
                            bpmn=bpmn,
                            state=state,
                            bindings=bindings,
                            flow_selector=_flow_selector,
                            target_element_id=str(tb["target_element_id"]),
                            boundary_id=str(tb["boundary_id"]),
                            boundary_type="timer",
                            attached_to=tid,
                            reason="run_timeout_routed_to_timer_boundary",
                            send_message=send_message,
                        )
                        continue
                now_iso = datetime.now(UTC).isoformat()
                meta = {"timed_out_at": now_iso}
                _set_engine_failure(engine_state, None, "timeout", meta)
                raise BpmnEngineError(
                    "Workflow execution exceeded the configured timeout.",
                    state=state,
                    failure_reason="timeout",
                    failed_node_id=None,
                    condition_failure_metadata=meta,
                )

        idx, pick_err = _pick_token_for_execution(engine_state, bpmn, service_tasks)
        if idx is None:
            if not (engine_state.get("active_tokens") or []):
                break
            _raise_engine_failure(
                message="No runnable BPMN service task among active tokens.",
                state=state,
                engine_state=engine_state,
                failure_reason="no_runnable_token",
                failed_node_id=None,
                condition_failure_metadata={
                    "message": "No bound serviceTask among active tokens.",
                },
            )

        if pick_err == "intermediate_catch":
            await _process_intermediate_catch_token(
                engine_state=engine_state,
                token_index=idx,
                bpmn=bpmn,
                state=state,
                bindings=bindings,
                flow_selector=_flow_selector,
                send_message=send_message,
            )
            continue

        _tok, current_key, branch_id, method, next_for_pause = _resolve_task_execution_context(
            engine_state=engine_state,
            token_index=idx,
            pick_err=pick_err,
            service_tasks=service_tasks,
            executor_instance=executor_instance,
            state=state,
            bpmn=bpmn,
            bindings=bindings,
            flow_selector=_flow_selector,
        )
        current = current_key

        tem = engine_state.setdefault("task_entry_monotonic", {})
        tkey = _task_retry_key(branch_id, current_key)
        pending_q = engine_state.get("_pending_timer_skip_reentry_queue")
        skip_timer_once = (
            isinstance(pending_q, list) and len(pending_q) > 0 and pending_q[0] == tkey
        )
        if skip_timer_once and isinstance(pending_q, list):
            pending_q.pop(0)
            if not pending_q:
                engine_state.pop("_pending_timer_skip_reentry_queue", None)
        if tkey not in tem:
            tem[tkey] = time.monotonic()
        if skip_timer_once:
            tem[tkey] = time.monotonic()
        tb = get_timer_boundary_for_task(bpmn, current_key)
        if tb and not skip_timer_once:
            sec = iso8601_duration_to_seconds(str(tb.get("duration_iso") or "")) or 0.0
            if sec > 0 and (time.monotonic() - float(tem[tkey])) >= sec:
                await _route_token_through_boundary(
                    engine_state=engine_state,
                    token_index=idx,
                    branch_id=branch_id,
                    bpmn=bpmn,
                    state=state,
                    bindings=bindings,
                    flow_selector=_flow_selector,
                    target_element_id=str(tb["target_element_id"]),
                    boundary_id=str(tb["boundary_id"]),
                    boundary_type="timer",
                    attached_to=current_key,
                    reason="timer_deadline",
                    send_message=send_message,
                )
                _clear_task_retry_slot(engine_state, branch_id, current_key)
                continue

        try:
            await _invoke_task_method(
                method=method,
                state=state,
                current=current,
                next_for_pause=next_for_pause,
                send_message=send_message,
            )
        except TaskPendingError:
            _append_completed_node(engine_state, current)
            # Successor may be join → next_for_pause is None; keep token on current task for resume.
            pause_pos = next_for_pause if next_for_pause is not None else current
            replace_token_at_index(engine_state, idx, pause_pos, branch_id)
            _sync_current_node_ids_from_tokens(engine_state)
            if hasattr(state, "__dict__"):
                state.__dict__["_bpmn_next_step"] = pause_pos
            raise
        except BpmnRetryableTaskError as e:
            await _handle_retryable_task_error(
                error=e,
                engine_state=engine_state,
                branch_id=branch_id,
                current_key=current_key,
                max_task_retries=max_tr,
                send_message=send_message,
                state=state,
            )
            continue
        except BpmnModeledBoundaryError as e:
            eb = get_error_boundary_for_task(bpmn, current_key)
            if not eb:
                _raise_engine_failure(
                    message=(
                        str(e).strip()
                        or "BpmnModeledBoundaryError raised but task has no error boundary."
                    ),
                    state=state,
                    engine_state=engine_state,
                    failure_reason="handler_error",
                    failed_node_id=current_key,
                    cause=e,
                )
            await _route_token_through_boundary(
                engine_state=engine_state,
                token_index=idx,
                branch_id=branch_id,
                bpmn=bpmn,
                state=state,
                bindings=bindings,
                flow_selector=_flow_selector,
                target_element_id=str(eb["target_element_id"]),
                boundary_id=str(eb["boundary_id"]),
                boundary_type="error",
                attached_to=current_key,
                reason=str(e).strip() or "modeled_error",
                send_message=send_message,
            )
            _clear_task_retry_slot(engine_state, branch_id, current_key)
            continue
        except Exception as e:
            _raise_engine_failure(
                message=str(e),
                state=state,
                engine_state=engine_state,
                failure_reason="handler_error",
                failed_node_id=current,
                cause=e,
            )

        _clear_task_retry_slot(engine_state, branch_id, current_key)
        _clear_task_entry_monotonic(engine_state, branch_id, current_key)

        if not getattr(state, "workflow_steps", None) and hasattr(state, "__dict__"):
            state.__dict__["workflow_steps"] = []
        if current not in state.workflow_steps:
            state.workflow_steps.append(current)

        try:
            kind, data = resolve_position_after_service_task(
                bpmn, current, state, bindings, _flow_selector
            )
        except ValueError as e:
            _raise_engine_failure(
                message=str(e),
                state=state,
                engine_state=engine_state,
                failure_reason="invalid_gateway",
                failed_node_id=current,
                condition_failure_metadata={"message": str(e)},
                cause=e,
            )

        _append_completed_node(engine_state, current)

        if kind == "join":
            join_id = data if isinstance(data, str) else str(data)
            bid = str(branch_id or "").strip()
            pj = get_pending_join(engine_state, join_id)
            exp = list(pj.get("expected_branch_ids") or []) if pj else []
            if not pj or bid not in exp:
                _raise_engine_failure(
                    message=f"Join {join_id!r} correlation failed for branch {bid!r}.",
                    state=state,
                    engine_state=engine_state,
                    failure_reason="join_correlation_failed",
                    failed_node_id=current,
                    condition_failure_metadata={
                        "join_element_id": join_id,
                        "branch_id": bid,
                        "message": (
                            "Parallel join is not registered for this execution or "
                            f"branch {bid!r} is not expected at join {join_id!r}."
                        ),
                    },
                )
            replace_token_at_index(engine_state, idx, join_id, branch_id)
            if mark_branch_arrived_at_join(engine_state, join_id, bid):
                _merge_parallel_join(engine_state, join_id, bpmn, state, bindings, _flow_selector)
        elif kind == "end":
            remove_token_at_index(engine_state, idx)
        elif kind == "subprocess_internal_end":
            sp_id = str(data).strip()
            remove_token_at_index(engine_state, idx)
            if not _tokens_remain_in_subprocess(engine_state, bpmn, sp_id):
                await _complete_subprocess_exit(
                    engine_state,
                    sp_id,
                    bpmn,
                    state,
                    bindings,
                    _flow_selector,
                )
        elif kind == "task":
            nxt = data if isinstance(data, str) else None
            if nxt:
                cur_sp = element_subprocess_container(bpmn, current)
                nxt_sp = element_subprocess_container(bpmn, nxt)
                if nxt_sp and nxt_sp != cur_sp:
                    _push_subprocess_frame(
                        engine_state,
                        nxt_sp,
                        bpmn,
                        parent_branch_id=branch_id,
                    )
            replace_token_at_index(engine_state, idx, nxt, branch_id)
        elif kind == "fork":
            fork_id, pairs = data
            _append_completed_node(engine_state, fork_id)
            try:
                join_id = join_gateway_for_parallel_fork(bpmn, fork_id)
            except ValueError as e:
                _raise_engine_failure(
                    message=str(e),
                    state=state,
                    engine_state=engine_state,
                    failure_reason="join_correlation_failed",
                    failed_node_id=fork_id,
                    condition_failure_metadata={"message": str(e)},
                    cause=e,
                )
            new_toks = [
                {"current_element_id": tid, "branch_id": bid}
                for bid, tid in pairs
                if tid is not None
            ]
            if join_id:
                flow_list = resolve_outgoing_flows(bpmn, fork_id)
                expected = [f"{fork_id}:{fid}" for fid, _, _ in flow_list]
                br_with_tasks = {bid for bid, tid in pairs if tid}
                register_pending_join(engine_state, join_id, fork_id, expected)
                for ebid in expected:
                    if ebid not in br_with_tasks:
                        mark_branch_arrived_at_join(engine_state, join_id, ebid)
            cur_sp_fork = element_subprocess_container(bpmn, fork_id)
            for t in new_toks:
                if not isinstance(t, dict):
                    continue
                tid = str(t.get("current_element_id") or "").strip()
                if not tid:
                    continue
                tsp = element_subprocess_container(bpmn, tid)
                if tsp and tsp != cur_sp_fork:
                    _push_subprocess_frame(
                        engine_state,
                        tsp,
                        bpmn,
                        parent_branch_id=_normalize_optional_str_id(t.get("branch_id")),
                    )
            replace_token_at_index_with_tokens(engine_state, idx, new_toks)
            if join_id and is_join_satisfied(engine_state, join_id):
                _merge_parallel_join(engine_state, join_id, bpmn, state, bindings, _flow_selector)
        else:
            remove_token_at_index(engine_state, idx)

        _sync_current_node_ids_from_tokens(engine_state)

        if send_message:
            cur_ids = current_node_ids_for_progress(engine_state)
            progress = {
                "completed_node_ids": list(engine_state.get("completed_node_ids", [])),
                "current_node_ids": cur_ids,
                "engine_state": engine_state,
            }
            await send_message("progress", progress)

    return state


def get_next_step_for_resume(state: Any) -> str | None:
    """
    After a TaskPendingError, return the BPMN task id to resume from.
    The engine sets state._bpmn_next_step when pausing.
    """
    if state is None:
        return None
    return getattr(state, "_bpmn_next_step", None)


def create_initial_state_from_inputs(workflow_id: str, input_data: dict[str, Any]) -> Any:
    """
    Build the workflow state object from input_data by instantiating the
    workflow's state class (from workflow.py). Used when running via BPMN engine.

    Returns:
        State instance with workflow_steps = [].
    Raises:
        ValueError: If state class cannot be resolved or instantiation fails.
    """
    context = get_workflow_context(workflow_id)
    code = context.get("code") or {}
    state_class_name = code.get("state_class_name")
    if not state_class_name:
        raise ValueError(
            f"Workflow {workflow_id} has no state class (state_class_name) in workflow.py; "
            "cannot run with BPMN engine."
        )
    try:
        from importlib import import_module

        mod = import_module(f"workflows.{workflow_id}.workflow")
        state_class = getattr(mod, state_class_name)
    except (ImportError, AttributeError) as e:
        raise ValueError(
            f"Cannot load state class {state_class_name} for workflow {workflow_id}: {e}"
        ) from e
    try:
        state = state_class(**(input_data or {}))
    except Exception as e:
        raise ValueError(
            f"Failed to create initial state for {workflow_id} with inputs {list((input_data or {}).keys())}: {e}"
        ) from e
    if not getattr(state, "workflow_steps", None):
        state.workflow_steps = []
    return state
