"""
Operator-facing BPMN run diagnostics (PAR-013). Pure functions; no ORM.
"""

from __future__ import annotations

from typing import Any

_ACTIVE_BPMN_STATUSES = frozenset(
    {
        "running",
        "waiting_for_task",
        "pending",
        "waiting_for_bpmn_timer",
        "waiting_for_bpmn_message",
    }
)
_ACTIVE_OR_TERMINAL_BPMN_STATUSES = _ACTIVE_BPMN_STATUSES | frozenset({"failed", "cancelled"})


def failure_reason_operator_label(reason: str | None) -> str:
    """Human-readable label for progress_data failure_reason."""
    if not reason:
        return "Stopped"
    mapping = {
        "handler_error": "Task handler failed",
        "invalid_gateway": "Gateway condition error",
        "join_correlation_failed": "Parallel join mismatch",
        "cancelled": "Cancelled by operator or system",
        "timeout": "Execution time limit reached",
        "retry_exhausted": "Task retries exhausted",
        "missing_binding": "Missing BPMN binding",
        "missing_handler": "Handler not found on executor",
        "boundary_routing_failed": "Boundary alternate path could not be resolved",
        "intermediate_catch_parallel_not_supported": "Intermediate catch with multiple tokens",
        "intermediate_catch_routing_failed": "Path after intermediate catch invalid",
        "intermediate_catch_invalid": "Intermediate catch configuration error",
        "subprocess_exit_routing_failed": "Subprocess exit routing failed",
    }
    return mapping.get(str(reason), str(reason).replace("_", " ").title())


def _fmt_nodes(ids: list[Any]) -> str:
    if not ids:
        return "—"
    return ", ".join(str(x) for x in ids if x is not None and str(x).strip())


def _normalized_current_node_ids(progress_data: dict[str, Any]) -> list[str]:
    """Return current BPMN node ids as a compact list of non-empty strings."""
    cur = progress_data.get("current_node_ids") or []
    if not isinstance(cur, list):
        cur = [cur] if cur else []
    return [str(x) for x in cur if x is not None and str(x).strip()]


def _append_status_timeline_lines(
    lines: list[str], *, status: str, pd: dict[str, Any], eng: dict[str, Any]
) -> None:
    if status == "waiting_for_task" and pd.get("next_step"):
        lines.append(
            f"Paused for human input; engine will resume from BPMN task “{pd.get('next_step')}”."
        )
        return
    if status == "pending" and pd.get("next_step"):
        lines.append(f"Ready to resume from BPMN task “{pd.get('next_step')}”.")
        return
    if status == "waiting_for_bpmn_timer":
        bew = eng.get("bpmn_event_wait") if isinstance(eng.get("bpmn_event_wait"), dict) else {}
        iso = bew.get("timer_deadline_iso") or bew.get("timer_deadline_ts") or "?"
        lines.append(
            f"Waiting on intermediate timer (deadline {iso}); explicit resume re-evaluates elapsed time."
        )
        return
    if status == "waiting_for_bpmn_message":
        bew = eng.get("bpmn_event_wait") if isinstance(eng.get("bpmn_event_wait"), dict) else {}
        mk = bew.get("message_key") or "?"
        lines.append(f"Waiting on intermediate message {mk!r}; satisfy via run API then resume.")


def _append_retry_timeline_lines(
    lines: list[str], *, status: str, pd: dict[str, Any]
) -> str | None:
    retry_tid = pd.get("retrying_task_id")
    if not retry_tid or status != "running":
        return None
    attempt = pd.get("retry_attempt")
    max_r = pd.get("bpmn_max_task_retries")
    if attempt is not None and max_r is not None:
        total = int(max_r) + 1
        lines.append(
            f"Retrying task {retry_tid!r} (failure #{attempt}, up to {total} total attempts)."
        )
    else:
        lines.append(f"Retrying task {retry_tid!r} after transient failure.")
    return str(retry_tid)


def _append_join_wait_timeline_lines(lines: list[str], *, status: str, eng: dict[str, Any]) -> None:
    pj = eng.get("pending_joins") if isinstance(eng.get("pending_joins"), dict) else {}
    if not pj or status not in _ACTIVE_OR_TERMINAL_BPMN_STATUSES:
        return
    parts = []
    for jid, info in sorted(pj.items()):
        if not isinstance(info, dict):
            continue
        arr = info.get("arrived_branch_ids") or []
        exp = info.get("expected_branch_ids") or []
        na = len(arr) if isinstance(arr, list) else 0
        ne = len(exp) if isinstance(exp, list) else 0
        parts.append(f"{jid} ({na}/{ne} branches arrived)")
    if parts:
        lines.append("Parallel join wait: " + "; ".join(parts) + ".")


def _append_boundary_timeline_lines(lines: list[str], eng: dict[str, Any]) -> None:
    btrans = eng.get("boundary_transitions") or []
    if not isinstance(btrans, list) or not btrans:
        return
    for rec in btrans:
        if not isinstance(rec, dict):
            continue
        bt = str(rec.get("boundary_type") or "")
        att = str(rec.get("attached_to_task_id") or "")
        reason = str(rec.get("reason") or "")
        if bt == "timer" and reason == "run_timeout_routed_to_timer_boundary":
            lines.append(
                f"Run time limit reached; routed to timer-boundary path from task {att!r}."
            )
        elif bt == "timer":
            lines.append(f"Deadline path triggered from task {att!r}.")
        elif bt == "error":
            lines.append(f"Error boundary taken from task {att!r}.")
        else:
            lines.append(f"Boundary event ({bt}) from task {att!r}.")


def _append_intermediate_timeline_lines(lines: list[str], eng: dict[str, Any]) -> None:
    ict = eng.get("intermediate_catch_transitions") or []
    if not isinstance(ict, list) or not ict:
        return
    for rec in ict:
        if not isinstance(rec, dict):
            continue
        eid = str(rec.get("event_id") or "")
        ct = str(rec.get("catch_type") or "")
        if eid and ct:
            lines.append(f"Advanced past intermediate {ct} catch at {eid!r}.")


def _append_subprocess_timeline_lines(
    lines: list[str], *, status: str, eng: dict[str, Any]
) -> None:
    spt = eng.get("subprocess_transitions") or []
    if isinstance(spt, list) and spt:
        for rec in spt:
            if not isinstance(rec, dict):
                continue
            sid = str(rec.get("subprocess_id") or "")
            act = str(rec.get("action") or "")
            nm = str(rec.get("name") or "").strip()
            label = nm or sid
            if act == "entered" and sid:
                lines.append(f"Entered subprocess {label!r} ({sid}).")
            elif act == "completed" and sid:
                lines.append(f"Completed subprocess {label!r} ({sid}); continuing in parent scope.")
    stack = eng.get("subprocess_stack") or []
    if not (isinstance(stack, list) and stack and status in _ACTIVE_OR_TERMINAL_BPMN_STATUSES):
        return
    top = stack[-1] if isinstance(stack[-1], dict) else {}
    spn = str(top.get("name") or top.get("subprocess_id") or "").strip()
    if spn:
        lines.append(f"Active subprocess context: {spn!r}.")


def _append_current_focus_timeline_lines(
    lines: list[str], *, status: str, cur: list[str], retry_tid: str | None
) -> None:
    if not cur or status not in _ACTIVE_OR_TERMINAL_BPMN_STATUSES:
        return
    if len(cur) > 1:
        lines.append(f"Active BPMN nodes (parallel): {_fmt_nodes(cur)}.")
    elif not retry_tid or status != "running":
        lines.append(f"Current BPMN focus: {_fmt_nodes(cur)}.")


def _append_terminal_timeline_lines(lines: list[str], *, status: str, pd: dict[str, Any]) -> None:
    reason = pd.get("failure_reason")
    if status == "cancelled":
        lines.append(
            failure_reason_operator_label("cancelled")
            + (f" at {pd.get('cancelled_at')}." if pd.get("cancelled_at") else ".")
        )
    elif status == "failed" and reason == "timeout":
        ts = pd.get("timed_out_at") or ""
        sec = pd.get("timeout_seconds")
        lines.append(
            failure_reason_operator_label("timeout")
            + (f" (limit {sec}s)" if sec is not None else "")
            + (f" at {ts}." if ts else ".")
        )
    elif status == "failed" and reason == "retry_exhausted":
        node = pd.get("failed_node_id") or "task"
        lines.append(f"Retries exhausted on node {node!r}; run stopped.")
    elif status == "failed" and reason:
        lines.append(f"{failure_reason_operator_label(reason)}.")
    if status == "completed" and (pd.get("completed_node_ids") or []):
        lines.append("All BPMN paths for this run finished successfully.")


def build_operator_timeline_lines(status: str, progress_data: dict[str, Any] | None) -> list[str]:
    """Chronological-style narrative lines from persisted progress_data."""
    lines: list[str] = []
    if not progress_data:
        if status == "completed":
            lines.append("Run completed.")
        return lines

    pd = progress_data
    eng = pd.get("engine_state") if isinstance(pd.get("engine_state"), dict) else {}
    completed = list(pd.get("completed_node_ids") or [])
    if not completed and isinstance(pd.get("state_data"), dict):
        completed = list((pd.get("state_data") or {}).get("workflow_steps") or [])
    cur = _normalized_current_node_ids(pd)

    if completed:
        lines.append(f"Completed nodes: {_fmt_nodes(completed)}.")
    _append_status_timeline_lines(lines, status=status, pd=pd, eng=eng)
    retry_tid = _append_retry_timeline_lines(lines, status=status, pd=pd)
    _append_join_wait_timeline_lines(lines, status=status, eng=eng)
    _append_boundary_timeline_lines(lines, eng)
    _append_intermediate_timeline_lines(lines, eng)
    _append_subprocess_timeline_lines(lines, status=status, eng=eng)
    _append_current_focus_timeline_lines(lines, status=status, cur=cur, retry_tid=retry_tid)
    _append_terminal_timeline_lines(lines, status=status, pd=pd)

    return lines


def _build_retry_block(
    out: dict[str, Any], *, status: str, pd: dict[str, Any], eng: dict[str, Any]
) -> None:
    if status != "running" or not pd.get("retrying_task_id"):
        return
    tid = pd.get("retrying_task_id")
    att = pd.get("retry_attempt")
    mx = pd.get("bpmn_max_task_retries")
    lre = (
        eng.get("last_retryable_error") if isinstance(eng.get("last_retryable_error"), dict) else {}
    )
    msg = lre.get("message") or lre.get("Message") or ""
    out["retry_block"] = {
        "task_id": tid,
        "attempt": att,
        "max_extra_retries": mx,
        "last_error": str(msg) if msg else None,
    }
    total = (int(mx) + 1) if mx is not None else None
    if att is not None and total:
        out["headline"] = f"Retrying task {tid} (attempt {att} of up to {total})"
    else:
        out["headline"] = f"Retrying task {tid}"
    out["primary_state_label"] = "Retrying after transient failure"


def _build_join_block(out: dict[str, Any], *, status: str, eng: dict[str, Any]) -> dict[str, Any]:
    pj = eng.get("pending_joins") if isinstance(eng.get("pending_joins"), dict) else {}
    if not pj:
        return {}
    summaries = []
    for jid, info in sorted(pj.items()):
        if isinstance(info, dict):
            arr = info.get("arrived_branch_ids") or []
            exp = info.get("expected_branch_ids") or []
            na = len(arr) if isinstance(arr, list) else 0
            ne = len(exp) if isinstance(exp, list) else 0
            summaries.append(f"{jid}: {na}/{ne} branches at join")
    out["join_block"] = "; ".join(summaries) if summaries else None
    if not out.get("headline") and status in {"running", "waiting_for_task"}:
        out["headline"] = "Waiting for parallel branches at join"
        out["primary_state_label"] = "Waiting at parallel join"
    return pj


def _terminal_lines_for_cancelled(pd: dict[str, Any], pj: dict[str, Any]) -> str | None:
    tb = []
    if pd.get("last_successful_node_id"):
        tb.append(f"Last successful node: {pd.get('last_successful_node_id')}")
    if pd.get("cancelled_at"):
        tb.append(f"Cancelled at: {pd.get('cancelled_at')}")
    cur = pd.get("current_node_ids") or []
    if isinstance(cur, list) and cur:
        tb.append(f"Active nodes when stopped: {_fmt_nodes(cur)}")
    if pj:
        tb.append(f"Open joins: {', '.join(sorted(pj.keys()))}")
    return "\n".join(tb) if tb else None


def _append_timeout_terminal_lines(tb: list[str], pd: dict[str, Any]) -> None:
    if pd.get("timeout_seconds") is not None:
        tb.append(f"Timeout limit: {pd.get('timeout_seconds')} seconds")
    if pd.get("timed_out_at"):
        tb.append(f"Timed out at: {pd.get('timed_out_at')}")


def _append_retry_exhausted_terminal_lines(tb: list[str], pd: dict[str, Any]) -> None:
    meta = pd.get("condition_failure_metadata") or {}
    if not isinstance(meta, dict):
        return
    if meta.get("retry_attempts") is not None:
        tb.append(f"Retry attempts: {meta.get('retry_attempts')}")
    if meta.get("branch_id"):
        tb.append(f"Branch: {meta.get('branch_id')}")
    if meta.get("last_error"):
        tb.append(f"Last error: {meta.get('last_error')}")


def _terminal_lines_for_failed(
    pd: dict[str, Any], pj: dict[str, Any], *, reason: str | None
) -> tuple[str | None, bool]:
    tb = []
    if pd.get("failed_node_id"):
        tb.append(f"Failed node: {pd.get('failed_node_id')}")
    if pd.get("last_successful_node_id"):
        tb.append(f"Last successful node: {pd.get('last_successful_node_id')}")
    if reason == "timeout":
        _append_timeout_terminal_lines(tb, pd)
    if reason == "retry_exhausted":
        _append_retry_exhausted_terminal_lines(tb, pd)
    if pj:
        tb.append(f"Open joins: {', '.join(sorted(pj.keys()))}")
    meta = pd.get("condition_failure_metadata")
    show_raw = (
        isinstance(meta, dict)
        and bool(meta)
        and reason
        not in (
            "retry_exhausted",
            "cancelled",
            "timeout",
        )
    )
    return ("\n".join(tb) if tb else None), show_raw


def _build_terminal_block(
    out: dict[str, Any], *, status: str, pd: dict[str, Any], pj: dict[str, Any], reason: str | None
) -> None:
    if status == "cancelled":
        out["failure_reason_label"] = failure_reason_operator_label("cancelled")
        out["headline"] = out["failure_reason_label"]
        out["primary_state_label"] = "Cancelled"
        out["terminal_block"] = _terminal_lines_for_cancelled(pd, pj)
        out["parallel_context"] = _parallel_failure_blurb(pd, "cancelled")
        return
    if status == "failed":
        out["failure_reason_label"] = failure_reason_operator_label(reason)
        out["headline"] = out["failure_reason_label"]
        out["primary_state_label"] = "Failed"
        term_block, show_raw = _terminal_lines_for_failed(pd, pj, reason=reason)
        out["terminal_block"] = term_block
        out["parallel_context"] = _parallel_failure_blurb(pd, reason or "")
        out["show_raw_metadata"] = show_raw
        return
    if status == "waiting_for_task" and not out.get("headline"):
        out["headline"] = "Waiting for human task"
        out["primary_state_label"] = "Paused for human input"
    elif status == "running" and not out.get("headline"):
        out["headline"] = "Run in progress"
        out["primary_state_label"] = "Running"
    elif status == "completed":
        out["headline"] = "Run completed"
        out["primary_state_label"] = "Completed"


def build_operator_diagnostics(progress_data: dict[str, Any] | None, status: str) -> dict[str, Any]:
    """
    Structured operator summary for templates.
    Keys: headline, primary_state_label, retry_block, join_block, terminal_block,
    parallel_context, timeline_lines, failure_reason_label, show_raw_metadata.
    """
    out: dict[str, Any] = {
        "headline": None,
        "primary_state_label": None,
        "retry_block": None,
        "join_block": None,
        "terminal_block": None,
        "parallel_context": None,
        "timeline_lines": build_operator_timeline_lines(status, progress_data),
        "failure_reason_label": None,
        "show_raw_metadata": False,
    }
    if not progress_data:
        if status == "completed":
            out["headline"] = "Run completed"
            out["primary_state_label"] = "Completed"
        return out

    pd = progress_data
    eng = pd.get("engine_state") if isinstance(pd.get("engine_state"), dict) else {}
    reason = pd.get("failure_reason")
    _build_retry_block(out, status=status, pd=pd, eng=eng)
    pj = _build_join_block(out, status=status, eng=eng)
    _build_terminal_block(out, status=status, pd=pd, pj=pj, reason=reason)

    return out


def _parallel_failure_blurb(pd: dict[str, Any], reason: str) -> str | None:
    eng = pd.get("engine_state") if isinstance(pd.get("engine_state"), dict) else {}
    pj = eng.get("pending_joins") if isinstance(eng.get("pending_joins"), dict) else {}
    if not pj:
        return None
    jids = ", ".join(sorted(pj.keys()))
    if reason in ("cancelled", "timeout"):
        return f"Parallel run stopped while branch(es) were waiting at join(s): {jids}."
    return f"Failure with parallel state at join(s): {jids}."


def is_bpmn_operator_view(
    *,
    diagram_bpmn_xml: bool,
    progress_data: dict[str, Any] | None,
) -> bool:
    """True when run should show BPMN operator diagnostics (not legacy non-BPMN)."""
    if diagram_bpmn_xml:
        return True
    if not progress_data or not isinstance(progress_data, dict):
        return False
    if progress_data.get("engine_state") is not None:
        return True
    if progress_data.get("completed_node_ids"):
        return True
    if progress_data.get("current_node_ids"):
        return True
    return progress_data.get("failure_reason") in (
        "cancelled",
        "timeout",
        "retry_exhausted",
        "join_correlation_failed",
        "invalid_gateway",
    )


def build_bpmn_task_run_context(
    progress_data: dict[str, Any] | None,
    status: str,
    run_id: str,
) -> dict[str, Any] | None:
    """Slim context for task detail when run is BPMN and active."""
    if status not in ("waiting_for_task", "running") or not progress_data:
        return None
    pd = progress_data
    if not (
        pd.get("engine_state")
        or pd.get("next_step")
        or pd.get("current_node_ids")
        or pd.get("completed_node_ids")
    ):
        return None
    eng = pd.get("engine_state") if isinstance(pd.get("engine_state"), dict) else {}
    pj = eng.get("pending_joins") if isinstance(eng.get("pending_joins"), dict) else {}
    join_line = None
    if pj:
        parts = []
        for jid, info in sorted(pj.items()):
            if isinstance(info, dict):
                arr = info.get("arrived_branch_ids") or []
                exp = info.get("expected_branch_ids") or []
                na, ne = (
                    (len(arr), len(exp))
                    if isinstance(arr, list) and isinstance(exp, list)
                    else (0, 0)
                )
                parts.append(f"{jid} ({na}/{ne})")
        join_line = "Waiting at join: " + "; ".join(parts) if parts else None

    cur = _normalized_current_node_ids(pd)

    return {
        "run_id": run_id,
        "next_step": pd.get("next_step"),
        "current_node_ids": cur,
        "current_nodes_display": _fmt_nodes(cur),
        "join_summary": join_line,
        "retrying_task_id": pd.get("retrying_task_id") if status == "running" else None,
    }
