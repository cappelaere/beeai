"""Unit tests for BPMN workflow engine (run_bpmn_workflow and helpers)."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from django.test import TestCase

from agent_app.bpmn_engine import (
    BpmnEngineError,
    can_run_with_bpmn_engine,
    create_initial_state_from_inputs,  # noqa: F401
    current_node_ids_for_progress,
    evaluate_condition,
    get_next_step_for_resume,
    normalize_engine_state,
    run_bpmn_workflow,
)
from agent_app.task_service import (
    BpmnModeledBoundaryError,
    BpmnRetryableTaskError,
    TaskPendingError,
)
from agent_app.tests.bpmn_conformance.fixtures.registry import (
    _BIND_EXCLUSIVE,
    _BIND_FJ,
    _BIND_LINEAR,
    _bpmn_exclusive,
    _bpmn_fork_join_downstream,
    _bpmn_linear,
)
from agent_app.workflow_context import (
    get_first_task_id,
    get_next_task_id,
    normalize_bindings,
    validate_exclusive_gateway_semantics,
)


def _state(**kwargs):
    s = SimpleNamespace(workflow_steps=[], **kwargs)
    return s


def _nb(raw: dict) -> dict:
    return normalize_bindings(
        dict(raw),
        workflow_id=raw.get("workflow_id", "t"),
        executor=raw.get("executor", "x.Executor"),
    )


class _ParallelJoinResumeExecutor:
    def __init__(self, b_calls: list[int], *, pause_on_first_b: bool = False):
        self._b_calls = b_calls
        self._pause_on_first_b = pause_on_first_b

    async def task0(self, s):
        return None

    async def task_a(self, s):
        return None

    async def task_b(self, s):
        self._b_calls[0] += 1
        if self._pause_on_first_b and self._b_calls[0] == 1:
            raise TaskPendingError("h", "human", s, "taskB")
        return

    async def task_after(self, s):
        return None


class FirstTaskDetectionTests(TestCase):
    @patch("agent_app.bpmn_engine.get_workflow_context")
    def test_can_run_true_when_bpmn_bindings_and_state_class(self, mock_ctx):
        mock_ctx.return_value = {
            "bpmn": _bpmn_linear(),
            "bindings": {"serviceTasks": {"t1": {"handler": "h1"}, "t2": {"handler": "h2"}}},
            "code": {"state_class_name": "SomeState"},
        }
        self.assertTrue(can_run_with_bpmn_engine("wf1"))

    @patch("agent_app.bpmn_engine.get_workflow_context")
    def test_can_run_false_when_first_task_missing_from_bindings(self, mock_ctx):
        mock_ctx.return_value = {
            "bpmn": _bpmn_linear(),
            "bindings": {"serviceTasks": {"t2": {"handler": "h2"}}},
            "code": {"state_class_name": "SomeState"},
        }
        self.assertFalse(can_run_with_bpmn_engine("wf1"))

    @patch("agent_app.bpmn_engine.get_workflow_context")
    def test_can_run_false_when_no_state_class(self, mock_ctx):
        mock_ctx.return_value = {
            "bpmn": _bpmn_linear(),
            "bindings": {"serviceTasks": {"t1": {"handler": "h1"}}},
            "code": {},
        }
        self.assertFalse(can_run_with_bpmn_engine("wf1"))

    @patch("agent_app.bpmn_engine.get_workflow_context")
    def test_can_run_false_when_empty_service_tasks(self, mock_ctx):
        mock_ctx.return_value = {
            "bpmn": _bpmn_linear(),
            "bindings": {"serviceTasks": {}},
            "code": {"state_class_name": "SomeState"},
        }
        self.assertFalse(can_run_with_bpmn_engine("wf1"))


class NextTaskTraversalTests(TestCase):
    def test_get_first_task_id_returns_first_service_task(self):
        self.assertEqual(get_first_task_id(_bpmn_linear()), "t1")

    def test_get_next_task_id_returns_next_then_none(self):
        bpmn = _bpmn_linear()
        self.assertEqual(get_next_task_id(bpmn, "t1"), "t2")
        self.assertIsNone(get_next_task_id(bpmn, "t2"))


class RunBpmnWorkflowMissingBindingTests(TestCase):
    def test_missing_binding_raises_value_error(self):
        bpmn = _bpmn_linear()
        bindings = _nb(
            {
                "workflow_id": "x",
                "executor": "E",
                "serviceTasks": {"t1": {"handler": "h1"}},
            }
        )

        class Ex:
            async def h1(self, state):
                return None

        async def run():
            return await run_bpmn_workflow(Ex(), _state(), bpmn, bindings)

        with self.assertRaises(BpmnEngineError) as ctx:
            asyncio.run(run())
        self.assertEqual(ctx.exception.failure_reason, "missing_binding")
        self.assertEqual(ctx.exception.failed_node_id, "t2")

    def test_missing_handler_on_executor_raises_value_error(self):
        bpmn = _bpmn_linear()
        bindings = _nb(_BIND_LINEAR)

        class Ex:
            async def h1(self, state):
                return None

        Ex.h2 = None

        async def run():
            return await run_bpmn_workflow(Ex(), _state(), bpmn, bindings)

        with self.assertRaises(BpmnEngineError) as ctx:
            asyncio.run(run())
        self.assertEqual(ctx.exception.failure_reason, "missing_handler")
        self.assertEqual(ctx.exception.failed_node_id, "t2")


class PauseResumeTests(TestCase):
    def test_pause_sets_next_step_for_resume(self):
        bpmn = _bpmn_linear()
        bindings = _nb(_BIND_LINEAR)

        class Ex:
            async def h1(self, state):
                raise TaskPendingError("tid", "t", state, "t2")

            async def h2(self, state):
                return None

        st = _state()

        async def run():
            await run_bpmn_workflow(Ex(), st, bpmn, bindings)

        with self.assertRaises(TaskPendingError):
            asyncio.run(run())
        self.assertEqual(get_next_step_for_resume(st), "t2")

    def test_resume_from_task_id_runs_next_handler(self):
        bpmn = _bpmn_linear()
        bindings = _nb(_BIND_LINEAR)
        calls: list[str] = []

        class Ex:
            async def h1(self, state):
                calls.append("h1")
                return

            async def h2(self, state):
                calls.append("h2")
                return

        st = _state()

        async def run():
            await run_bpmn_workflow(Ex(), st, bpmn, bindings, start_from_task_id="t2")

        asyncio.run(run())
        self.assertEqual(calls, ["h2"])


class CurrentNodeIdsForProgressTests(TestCase):
    def test_two_active_tokens(self):
        eng = normalize_engine_state(
            {
                "active_tokens": [
                    {"current_element_id": "a", "branch_id": "b1"},
                    {"current_element_id": "b", "branch_id": "b2"},
                ]
            }
        )
        self.assertEqual(current_node_ids_for_progress(eng), ["a", "b"])

    def test_fallback_when_empty_tokens(self):
        eng = normalize_engine_state({"current_node_ids": ["x"], "active_tokens": []})
        self.assertEqual(current_node_ids_for_progress(eng), ["x"])

    def test_none_state(self):
        self.assertEqual(current_node_ids_for_progress(None), [])


class ValidateExclusiveGatewaySemanticsTests(TestCase):
    def test_multiple_outgoing_no_condition_no_default_errors(self):
        bpmn = {
            "elements": {
                "gw": {
                    "type": "exclusiveGateway",
                    "outgoing_flow_ids": ["f1", "f2"],
                    "outgoing": ["a", "b"],
                }
            },
            "sequence_flows": {"f1": {"condition": ""}, "f2": {"condition": ""}},
        }
        errs = validate_exclusive_gateway_semantics(bpmn)
        self.assertTrue(any("no conditions and no default" in e for e in errs))

    def test_nested_attr_condition_rejected(self):
        bpmn = {
            "elements": {
                "gw": {
                    "type": "exclusiveGateway",
                    "outgoing_flow_ids": ["f1", "f2"],
                    "outgoing": ["a", "b"],
                    "default_flow_id": "f1",
                }
            },
            "sequence_flows": {
                "f1": {"condition": "state.x == 1"},
                "f2": {"condition": "state.nested.x == 1"},
            },
        }
        errs = validate_exclusive_gateway_semantics(bpmn)
        self.assertTrue(any("unparsable" in e.lower() for e in errs))


class EngineStateTests(TestCase):
    def test_linear_flow_initializes_and_updates_engine_state(self):
        bpmn = _bpmn_linear()
        bindings = _nb(_BIND_LINEAR)

        class Ex:
            async def h1(self, state):
                return None

            async def h2(self, state):
                return None

        st = _state()

        async def run():
            await run_bpmn_workflow(Ex(), st, bpmn, bindings)

        asyncio.run(run())
        eng = getattr(st, "_bpmn_engine_state", {})
        self.assertIn("t1", eng.get("completed_node_ids", []))
        self.assertIn("t2", eng.get("completed_node_ids", []))

    def test_pause_resume_preserves_token_state(self):
        bpmn = _bpmn_linear()
        bindings = _nb(_BIND_LINEAR)

        class Ex:
            async def h1(self, state):
                raise TaskPendingError("x", "human", state, "t1")

            async def h2(self, state):
                return None

        st = _state()

        async def run1():
            await run_bpmn_workflow(Ex(), st, bpmn, bindings)

        with self.assertRaises(TaskPendingError):
            asyncio.run(run1())
        eng1 = normalize_engine_state(dict(getattr(st, "_bpmn_engine_state", {})))
        self.assertIn("t1", eng1.get("completed_node_ids", []))

        class Ex2:
            async def h1(self, state):
                return None

            async def h2(self, state):
                return None

        st.__dict__["_bpmn_engine_state"] = eng1

        async def run2():
            await run_bpmn_workflow(Ex2(), st, bpmn, bindings, start_from_task_id="t1")

        asyncio.run(run2())
        # Paused before t1 was appended to workflow_steps; resume continues from t1 so only
        # post-pause completions appear in workflow_steps (t2 after t1's handler returns).
        self.assertEqual(getattr(st, "workflow_steps", []), ["t2"])
        eng2 = normalize_engine_state(dict(getattr(st, "_bpmn_engine_state", {})))
        self.assertIn("t1", eng2.get("completed_node_ids", []))
        self.assertIn("t2", eng2.get("completed_node_ids", []))


class ExclusiveGatewayTests(TestCase):
    def test_exclusive_gateway_chooses_branch_a(self):
        bpmn = _bpmn_exclusive()
        bindings = _nb(_BIND_EXCLUSIVE)

        class Ex:
            async def task1(self, state):
                return None

            async def task_a(self, state):
                return None

            async def task_b(self, state):
                return None

        st = _state()
        st.x = 1

        async def run():
            await run_bpmn_workflow(Ex(), st, bpmn, bindings)

        asyncio.run(run())
        self.assertEqual(st.workflow_steps, ["task1", "task_a"])

    def test_exclusive_gateway_chooses_branch_b(self):
        bpmn = _bpmn_exclusive()
        bindings = _nb(_BIND_EXCLUSIVE)

        class Ex:
            async def task1(self, state):
                return None

            async def task_a(self, state):
                return None

            async def task_b(self, state):
                return None

        st = _state()
        st.x = 2

        async def run():
            await run_bpmn_workflow(Ex(), st, bpmn, bindings)

        asyncio.run(run())
        self.assertEqual(st.workflow_steps, ["task1", "task_b"])

    def test_exclusive_gateway_no_match_uses_default(self):
        bpmn = {
            "elements": {
                "start": {
                    "type": "startEvent",
                    "outgoing": ["t1"],
                    "outgoing_flow_ids": ["s0"],
                },
                "t1": {
                    "type": "serviceTask",
                    "outgoing": ["gw"],
                    "outgoing_flow_ids": ["f0"],
                },
                "gw": {
                    "type": "exclusiveGateway",
                    "incoming": ["t1"],
                    "outgoing": ["ta", "tb"],
                    "outgoing_flow_ids": ["fa", "fb"],
                    "default_flow_id": "fb",
                },
                "ta": {
                    "type": "serviceTask",
                    "outgoing": ["end"],
                    "outgoing_flow_ids": ["f2"],
                },
                "tb": {
                    "type": "serviceTask",
                    "outgoing": ["end"],
                    "outgoing_flow_ids": ["f3"],
                },
                "end": {"type": "endEvent", "outgoing": []},
            },
            "sequence_flows": {
                "s0": {},
                "f0": {},
                "fa": {"condition": "state.x == 99"},
                "fb": {"condition": ""},
                "f2": {},
                "f3": {},
            },
            "ordered_element_ids": ["start", "t1", "gw", "ta", "tb", "end"],
        }
        bindings = _nb(
            {
                "workflow_id": "exd",
                "executor": "E",
                "serviceTasks": {
                    "t1": {"handler": "t1"},
                    "ta": {"handler": "ta"},
                    "tb": {"handler": "tb"},
                },
            }
        )

        class Ex:
            async def t1(self, state):
                return None

            async def ta(self, state):
                return None

            async def tb(self, state):
                return None

        st = _state()
        st.x = 0

        async def run():
            await run_bpmn_workflow(Ex(), st, bpmn, bindings)

        asyncio.run(run())
        self.assertIn("tb", st.workflow_steps)
        self.assertNotIn("ta", st.workflow_steps)

    def test_exclusive_gateway_no_match_no_default_fails(self):
        bpmn = _bpmn_exclusive()
        bindings = _nb(_BIND_EXCLUSIVE)

        class Ex:
            async def task1(self, state):
                return None

            async def task_a(self, state):
                return None

            async def task_b(self, state):
                return None

        st = _state()
        st.x = 3

        async def run():
            await run_bpmn_workflow(Ex(), st, bpmn, bindings)

        with self.assertRaises(BpmnEngineError) as ctx:
            asyncio.run(run())
        self.assertEqual(ctx.exception.failure_reason, "invalid_gateway")


class ParallelForkExecutionTests(TestCase):
    def test_parallel_fork_creates_multiple_active_tokens(self):
        bpmn = _bpmn_fork_join_downstream()
        bindings = _nb(_BIND_FJ)

        class Ex:
            async def task0(self, s):
                return None

            async def task_a(self, s):
                return None

            async def task_b(self, s):
                return None

            async def task_after(self, s):
                return None

        st = _state()
        steps: list[str] = []

        async def send(typ, payload):
            if typ == "step":
                steps.append(payload)
            if typ == "progress" and "engine_state" in payload:
                es = payload["engine_state"]
                toks = es.get("active_tokens") or []
                if len(toks) == 2 and all(
                    t.get("current_element_id") in ("taskA", "taskB") for t in toks
                ):
                    send.seen_parallel = True

        send.seen_parallel = False

        async def run():
            await run_bpmn_workflow(Ex(), st, bpmn, bindings, send_message=send)

        asyncio.run(run())
        self.assertTrue(getattr(send, "seen_parallel", False))

    def test_parallel_fork_executes_branches_in_flow_order(self):
        bpmn = _bpmn_fork_join_downstream()
        bindings = _nb(_BIND_FJ)
        steps: list[str] = []

        class Ex:
            async def task0(self, s):
                return None

            async def task_a(self, s):
                return None

            async def task_b(self, s):
                return None

            async def task_after(self, s):
                return None

        async def send(typ, payload):
            if typ == "step":
                steps.append(payload)

        st = _state()

        async def run():
            await run_bpmn_workflow(Ex(), st, bpmn, bindings, send_message=send)

        asyncio.run(run())
        i0 = steps.index("task0")
        ia = steps.index("taskA")
        ib = steps.index("taskB")
        self.assertLess(i0, ia)
        self.assertLess(ia, ib)

    def test_parallel_branch_completion_removes_only_finished_token(self):
        bpmn = _bpmn_fork_join_downstream()
        bindings = _nb(_BIND_FJ)

        class Ex:
            async def task0(self, s):
                return None

            async def task_a(self, s):
                return None

            async def task_b(self, s):
                return None

            async def task_after(self, s):
                return None

        st = _state()

        async def run():
            await run_bpmn_workflow(Ex(), st, bpmn, bindings)

        asyncio.run(run())
        eng = getattr(st, "_bpmn_engine_state", {})
        self.assertEqual(len(eng.get("active_tokens") or []), 0)

    def test_parallel_branch_pause_preserves_other_active_tokens(self):
        bpmn = _bpmn_fork_join_downstream()
        bindings = _nb(_BIND_FJ)

        class Ex:
            async def task0(self, s):
                return None

            async def task_a(self, s):
                return None

            async def task_b(self, s):
                raise TaskPendingError("h", "human", s, "taskB")

            async def task_after(self, s):
                return None

        st = _state()

        async def run():
            await run_bpmn_workflow(Ex(), st, bpmn, bindings)

        with self.assertRaises(TaskPendingError):
            asyncio.run(run())
        eng = normalize_engine_state(dict(getattr(st, "_bpmn_engine_state", {})))
        ids = {t.get("current_element_id") for t in eng.get("active_tokens") or []}
        self.assertIn("joinGW", ids)
        self.assertIn("taskB", ids)

    def test_parallel_branch_failure_surfaces_failed_node_and_engine_state(self):
        bpmn = _bpmn_fork_join_downstream()
        bindings = _nb(_BIND_FJ)

        class Ex:
            async def task0(self, s):
                return None

            async def task_a(self, s):
                return None

            async def task_b(self, s):
                raise RuntimeError("branch_boom")

            async def task_after(self, s):
                return None

        st = _state()

        async def run():
            await run_bpmn_workflow(Ex(), st, bpmn, bindings)

        with self.assertRaises(BpmnEngineError) as ctx:
            asyncio.run(run())
        self.assertEqual(ctx.exception.failed_node_id, "taskB")
        eng = getattr(st, "_bpmn_engine_state", {})
        self.assertIn("joinGW", eng.get("pending_joins", {}))

    def test_bpmn_cancel_during_linear_two_step(self):
        bpmn = _bpmn_linear()
        bindings = _nb(_BIND_LINEAR)
        n = [0]

        class Ex:
            async def h1(self, s):
                return None

            async def h2(self, s):
                return None

        async def chk():
            n[0] += 1
            return "cancelled" if n[0] >= 2 else None

        async def run():
            await run_bpmn_workflow(Ex(), _state(), bpmn, bindings, execution_check=chk)

        with self.assertRaises(BpmnEngineError) as e:
            asyncio.run(run())
        self.assertEqual(e.exception.failure_reason, "cancelled")

    def test_bpmn_cancelled_run_preserves_active_tokens(self):
        bpmn = _bpmn_fork_join_downstream()
        bindings = _nb(_BIND_FJ)
        k = [0]

        class Ex:
            async def task0(self, s):
                return None

            async def task_a(self, s):
                return None

            async def task_b(self, s):
                return None

            async def task_after(self, s):
                return None

        async def chk():
            k[0] += 1
            return "cancelled" if k[0] >= 2 else None

        st = _state()

        async def run():
            await run_bpmn_workflow(Ex(), st, bpmn, bindings, execution_check=chk)

        with self.assertRaises(BpmnEngineError):
            asyncio.run(run())
        eng = getattr(st, "_bpmn_engine_state", {})
        self.assertGreaterEqual(len(eng.get("active_tokens") or []), 1)

    def test_bpmn_timeout_preserves_pending_joins(self):
        bpmn = _bpmn_fork_join_downstream()
        bindings = _nb(_BIND_FJ)
        k = [0]

        class Ex:
            async def task0(self, s):
                return None

            async def task_a(self, s):
                return None

            async def task_b(self, s):
                return None

            async def task_after(self, s):
                return None

        async def chk():
            k[0] += 1
            return "timeout" if k[0] >= 2 else None

        st = _state()

        async def run():
            await run_bpmn_workflow(Ex(), st, bpmn, bindings, execution_check=chk)

        with self.assertRaises(BpmnEngineError) as e:
            asyncio.run(run())
        self.assertEqual(e.exception.failure_reason, "timeout")
        eng = getattr(st, "_bpmn_engine_state", {})
        self.assertIn("joinGW", eng.get("pending_joins", {}))


class ParallelJoinExecutionTests(TestCase):
    def test_parallel_join_waits_for_all_branches(self):
        """Both branches must complete before taskAfter; step order reflects fork order."""
        bpmn = _bpmn_fork_join_downstream()
        bindings = _nb(_BIND_FJ)
        steps: list[str] = []

        class Ex:
            async def task0(self, s):
                return None

            async def task_a(self, s):
                return None

            async def task_b(self, s):
                return None

            async def task_after(self, s):
                return None

        async def send(typ, p):
            if typ == "step":
                steps.append(p)

        st = _state()
        asyncio.run(run_bpmn_workflow(Ex(), st, bpmn, bindings, send_message=send))
        self.assertIn("taskAfter", st.workflow_steps)
        ia, ib = steps.index("taskA"), steps.index("taskB")
        iafter = steps.index("taskAfter")
        self.assertLess(max(ia, ib), iafter)

    def test_parallel_join_merges_to_single_downstream_token(self):
        bpmn = _bpmn_fork_join_downstream()
        bindings = _nb(_BIND_FJ)

        class Ex:
            async def task0(self, s):
                return None

            async def task_a(self, s):
                return None

            async def task_b(self, s):
                return None

            async def task_after(self, s):
                return None

        st = _state()

        async def run():
            await run_bpmn_workflow(Ex(), st, bpmn, bindings)

        asyncio.run(run())
        eng = getattr(st, "_bpmn_engine_state", {})
        self.assertIn("joinGW", eng.get("completed_node_ids", []))

    def test_parallel_join_clears_pending_join_state(self):
        bpmn = _bpmn_fork_join_downstream()
        bindings = _nb(_BIND_FJ)

        class Ex:
            async def task0(self, s):
                return None

            async def task_a(self, s):
                return None

            async def task_b(self, s):
                return None

            async def task_after(self, s):
                return None

        st = _state()

        async def run():
            await run_bpmn_workflow(Ex(), st, bpmn, bindings)

        asyncio.run(run())
        eng = getattr(st, "_bpmn_engine_state", {})
        self.assertEqual(eng.get("pending_joins"), {})

    def test_parallel_join_multi_task_branch_paths_complete(self):
        bpmn = {
            "elements": {
                "start": {
                    "type": "startEvent",
                    "outgoing": ["task0"],
                    "outgoing_flow_ids": ["s0"],
                },
                "task0": {
                    "type": "serviceTask",
                    "outgoing": ["forkGW"],
                    "outgoing_flow_ids": ["t0"],
                },
                "forkGW": {
                    "type": "parallelGateway",
                    "incoming": ["task0"],
                    "outgoing": ["taskA1", "taskB1"],
                    "outgoing_flow_ids": ["ffa", "ffb"],
                },
                "taskA1": {
                    "type": "serviceTask",
                    "outgoing": ["taskA2"],
                    "outgoing_flow_ids": ["fa1"],
                },
                "taskA2": {
                    "type": "serviceTask",
                    "outgoing": ["joinGW"],
                    "outgoing_flow_ids": ["fa2"],
                },
                "taskB1": {
                    "type": "serviceTask",
                    "outgoing": ["joinGW"],
                    "outgoing_flow_ids": ["fb1"],
                },
                "joinGW": {
                    "type": "parallelGateway",
                    "incoming": ["taskA2", "taskB1"],
                    "outgoing": ["taskAfter"],
                    "outgoing_flow_ids": ["jc"],
                },
                "taskAfter": {
                    "type": "serviceTask",
                    "outgoing": ["end"],
                    "outgoing_flow_ids": ["jd"],
                },
                "end": {"type": "endEvent", "outgoing": []},
            },
            "sequence_flows": {
                k: {} for k in ["s0", "t0", "ffa", "ffb", "fa1", "fa2", "fb1", "jc", "jd"]
            },
            "ordered_element_ids": [
                "start",
                "task0",
                "forkGW",
                "taskA1",
                "taskA2",
                "taskB1",
                "joinGW",
                "taskAfter",
                "end",
            ],
        }
        bindings = _nb(
            {
                "workflow_id": "mj",
                "executor": "E",
                "serviceTasks": {
                    "task0": {"handler": "task0"},
                    "taskA1": {"handler": "a1"},
                    "taskA2": {"handler": "a2"},
                    "taskB1": {"handler": "b1"},
                    "taskAfter": {"handler": "after"},
                },
            }
        )

        class Ex:
            async def task0(self, s):
                return None

            async def a1(self, s):
                return None

            async def a2(self, s):
                return None

            async def b1(self, s):
                return None

            async def after(self, s):
                return None

        st = _state()

        async def run():
            await run_bpmn_workflow(Ex(), st, bpmn, bindings)

        asyncio.run(run())
        self.assertIn("taskAfter", st.workflow_steps)

    def test_parallel_join_branch_failure_preserves_failure_metadata(self):
        bpmn = _bpmn_fork_join_downstream()
        bindings = _nb(_BIND_FJ)

        class Ex:
            async def task0(self, s):
                return None

            async def task_a(self, s):
                raise RuntimeError("a_fail")

            async def task_b(self, s):
                return None

            async def task_after(self, s):
                return None

        st = _state()

        async def run():
            await run_bpmn_workflow(Ex(), st, bpmn, bindings)

        with self.assertRaises(BpmnEngineError) as ctx:
            asyncio.run(run())
        self.assertEqual(ctx.exception.failed_node_id, "taskA")
        eng = getattr(ctx.exception.state, "_bpmn_engine_state", {})
        self.assertIsNotNone(eng.get("pending_joins"))

    def test_parallel_pause_before_join_keeps_token_on_task(self):
        bpmn = _bpmn_fork_join_downstream()
        bindings = _nb(_BIND_FJ)

        class Ex:
            async def task0(self, s):
                return None

            async def task_a(self, s):
                raise TaskPendingError("h", "human", s, "taskA")

            async def task_b(self, s):
                return None

            async def task_after(self, s):
                return None

        st = _state()

        async def run():
            await run_bpmn_workflow(Ex(), st, bpmn, bindings)

        with self.assertRaises(TaskPendingError):
            asyncio.run(run())
        eng = getattr(st, "_bpmn_engine_state", {})
        cur = current_node_ids_for_progress(eng)
        self.assertIn("taskA", cur)

    def test_parallel_join_resume_preserves_waiting_branches(self):
        bpmn = _bpmn_fork_join_downstream()
        bindings = _nb(_BIND_FJ)
        b_calls = [0]
        st = _state()

        async def run1():
            await run_bpmn_workflow(
                _ParallelJoinResumeExecutor(b_calls, pause_on_first_b=True), st, bpmn, bindings
            )

        with self.assertRaises(TaskPendingError):
            asyncio.run(run1())
        eng = normalize_engine_state(dict(getattr(st, "_bpmn_engine_state", {})))
        st.__dict__["_bpmn_engine_state"] = eng

        async def run2():
            await run_bpmn_workflow(
                _ParallelJoinResumeExecutor(b_calls), st, bpmn, bindings, start_from_task_id="taskB"
            )

        asyncio.run(run2())
        self.assertIn("taskAfter", st.workflow_steps)
        self.assertGreaterEqual(b_calls[0], 2)


class BoundaryTimerAndErrorTests(TestCase):
    def test_timer_boundary_routes_before_handler(self):
        bpmn = {
            "elements": {
                "start": {
                    "type": "startEvent",
                    "outgoing": ["tmain"],
                    "outgoing_flow_ids": ["s0"],
                },
                "tmain": {
                    "type": "serviceTask",
                    "outgoing": ["endm"],
                    "outgoing_flow_ids": ["fm"],
                },
                "trec": {
                    "type": "serviceTask",
                    "outgoing": ["tmain"],
                    "outgoing_flow_ids": ["fr"],
                },
                "endm": {"type": "endEvent", "outgoing": []},
            },
            "sequence_flows": {"s0": {}, "fm": {}, "fr": {}},
            "ordered_element_ids": ["start", "tmain", "trec", "endm"],
            "boundary_by_task": {
                "tmain": {
                    "timer": {
                        "boundary_id": "bt",
                        "target_element_id": "trec",
                        "duration_iso": "PT0.001S",
                    }
                }
            },
        }
        bindings = _nb(
            {
                "workflow_id": "bt",
                "executor": "E",
                "serviceTasks": {
                    "tmain": {"handler": "main"},
                    "trec": {"handler": "rec"},
                },
            }
        )
        calls: list[str] = []

        class Ex:
            async def main(self, s):
                calls.append("main")
                return

            async def rec(self, s):
                calls.append("rec")
                return

        tmono = [0.0]

        def _m():
            tmono[0] += 0.01
            return tmono[0]

        with patch("agent_app.bpmn_engine.time.monotonic", side_effect=_m):
            asyncio.run(run_bpmn_workflow(Ex(), _state(), bpmn, bindings))
        self.assertEqual(calls, ["rec", "main"])

    def test_error_boundary_routes_on_modeled_error(self):
        bpmn = {
            "elements": {
                "start": {
                    "type": "startEvent",
                    "outgoing": ["t1"],
                    "outgoing_flow_ids": ["s0"],
                },
                "t1": {
                    "type": "serviceTask",
                    "outgoing": ["endbad"],
                    "outgoing_flow_ids": ["f1"],
                },
                "tfix": {
                    "type": "serviceTask",
                    "outgoing": ["endok"],
                    "outgoing_flow_ids": ["f2"],
                },
                "endbad": {"type": "endEvent", "outgoing": []},
                "endok": {"type": "endEvent", "outgoing": []},
            },
            "sequence_flows": {"s0": {}, "f1": {}, "f2": {}},
            "ordered_element_ids": ["start", "t1", "tfix", "endbad", "endok"],
            "boundary_by_task": {
                "t1": {
                    "error": {
                        "boundary_id": "be",
                        "target_element_id": "tfix",
                    }
                }
            },
        }
        bindings = _nb(
            {
                "workflow_id": "eb",
                "executor": "E",
                "serviceTasks": {
                    "t1": {"handler": "h1"},
                    "tfix": {"handler": "hfix"},
                },
            }
        )

        class Ex:
            async def h1(self, s):
                raise BpmnModeledBoundaryError("modeled")

            async def hfix(self, s):
                return None

        st = _state()
        asyncio.run(run_bpmn_workflow(Ex(), st, bpmn, bindings))
        self.assertIn("tfix", st.workflow_steps)

    def test_modeled_error_without_boundary_fails(self):
        bpmn = _bpmn_linear()
        bindings = _nb(_BIND_LINEAR)

        class Ex:
            async def h1(self, s):
                raise BpmnModeledBoundaryError("x")

            async def h2(self, s):
                return None

        with self.assertRaises(BpmnEngineError) as ctx:
            asyncio.run(run_bpmn_workflow(Ex(), _state(), bpmn, bindings))
        self.assertEqual(ctx.exception.failure_reason, "handler_error")

    def test_unmodeled_exception_still_handler_error(self):
        bpmn = _bpmn_linear()
        bindings = _nb(_BIND_LINEAR)

        class Ex:
            async def h1(self, s):
                raise ValueError("boom")

            async def h2(self, s):
                return None

        with self.assertRaises(BpmnEngineError) as ctx:
            asyncio.run(run_bpmn_workflow(Ex(), _state(), bpmn, bindings))
        self.assertEqual(ctx.exception.failure_reason, "handler_error")

    def test_timer_boundary_merge_back_to_same_task_completes_without_hang(self):
        bpmn = {
            "elements": {
                "start": {
                    "type": "startEvent",
                    "outgoing": ["tmain"],
                    "outgoing_flow_ids": ["s0"],
                },
                "tmain": {
                    "type": "serviceTask",
                    "outgoing": ["endm"],
                    "outgoing_flow_ids": ["fm"],
                },
                "trec": {
                    "type": "serviceTask",
                    "outgoing": ["tmain"],
                    "outgoing_flow_ids": ["fr"],
                },
                "endm": {"type": "endEvent", "outgoing": []},
            },
            "sequence_flows": {"s0": {}, "fm": {}, "fr": {}},
            "ordered_element_ids": ["start", "tmain", "trec", "endm"],
            "boundary_by_task": {
                "tmain": {
                    "timer": {
                        "boundary_id": "bt",
                        "target_element_id": "trec",
                        "duration_iso": "PT0.001S",
                    }
                }
            },
        }
        bindings = _nb(
            {
                "workflow_id": "mb",
                "executor": "E",
                "serviceTasks": {
                    "tmain": {"handler": "main"},
                    "trec": {"handler": "rec"},
                },
            }
        )
        main_calls = [0]

        class Ex:
            async def main(self, s):
                main_calls[0] += 1
                return

            async def rec(self, s):
                return None

        tmono = [0.0]

        def _m():
            tmono[0] += 0.01
            return tmono[0]

        with patch("agent_app.bpmn_engine.time.monotonic", side_effect=_m):
            asyncio.run(run_bpmn_workflow(Ex(), _state(), bpmn, bindings))
        self.assertGreaterEqual(main_calls[0], 1)

    def test_global_timeout_routes_to_timer_boundary_when_single_token(self):
        bpmn = {
            "elements": {
                "start": {
                    "type": "startEvent",
                    "outgoing": ["t1"],
                    "outgoing_flow_ids": ["s0"],
                },
                "t1": {
                    "type": "serviceTask",
                    "outgoing": ["end"],
                    "outgoing_flow_ids": ["f1"],
                },
                "talt": {
                    "type": "serviceTask",
                    "outgoing": ["end"],
                    "outgoing_flow_ids": ["f2"],
                },
                "end": {"type": "endEvent", "outgoing": []},
            },
            "sequence_flows": {"s0": {}, "f1": {}, "f2": {}},
            "ordered_element_ids": ["start", "t1", "talt", "end"],
            "boundary_by_task": {
                "t1": {
                    "timer": {
                        "boundary_id": "bt",
                        "target_element_id": "talt",
                        "duration_iso": "PT1H",
                    }
                }
            },
        }
        bindings = _nb(
            {
                "workflow_id": "gt",
                "executor": "E",
                "serviceTasks": {
                    "t1": {"handler": "h1"},
                    "talt": {"handler": "halt"},
                },
            }
        )
        chk = AsyncMock(side_effect=["timeout"] + [None] * 30)

        class Ex:
            async def h1(self, s):
                return None

            async def halt(self, s):
                return None

        st = _state()

        async def run():
            await run_bpmn_workflow(Ex(), st, bpmn, bindings, execution_check=chk)

        asyncio.run(run())
        eng = getattr(st, "_bpmn_engine_state", {})
        bts = eng.get("boundary_transitions") or []
        self.assertTrue(
            any(
                x.get("reason") == "run_timeout_routed_to_timer_boundary"
                for x in bts
                if isinstance(x, dict)
            )
        )


class BpmnTaskRetryTests(TestCase):
    def test_bpmn_linear_task_retries_then_succeeds(self):
        bpmn = {
            "elements": {
                "start": {
                    "type": "startEvent",
                    "outgoing": ["t1"],
                    "outgoing_flow_ids": ["s0"],
                },
                "t1": {
                    "type": "serviceTask",
                    "outgoing": ["end"],
                    "outgoing_flow_ids": ["f1"],
                },
                "end": {"type": "endEvent", "outgoing": []},
            },
            "sequence_flows": {"s0": {}, "f1": {}},
            "ordered_element_ids": ["start", "t1", "end"],
        }
        bindings = _nb(
            {
                "workflow_id": "r",
                "executor": "E",
                "serviceTasks": {"t1": {"handler": "h1"}},
            }
        )
        n = [0]

        class Ex:
            async def h1(self, s):
                n[0] += 1
                if n[0] < 3:
                    raise BpmnRetryableTaskError("retry")
                return

        st = _state()
        asyncio.run(run_bpmn_workflow(Ex(), st, bpmn, bindings, max_task_retries=5))
        self.assertEqual(n[0], 3)

    def test_bpmn_retry_limit_exceeded_fails_run(self):
        bpmn = {
            "elements": {
                "start": {
                    "type": "startEvent",
                    "outgoing": ["t1"],
                    "outgoing_flow_ids": ["s0"],
                },
                "t1": {
                    "type": "serviceTask",
                    "outgoing": ["end"],
                    "outgoing_flow_ids": ["f1"],
                },
                "end": {"type": "endEvent", "outgoing": []},
            },
            "sequence_flows": {"s0": {}, "f1": {}},
            "ordered_element_ids": ["start", "t1", "end"],
        }
        bindings = _nb(
            {
                "workflow_id": "r",
                "executor": "E",
                "serviceTasks": {"t1": {"handler": "h1"}},
            }
        )

        class Ex:
            async def h1(self, s):
                raise BpmnRetryableTaskError("always")

        with self.assertRaises(BpmnEngineError) as ctx:
            asyncio.run(run_bpmn_workflow(Ex(), _state(), bpmn, bindings, max_task_retries=0))
        self.assertEqual(ctx.exception.failure_reason, "retry_exhausted")

    def test_bpmn_parallel_branch_retry_preserves_pending_join_state(self):
        bpmn = _bpmn_fork_join_downstream()
        bindings = _nb(_BIND_FJ)
        b_n = [0]

        class Ex:
            async def task0(self, s):
                return None

            async def task_a(self, s):
                return None

            async def task_b(self, s):
                b_n[0] += 1
                if b_n[0] == 1:
                    raise BpmnRetryableTaskError("transient")
                return

            async def task_after(self, s):
                return None

        st = _state()
        asyncio.run(run_bpmn_workflow(Ex(), st, bpmn, bindings, max_task_retries=2))
        eng = getattr(st, "_bpmn_engine_state", {})
        self.assertEqual(eng.get("pending_joins"), {})
        self.assertIn("taskAfter", st.workflow_steps)

    def test_bpmn_timeout_during_retry_loop(self):
        bpmn = {
            "elements": {
                "start": {
                    "type": "startEvent",
                    "outgoing": ["t1"],
                    "outgoing_flow_ids": ["s0"],
                },
                "t1": {
                    "type": "serviceTask",
                    "outgoing": ["end"],
                    "outgoing_flow_ids": ["f1"],
                },
                "end": {"type": "endEvent", "outgoing": []},
            },
            "sequence_flows": {"s0": {}, "f1": {}},
            "ordered_element_ids": ["start", "t1", "end"],
        }
        bindings = _nb(
            {
                "workflow_id": "r",
                "executor": "E",
                "serviceTasks": {"t1": {"handler": "h1"}},
            }
        )
        k = [0]

        class Ex:
            async def h1(self, s):
                raise BpmnRetryableTaskError("r")

        async def chk():
            k[0] += 1
            return "timeout" if k[0] >= 2 else None

        with self.assertRaises(BpmnEngineError) as ctx:
            asyncio.run(
                run_bpmn_workflow(
                    Ex(),
                    _state(),
                    bpmn,
                    bindings,
                    max_task_retries=5,
                    execution_check=chk,
                )
            )
        self.assertEqual(ctx.exception.failure_reason, "timeout")


class ConditionEvaluatorTests(TestCase):
    def test_state_attr_equals(self):
        st = _state()
        st.flag = 7
        self.assertTrue(evaluate_condition("state.flag == 7", st))
        self.assertFalse(evaluate_condition("state.flag == 8", st))

    def test_literal_true_false(self):
        self.assertTrue(evaluate_condition("true", _state()))
        self.assertFalse(evaluate_condition("false", _state()))

    def test_negative_number_in_condition(self):
        st = _state()
        st.x = -3
        self.assertTrue(evaluate_condition("state.x == -3", st))

    def test_unsupported_condition_raises(self):
        with self.assertRaises(ValueError):
            evaluate_condition("1 + 1 == 2", _state())


class SubprocessEngineTests(TestCase):
    def _bpmn_sub_sequential(self):
        return {
            "elements": {
                "start": {
                    "id": "start",
                    "type": "startEvent",
                    "outgoing": ["t_pre"],
                    "outgoing_flow_ids": ["e0"],
                },
                "t_pre": {
                    "id": "t_pre",
                    "type": "serviceTask",
                    "outgoing": ["sp"],
                    "outgoing_flow_ids": ["e1"],
                },
                "sp": {
                    "id": "sp",
                    "type": "subProcess",
                    "incoming": ["t_pre"],
                    "outgoing": ["t_post"],
                    "outgoing_flow_ids": ["e2"],
                },
                "t_post": {
                    "id": "t_post",
                    "type": "serviceTask",
                    "outgoing": ["end_p"],
                    "outgoing_flow_ids": ["e3"],
                },
                "end_p": {
                    "id": "end_p",
                    "type": "endEvent",
                    "outgoing": [],
                },
                "si": {
                    "id": "si",
                    "type": "startEvent",
                    "subprocess_container": "sp",
                    "outgoing": ["tin"],
                    "outgoing_flow_ids": ["ei0"],
                },
                "tin": {
                    "id": "tin",
                    "type": "serviceTask",
                    "subprocess_container": "sp",
                    "outgoing": ["end_i"],
                    "outgoing_flow_ids": ["ei1"],
                },
                "end_i": {
                    "id": "end_i",
                    "type": "endEvent",
                    "subprocess_container": "sp",
                    "outgoing": [],
                },
            },
            "sequence_flows": {k: {} for k in ["e0", "e1", "e2", "e3", "ei0", "ei1"]},
            "ordered_element_ids": [
                "start",
                "t_pre",
                "sp",
                "si",
                "tin",
                "end_i",
                "t_post",
                "end_p",
            ],
            "subprocess_root_ids": ["sp"],
        }

    def test_sequential_subprocess_runs_inner_then_parent(self):
        bpmn = self._bpmn_sub_sequential()
        bindings = _nb(
            {
                "workflow_id": "sp1",
                "executor": "E",
                "serviceTasks": {
                    "t_pre": {"handler": "pre"},
                    "tin": {"handler": "inner"},
                    "t_post": {"handler": "post"},
                },
            }
        )
        calls: list[str] = []

        class Ex:
            async def pre(self, s):
                calls.append("pre")
                return

            async def inner(self, s):
                calls.append("inner")
                return

            async def post(self, s):
                calls.append("post")
                return

        st = _state()
        asyncio.run(run_bpmn_workflow(Ex(), st, bpmn, bindings))
        self.assertEqual(calls, ["pre", "inner", "post"])
        stt = getattr(st, "_bpmn_engine_state", {}).get("subprocess_transitions") or []
        actions = [x.get("action") for x in stt if isinstance(x, dict)]
        self.assertIn("entered", actions)
        self.assertIn("completed", actions)

    def _bpmn_sub_parallel(self):
        return {
            "elements": {
                "start": {
                    "id": "start",
                    "type": "startEvent",
                    "outgoing": ["t_pre"],
                    "outgoing_flow_ids": ["s0"],
                },
                "t_pre": {
                    "id": "t_pre",
                    "type": "serviceTask",
                    "outgoing": ["sp"],
                    "outgoing_flow_ids": ["f1"],
                },
                "sp": {
                    "id": "sp",
                    "type": "subProcess",
                    "incoming": ["t_pre"],
                    "outgoing": ["t_post"],
                    "outgoing_flow_ids": ["f2"],
                },
                "t_post": {
                    "id": "t_post",
                    "type": "serviceTask",
                    "outgoing": ["end_p"],
                    "outgoing_flow_ids": ["f3"],
                },
                "end_p": {"id": "end_p", "type": "endEvent", "outgoing": []},
                "si": {
                    "id": "si",
                    "type": "startEvent",
                    "subprocess_container": "sp",
                    "outgoing": ["t_ent"],
                    "outgoing_flow_ids": ["i0"],
                },
                "t_ent": {
                    "id": "t_ent",
                    "type": "serviceTask",
                    "subprocess_container": "sp",
                    "outgoing": ["fork_in"],
                    "outgoing_flow_ids": ["i1"],
                },
                "fork_in": {
                    "id": "fork_in",
                    "type": "parallelGateway",
                    "incoming": ["t_ent"],
                    "outgoing": ["tA", "tB"],
                    "outgoing_flow_ids": ["ifa", "ifb"],
                },
                "tA": {
                    "id": "tA",
                    "type": "serviceTask",
                    "subprocess_container": "sp",
                    "outgoing": ["join_in"],
                    "outgoing_flow_ids": ["fa"],
                },
                "tB": {
                    "id": "tB",
                    "type": "serviceTask",
                    "subprocess_container": "sp",
                    "outgoing": ["join_in"],
                    "outgoing_flow_ids": ["fb"],
                },
                "join_in": {
                    "id": "join_in",
                    "type": "parallelGateway",
                    "incoming": ["tA", "tB"],
                    "outgoing": ["t_merge"],
                    "outgoing_flow_ids": ["fj"],
                },
                "t_merge": {
                    "id": "t_merge",
                    "type": "serviceTask",
                    "subprocess_container": "sp",
                    "outgoing": ["end_i"],
                    "outgoing_flow_ids": ["fm"],
                },
                "end_i": {
                    "id": "end_i",
                    "type": "endEvent",
                    "subprocess_container": "sp",
                    "outgoing": [],
                },
            },
            "sequence_flows": {
                k: {}
                for k in ["s0", "f1", "f2", "f3", "i0", "i1", "ifa", "ifb", "fa", "fb", "fj", "fm"]
            },
            "ordered_element_ids": [
                "start",
                "t_pre",
                "sp",
                "si",
                "t_ent",
                "fork_in",
                "tA",
                "tB",
                "join_in",
                "t_merge",
                "end_i",
                "t_post",
                "end_p",
            ],
            "subprocess_root_ids": ["sp"],
        }

    def test_parallel_inside_subprocess_then_exit(self):
        bpmn = self._bpmn_sub_parallel()
        bindings = _nb(
            {
                "workflow_id": "sp2",
                "executor": "E",
                "serviceTasks": {
                    "t_pre": {"handler": "pre"},
                    "t_ent": {"handler": "ent"},
                    "tA": {"handler": "ha"},
                    "tB": {"handler": "hb"},
                    "t_merge": {"handler": "merge"},
                    "t_post": {"handler": "post"},
                },
            }
        )
        calls: list[str] = []

        class Ex:
            async def pre(self, s):
                calls.append("pre")
                return

            async def ent(self, s):
                calls.append("ent")
                return

            async def ha(self, s):
                calls.append("ha")
                return

            async def hb(self, s):
                calls.append("hb")
                return

            async def merge(self, s):
                calls.append("merge")
                return

            async def post(self, s):
                calls.append("post")
                return

        st = _state()
        asyncio.run(run_bpmn_workflow(Ex(), st, bpmn, bindings))
        self.assertLess(calls.index("pre"), calls.index("ent"))
        self.assertLess(calls.index("ent"), calls.index("ha"))
        self.assertLess(calls.index("ent"), calls.index("hb"))
        self.assertLess(max(calls.index("ha"), calls.index("hb")), calls.index("merge"))
        self.assertLess(calls.index("merge"), calls.index("post"))

    def test_pause_resume_inside_subprocess_preserves_stack(self):
        bpmn = self._bpmn_sub_sequential()
        bindings = _nb(
            {
                "workflow_id": "sp3",
                "executor": "E",
                "serviceTasks": {
                    "t_pre": {"handler": "pre"},
                    "tin": {"handler": "inner"},
                    "t_post": {"handler": "post"},
                },
            }
        )
        inner_n = [0]

        class Ex1:
            async def pre(self, s):
                return None

            async def inner(self, s):
                inner_n[0] += 1
                if inner_n[0] == 1:
                    raise TaskPendingError("h", "human", s, "tin")
                return

            async def post(self, s):
                return None

        st = _state()
        with self.assertRaises(TaskPendingError):
            asyncio.run(run_bpmn_workflow(Ex1(), st, bpmn, bindings))
        stack = getattr(st, "_bpmn_engine_state", {}).get("subprocess_stack") or []
        self.assertTrue(
            any(str(x.get("subprocess_id")) == "sp" for x in stack if isinstance(x, dict))
        )

        eng = normalize_engine_state(dict(getattr(st, "_bpmn_engine_state", {})))
        st.__dict__["_bpmn_engine_state"] = eng

        class Ex2:
            async def pre(self, s):
                return None

            async def inner(self, s):
                return None

            async def post(self, s):
                return None

        asyncio.run(run_bpmn_workflow(Ex2(), st, bpmn, bindings, start_from_task_id="tin"))
        self.assertIn("t_post", getattr(st, "workflow_steps", []))
