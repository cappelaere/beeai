"""
Integration tests for BPMN engine: run from BPMN, pause/resume, gateways in real run, invalid BPMN rejected.
Uses real run_bpmn_workflow and fixtures; no full stack (DB/WS).
"""

import asyncio

from django.test import TestCase

from agent_app.bpmn_engine import (
    BpmnEngineError,
    get_next_step_for_resume,
    run_bpmn_workflow,
)
from agent_app.task_service import TaskPendingException
from agent_app.workflow_context import get_first_task_id, normalize_bindings


def _minimal_bpmn():
    return {
        "elements": {
            "start": {
                "id": "start",
                "type": "startEvent",
                "outgoing": ["task1"],
                "outgoing_flow_ids": ["f1"],
            },
            "task1": {
                "id": "task1",
                "type": "serviceTask",
                "outgoing": ["task2"],
                "outgoing_flow_ids": ["f2"],
            },
            "task2": {
                "id": "task2",
                "type": "serviceTask",
                "outgoing": ["end"],
                "outgoing_flow_ids": ["f3"],
            },
            "end": {"id": "end", "type": "endEvent", "outgoing": []},
        },
        "sequence_flows": {"f1": {}, "f2": {}, "f3": {}},
        "ordered_element_ids": ["start", "task1", "task2", "end"],
    }


def _bindings_linear():
    return normalize_bindings(
        {
            "workflow_id": "test",
            "serviceTasks": {"task1": {"handler": "task1"}, "task2": {"handler": "task2"}},
        },
        workflow_id="test",
        executor="test.Executor",
    )


class _MinimalState:
    workflow_steps = []

    def __init__(self):
        self.workflow_steps = list(self.workflow_steps)


class _ExecutorLinear:
    def __init__(self):
        self.calls = []

    async def task1(self, state):
        self.calls.append("task1")
        return None

    async def task2(self, state):
        self.calls.append("task2")
        return None


class _ExecutorPausesAfterTask1:
    async def task1(self, state):
        raise TaskPendingException("task1", "human_task", state, "task2")

    async def task2(self, state):
        return None


class BpmnIntegrationTests(TestCase):
    """Integration-style tests hitting run_bpmn_workflow with real BPMN/bindings."""

    def test_run_starts_from_bpmn_first_task(self):
        """Workflow run starts from the first task determined by BPMN, not by code."""
        bpmn = _minimal_bpmn()
        bindings = _bindings_linear()
        first_id = get_first_task_id(bpmn)
        self.assertEqual(first_id, "task1")

        state = _MinimalState()
        executor = _ExecutorLinear()
        asyncio.run(run_bpmn_workflow(executor, state, bpmn, bindings))

        self.assertEqual(executor.calls, ["task1", "task2"])
        self.assertIn("task1", state.workflow_steps)
        self.assertIn("task2", state.workflow_steps)
        eng = getattr(state, "_bpmn_engine_state", None)
        self.assertIsNotNone(eng)
        self.assertEqual(eng.get("completed_node_ids"), ["task1", "task2"])

    def test_pause_resume_preserves_engine_state(self):
        """Pause saves engine state; resume continues from correct node with state restored."""
        bpmn = _minimal_bpmn()
        bindings = _bindings_linear()
        state = _MinimalState()
        executor = _ExecutorPausesAfterTask1()

        with self.assertRaises(TaskPendingException) as ctx:
            asyncio.run(run_bpmn_workflow(executor, state, bpmn, bindings))

        next_step = get_next_step_for_resume(ctx.exception.state)
        self.assertEqual(next_step, "task2")
        eng = getattr(ctx.exception.state, "_bpmn_engine_state", None)
        self.assertIsNotNone(eng)
        self.assertIn("task1", eng.get("completed_node_ids", []))
        self.assertEqual(eng.get("current_node_ids"), ["task2"])

        # Resume from task2
        state_resumed = _MinimalState()
        state_resumed.workflow_steps = list(eng.get("completed_node_ids", []))
        state_resumed.__dict__["_bpmn_engine_state"] = dict(eng)
        executor2 = _ExecutorLinear()
        asyncio.run(
            run_bpmn_workflow(executor2, state_resumed, bpmn, bindings, start_from_task_id="task2")
        )
        self.assertEqual(executor2.calls, ["task2"])

    def test_exclusive_gateway_routes_correctly_in_real_run(self):
        """Exclusive gateway routes to the correct branch in a full run."""
        bpmn = {
            "elements": {
                "start": {
                    "id": "start",
                    "type": "startEvent",
                    "outgoing": ["task1"],
                    "outgoing_flow_ids": ["f0"],
                },
                "task1": {
                    "id": "task1",
                    "type": "serviceTask",
                    "outgoing": ["gw1"],
                    "outgoing_flow_ids": ["f1"],
                },
                "gw1": {
                    "id": "gw1",
                    "type": "exclusiveGateway",
                    "outgoing": ["task_a", "task_b"],
                    "outgoing_flow_ids": ["flow_a", "flow_b"],
                    "default_flow_id": "flow_b",
                },
                "task_a": {
                    "id": "task_a",
                    "type": "serviceTask",
                    "outgoing": ["end"],
                    "outgoing_flow_ids": ["f2"],
                },
                "task_b": {
                    "id": "task_b",
                    "type": "serviceTask",
                    "outgoing": ["end"],
                    "outgoing_flow_ids": ["f3"],
                },
                "end": {"id": "end", "type": "endEvent", "outgoing": []},
            },
            "sequence_flows": {
                "f0": {},
                "f1": {},
                "flow_a": {"condition": "state.x == 1", "target": "task_a"},
                "flow_b": {"condition": "state.x == 2", "target": "task_b"},
                "f2": {},
                "f3": {},
            },
            "ordered_element_ids": ["start", "task1", "gw1", "task_a", "task_b", "end"],
        }
        bindings = normalize_bindings(
            {
                "workflow_id": "test",
                "serviceTasks": {
                    "task1": {"handler": "task1"},
                    "task_a": {"handler": "task_a"},
                    "task_b": {"handler": "task_b"},
                },
            },
            workflow_id="test",
            executor="test.Executor",
        )
        state = _MinimalState()
        state.__dict__["x"] = 1

        class _ExecGateway:
            def __init__(self):
                self.calls = []

            async def task1(self, s):
                self.calls.append("task1")

            async def task_a(self, s):
                self.calls.append("task_a")

            async def task_b(self, s):
                self.calls.append("task_b")

        executor = _ExecGateway()
        asyncio.run(run_bpmn_workflow(executor, state, bpmn, bindings))

        self.assertIn("task1", executor.calls)
        self.assertIn("task_a", executor.calls)
        self.assertNotIn("task_b", executor.calls)
        self.assertIn("task1", state.workflow_steps)
        self.assertIn("task_a", state.workflow_steps)

    def test_invalid_bpmn_rejected_before_execution(self):
        """Missing binding for first task raises before any handler runs."""
        bpmn = _minimal_bpmn()
        bindings = normalize_bindings(
            {"workflow_id": "test", "serviceTasks": {"task2": {"handler": "task2"}}},
            workflow_id="test",
            executor="test.Executor",
        )
        state = _MinimalState()
        executor = _ExecutorLinear()

        with self.assertRaises(BpmnEngineError) as ctx:
            asyncio.run(run_bpmn_workflow(executor, state, bpmn, bindings))

        self.assertEqual(ctx.exception.failure_reason, "missing_binding")
        self.assertEqual(ctx.exception.failed_node_id, "task1")
        self.assertEqual(executor.calls, [])

    def test_handler_error_failure_metadata_surfaced(self):
        """Handler exception sets failed_node_id, failure_reason, last_successful_node_id on engine state."""
        bpmn = _minimal_bpmn()
        bindings = _bindings_linear()
        state = _MinimalState()

        class _ExecutorFailsOnTask2:
            async def task1(self, s):
                pass

            async def task2(self, s):
                raise RuntimeError("task2 failed")

        executor = _ExecutorFailsOnTask2()
        with self.assertRaises(BpmnEngineError) as ctx:
            asyncio.run(run_bpmn_workflow(executor, state, bpmn, bindings))
        e = ctx.exception
        self.assertEqual(e.failure_reason, "handler_error")
        self.assertEqual(e.failed_node_id, "task2")
        eng = getattr(e.state, "_bpmn_engine_state", None)
        self.assertIsNotNone(eng)
        self.assertEqual(eng.get("last_successful_node_id"), "task1")
        self.assertIn("task1", eng.get("completed_node_ids", []))

    def test_pause_resume_with_persisted_progress_data(self):
        """Resume using a progress_data-like dict (engine_state, state_data, next_step) restores and continues."""
        bpmn = _minimal_bpmn()
        bindings = _bindings_linear()
        state = _MinimalState()
        executor_pause = _ExecutorPausesAfterTask1()

        with self.assertRaises(TaskPendingException) as ctx:
            asyncio.run(run_bpmn_workflow(executor_pause, state, bpmn, bindings))

        eng = getattr(ctx.exception.state, "_bpmn_engine_state", None)
        self.assertIsNotNone(eng)
        progress_data = {
            "engine_state": dict(eng),
            "state_data": {"workflow_steps": list(eng.get("completed_node_ids", []))},
            "next_step": "task2",
        }

        # Simulate resume: rebuild state from progress_data and run from next_step
        state_resumed = _MinimalState()
        state_resumed.workflow_steps = list(progress_data["state_data"].get("workflow_steps", []))
        state_resumed.__dict__["_bpmn_engine_state"] = dict(progress_data["engine_state"])
        executor2 = _ExecutorLinear()
        asyncio.run(
            run_bpmn_workflow(
                executor2,
                state_resumed,
                bpmn,
                bindings,
                start_from_task_id=progress_data["next_step"],
            )
        )
        self.assertEqual(executor2.calls, ["task2"])
        self.assertIn("task2", state_resumed.workflow_steps)

    def test_gateway_no_match_failure_metadata_surfaced(self):
        """When no condition matches and no default flow, engine raises with condition_failure_metadata."""
        bpmn = {
            "elements": {
                "start": {
                    "id": "start",
                    "type": "startEvent",
                    "outgoing": ["task1"],
                    "outgoing_flow_ids": ["f0"],
                },
                "task1": {
                    "id": "task1",
                    "type": "serviceTask",
                    "outgoing": ["gw1"],
                    "outgoing_flow_ids": ["f1"],
                },
                "gw1": {
                    "id": "gw1",
                    "type": "exclusiveGateway",
                    "outgoing": ["task_a", "task_b"],
                    "outgoing_flow_ids": ["flow_a", "flow_b"],
                    "default_flow_id": None,
                },
                "task_a": {
                    "id": "task_a",
                    "type": "serviceTask",
                    "outgoing": ["end"],
                    "outgoing_flow_ids": ["f2"],
                },
                "task_b": {
                    "id": "task_b",
                    "type": "serviceTask",
                    "outgoing": ["end"],
                    "outgoing_flow_ids": ["f3"],
                },
                "end": {"id": "end", "type": "endEvent", "outgoing": []},
            },
            "sequence_flows": {
                "f0": {},
                "f1": {},
                "flow_a": {"condition": "state.x == 1", "target": "task_a"},
                "flow_b": {"condition": "state.x == 2", "target": "task_b"},
                "f2": {},
                "f3": {},
            },
            "ordered_element_ids": ["start", "task1", "gw1", "task_a", "task_b", "end"],
        }
        bindings = normalize_bindings(
            {
                "workflow_id": "test",
                "serviceTasks": {
                    "task1": {"handler": "task1"},
                    "task_a": {"handler": "task_a"},
                    "task_b": {"handler": "task_b"},
                },
            },
            workflow_id="test",
            executor="test.Executor",
        )
        state = _MinimalState()
        state.__dict__["x"] = 3  # no condition matches

        class _ExecGateway:
            def __init__(self):
                self.calls = []

            async def task1(self, s):
                self.calls.append("task1")

            async def task_a(self, s):
                self.calls.append("task_a")

            async def task_b(self, s):
                self.calls.append("task_b")

        executor = _ExecGateway()
        with self.assertRaises(BpmnEngineError) as ctx:
            asyncio.run(run_bpmn_workflow(executor, state, bpmn, bindings))
        e = ctx.exception
        self.assertEqual(e.failure_reason, "invalid_gateway")
        # Engine records the current node (task1) when resolve_next_executable_task raises at the gateway
        self.assertEqual(e.failed_node_id, "task1")
        self.assertIsNotNone(e.condition_failure_metadata)
        self.assertIn("message", e.condition_failure_metadata)
        self.assertIn("no matching condition", e.condition_failure_metadata["message"])
