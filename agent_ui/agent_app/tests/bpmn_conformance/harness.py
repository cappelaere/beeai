"""Run validation and execution conformance fixtures."""

from __future__ import annotations

import asyncio
from typing import Any

from agent_app.bpmn_engine import BpmnEngineError, normalize_engine_state, run_bpmn_workflow
from agent_app.task_service import BpmnRetryableTaskError, TaskPendingException
from agent_app.tests.bpmn_conformance.schema import (
    ExecutionFixture,
    ValidationFixture,
)
from agent_app.workflow_context import normalize_bindings, validate_bpmn_for_save


def run_validation_fixture(f: ValidationFixture) -> None:
    errs = validate_bpmn_for_save(f.bpmn, f.bindings)
    joined = " ".join(errs).lower()
    assert errs, f"{f.id}: expected validation errors, got []"
    for sub in f.expect_error_substrings:
        assert sub.lower() in joined, f"{f.id}: missing substring {sub!r} in {errs}"


def _make_handler(
    behavior: str,
    task_id: str,
    counters: dict[str, int],
    pause_next: str | None,
    task_id_for_pause: str | None,
):
    # Bound as executor instance methods: first arg is self (see run_bpmn_workflow getattr + call).
    async def _fn(self, state: Any):
        if behavior == "ok":
            return None
        if behavior == "retryable_once":
            k = task_id
            counters[k] = counters.get(k, 0) + 1
            if counters[k] == 1:
                raise BpmnRetryableTaskError(f"retry_{task_id}")
            return None
        if behavior == "retry_always":
            raise BpmnRetryableTaskError(f"always_{task_id}")
        if behavior == "fail_runtime":
            raise RuntimeError(f"fail_{task_id}")
        if behavior == "pause_human":
            if task_id == task_id_for_pause:
                raise TaskPendingException(
                    f"ht_{task_id}", "human_task", state, pause_next or task_id
                )
            return None
        raise ValueError(f"unknown behavior {behavior}")

    return _fn


def _build_executor(
    f: ExecutionFixture,
    bindings: dict[str, Any],
    *,
    pause_task_id: str | None = None,
):
    counters: dict[str, int] = {}
    st_map = f.bindings_raw.get("serviceTasks") or {}
    methods: dict[str, Any] = {}

    for task_el_id, behavior in f.behaviors.items():
        spec = st_map.get(task_el_id) or {}
        hname = (spec.get("handler") or "").strip()
        if not hname:
            raise ValueError(f"{f.id}: no handler for {task_el_id}")
        methods[hname] = _make_handler(
            behavior,
            task_el_id,
            counters,
            f.pause_next_step,
            pause_task_id,
        )

    return type("ConfEx", (), methods)()


def run_execution_fixture(f: ExecutionFixture) -> Any:
    bindings = normalize_bindings(
        dict(f.bindings_raw),
        workflow_id=f.bindings_raw.get("workflow_id", "conf_test"),
        executor=f.bindings_raw.get("executor", "conf.Executor"),
    )
    state = f.state_factory()
    ex = _build_executor(
        f,
        bindings,
        pause_task_id=f.pause_at_element_id,
    )
    check_idx = [0]

    async def execution_check():
        seq = f.execution_check_returns
        i = check_idx[0]
        check_idx[0] += 1
        if i < len(seq):
            return seq[i]
        return None

    ec = execution_check if f.execution_check_returns else None

    async def _run(start_from=None):
        return await run_bpmn_workflow(
            ex,
            state,
            f.bpmn,
            bindings,
            start_from_task_id=start_from,
            execution_check=ec,
            max_task_retries=f.max_task_retries,
        )

    if f.expect.outcome == "task_pending":
        with _expect_raises(TaskPendingException):
            asyncio.run(_run())
        eng = normalize_engine_state(getattr(state, "_bpmn_engine_state", None))
        assert f.pause_next_step, f.id
        asyncio.run(_run(start_from=f.pause_next_step))
        _assert_expect_complete(state, f, phase2=True)
        return state

    if f.expect.outcome == "bpmn_engine_error":
        with _expect_raises(BpmnEngineError) as ctx:
            asyncio.run(_run())
        _assert_engine_error(ctx.exception, f)
        return ctx.exception

    asyncio.run(_run())
    _assert_expect_complete(state, f)
    return state


def _expect_raises(exc_type):
    class Ctx:
        exception = None

        def __enter__(self):
            return self

        def __exit__(self, et, ev, tb):
            if et is None:
                raise AssertionError(f"expected {exc_type.__name__}")
            if not issubclass(et, exc_type):
                return False
            self.exception = ev
            return True

    return Ctx()


def _assert_engine_error(e: BpmnEngineError, f: ExecutionFixture) -> None:
    exp = f.expect
    if exp.failure_reason:
        assert e.failure_reason == exp.failure_reason, (f.id, e.failure_reason)
    if exp.failed_node_id is not None:
        assert e.failed_node_id == exp.failed_node_id, (f.id, e.failed_node_id)
    eng = getattr(e.state, "_bpmn_engine_state", None) or {}
    if exp.pending_join_ids is not None:
        pj = eng.get("pending_joins") or {}
        for jid in exp.pending_join_ids:
            assert jid in pj, f"{f.id}: missing join {jid} in {pj}"
    if exp.min_active_tokens is not None:
        toks = eng.get("active_tokens") or []
        assert len(toks) >= exp.min_active_tokens, (f.id, toks)
    meta = e.condition_failure_metadata or {}
    if exp.retry_attempts is not None:
        assert meta.get("retry_attempts") == exp.retry_attempts, (f.id, meta)


def _assert_expect_complete(state: Any, f: ExecutionFixture, phase2: bool = False) -> None:
    exp = f.expect
    steps = list(getattr(state, "workflow_steps", []) or [])
    for node in exp.completed_contains:
        assert node in steps, f"{f.id}: missing completed {node} in {steps}"
    if exp.completed_ordered_suffix:
        suf = exp.completed_ordered_suffix
        assert tuple(steps[-len(suf) :]) == suf, f"{f.id}: steps={steps} want suffix {suf}"
    eng = normalize_engine_state(getattr(state, "_bpmn_engine_state", None))
    if exp.pending_join_ids is not None and not phase2:
        pj = eng.get("pending_joins") or {}
        for jid in exp.pending_join_ids:
            assert jid in pj, f"{f.id}: {pj}"
    if f.expect.outcome == "complete" or phase2:
        assert not (eng.get("pending_joins")), f"{f.id}: pending_joins should drain: {eng}"


def run_pause_resume_fixture(f: ExecutionFixture) -> Any:
    assert f.expect.outcome == "task_pending"
    return run_execution_fixture(f)
