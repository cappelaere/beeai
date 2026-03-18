"""Progress payload shaping for multi-node current_node_ids (BPMN-PAR-004, PAR-008)."""

import json
from pathlib import Path
from types import SimpleNamespace

from django.template import Context, Template
from django.template.loader import get_template
from django.test import SimpleTestCase

from agent_app.bpmn_run_diagnostics import build_operator_diagnostics
from agent_app.models import WorkflowRun
from agent_app.views.workflows import _build_progress_info, _build_progress_node_ids_json


class BuildProgressInfoTests(SimpleTestCase):
    def test_preserves_multiple_current_nodes(self):
        run = SimpleNamespace(
            status="waiting_for_task",
            progress_data={
                "next_step": "join_gw",
                "state_data": {"workflow_steps": ["t_a"]},
                "paused_at": "2025-01-01T00:00:00Z",
                "pending_tasks": ["ht1"],
                "completed_node_ids": ["t_a"],
                "current_node_ids": ["branch_task_1", "branch_task_2"],
                "failed_node_id": None,
            },
        )
        info = _build_progress_info(run)
        assert info is not None
        self.assertEqual(info["current_node_ids"], ["branch_task_1", "branch_task_2"])
        self.assertIn("branch_task_1", info["current_node_display"])
        self.assertIn("branch_task_2", info["current_node_display"])

    def test_build_progress_node_ids_json_round_trip_multi(self):
        info = {
            "completed_node_ids": ["a"],
            "current_node_ids": ["x", "y", "z"],
            "failed_node_id": None,
        }
        j = _build_progress_node_ids_json(info)
        self.assertEqual(json.loads(j["current_node_ids"]), ["x", "y", "z"])
        self.assertEqual(json.loads(j["completed_node_ids"]), ["a"])

    def test_completed_run_empty_current_display(self):
        run = SimpleNamespace(
            status="completed",
            progress_data={"completed_node_ids": ["a", "b"]},
            output_data=None,
        )
        info = _build_progress_info(run)
        assert info is not None
        self.assertEqual(info["current_node_ids"], [])
        self.assertEqual(info["current_node_display"], "—")
        self.assertFalse(info.get("show_parallel_panel"))

    def test_build_progress_info_includes_waiting_join_ids(self):
        run = SimpleNamespace(
            status="waiting_for_task",
            progress_data={
                "next_step": "taskB",
                "state_data": {"workflow_steps": ["task0", "taskA"]},
                "current_node_ids": ["joinGW", "taskB"],
                "engine_state": {
                    "active_tokens": [
                        {"current_element_id": "joinGW", "branch_id": "forkGW:ffa"},
                        {"current_element_id": "taskB", "branch_id": "forkGW:ffb"},
                    ],
                    "pending_joins": {
                        "joinGW": {
                            "expected_branch_ids": ["forkGW:ffa", "forkGW:ffb"],
                            "arrived_branch_ids": ["forkGW:ffa"],
                        }
                    },
                },
            },
        )
        info = _build_progress_info(run)
        assert info is not None
        self.assertEqual(info["waiting_join_ids"], ["joinGW"])
        self.assertEqual(info["pending_join_count"], 1)
        self.assertIn("forkGW:ffa", info["active_branch_ids"])
        self.assertTrue(info["show_parallel_panel"])
        self.assertIn("joinGW", info["parallel_state_summary"] or "")
        self.assertEqual(info["nodes_waiting_at_join"], ["joinGW"])

    def test_build_progress_info_parallel_state_summary_multi_branch(self):
        run = SimpleNamespace(
            status="running",
            progress_data={
                "completed_node_ids": ["task0"],
                "current_node_ids": ["taskA", "taskB"],
                "engine_state": {
                    "active_tokens": [
                        {"current_element_id": "taskA", "branch_id": "f:a"},
                        {"current_element_id": "taskB", "branch_id": "f:b"},
                    ],
                    "pending_joins": {},
                },
            },
        )
        info = _build_progress_info(run)
        assert info is not None
        self.assertTrue(info["show_parallel_panel"])
        self.assertIn("2 parallel branches", info["parallel_state_summary"] or "")

    def test_build_progress_info_linear_waiting_no_parallel_clutter(self):
        run = SimpleNamespace(
            status="waiting_for_task",
            progress_data={
                "next_step": "task_b",
                "state_data": {"workflow_steps": ["task_a"]},
                "current_node_ids": ["task_b"],
                "engine_state": {
                    "active_tokens": [{"current_element_id": "task_b", "branch_id": None}],
                    "pending_joins": {},
                },
            },
        )
        info = _build_progress_info(run)
        assert info is not None
        self.assertFalse(info.get("show_parallel_panel"))
        self.assertEqual(info.get("pending_join_count"), 0)

    def test_run_detail_fragment_renders_waiting_join_state(self):
        info = {
            "show_parallel_panel": True,
            "waiting_join_ids": ["joinGW"],
            "nodes_waiting_at_join": ["joinGW"],
            "active_branch_ids": ["forkGW:ffa", "forkGW:ffb"],
            "parallel_state_summary": "Waiting at parallel join — joinGW (1/2 branches at join).",
        }
        t = Template(
            "{% if progress_info.show_parallel_panel %}"
            "<div class='parallel-panel'>{{ progress_info.parallel_state_summary }}"
            "{% for j in progress_info.waiting_join_ids %}<span data-join='{{ j }}'></span>{% endfor %}"
            "</div>{% endif %}"
        )
        html = t.render(Context({"progress_info": info}))
        self.assertIn("joinGW", html)
        self.assertIn("parallel-panel", html)
        self.assertIn("Waiting at parallel join", html)

    def test_task_detail_fragment_parallel_failure_context(self):
        wf = {
            "parallel_failure_context": "Failure during parallel execution.",
            "parallel_failure_waiting_join_ids": ["joinGW"],
            "failure_reason": "handler_error",
            "failed_node_id": "taskB",
        }
        t = Template(
            "{% if workflow_run_failure.parallel_failure_context %}"
            "<p class='pf'>{{ workflow_run_failure.parallel_failure_context }}</p>"
            "{% for j in workflow_run_failure.parallel_failure_waiting_join_ids %}"
            "<code>{{ j }}</code>{% endfor %}"
            "{% endif %}"
        )
        html = t.render(Context({"workflow_run_failure": wf}))
        self.assertIn("parallel execution", html)
        self.assertIn("joinGW", html)

    def test_bpmn_failure_summary_parallel_fields(self):
        r = WorkflowRun()
        r.status = WorkflowRun.STATUS_FAILED
        r.progress_data = {
            "failure_reason": "handler_error",
            "failed_node_id": "taskB",
            "engine_state": {
                "pending_joins": {"joinGW": {"expected_branch_ids": ["a", "b"]}},
                "active_tokens": [
                    {"current_element_id": "joinGW", "branch_id": "a"},
                ],
            },
        }
        s = r.bpmn_failure_summary()
        assert s is not None
        self.assertEqual(s["parallel_failure_waiting_join_ids"], ["joinGW"])
        self.assertIn("joinGW", s["parallel_failure_context"])

    def test_bpmn_failure_summary_timeout_context(self):
        r = WorkflowRun()
        r.status = WorkflowRun.STATUS_FAILED
        r.progress_data = {
            "failure_reason": "timeout",
            "failed_node_id": None,
            "timeout_seconds": 120,
            "timed_out_at": "2026-01-01T00:00:00+00:00",
            "engine_state": {
                "pending_joins": {"joinGW": {"expected_branch_ids": ["a", "b"]}},
                "active_tokens": [
                    {"current_element_id": "joinGW", "branch_id": "a"},
                    {"current_element_id": "taskB", "branch_id": "b"},
                ],
            },
        }
        s = r.bpmn_failure_summary()
        assert s is not None
        self.assertEqual(s["failure_reason"], "timeout")
        self.assertEqual(s["timeout_seconds"], 120)
        self.assertEqual(s["timed_out_at"], "2026-01-01T00:00:00+00:00")
        self.assertEqual(s["parallel_failure_waiting_join_ids"], ["joinGW"])

    def test_bpmn_failure_summary_retry_exhausted_context(self):
        r = WorkflowRun()
        r.status = WorkflowRun.STATUS_FAILED
        r.progress_data = {
            "failure_reason": "retry_exhausted",
            "failed_node_id": "taskX",
            "condition_failure_metadata": {
                "retry_attempts": 3,
                "bpmn_max_task_retries": 2,
                "last_error": "rate limited",
                "branch_id": "forkGW:ffa",
            },
        }
        s = r.bpmn_failure_summary()
        assert s is not None
        self.assertEqual(s["failure_reason"], "retry_exhausted")
        self.assertEqual(s["retry_attempts"], 3)
        self.assertEqual(s["bpmn_max_task_retries"], 2)
        self.assertEqual(s["last_retryable_error_message"], "rate limited")
        self.assertEqual(s["retry_exhausted_branch_id"], "forkGW:ffa")

    def test_workflow_execution_js_handles_parallel_join_progress(self):
        agent_ui_root = Path(__file__).resolve().parents[2]
        js = (agent_ui_root / "static" / "js" / "workflow-execution.js").read_text(encoding="utf-8")
        self.assertIn("pending_joins", js)
        self.assertIn("Running · at join", js)
        self.assertIn("merged path", js)

    def test_workflow_execution_js_status_labels_for_retry_and_join_wait(self):
        agent_ui_root = Path(__file__).resolve().parents[2]
        js = (agent_ui_root / "static" / "js" / "workflow-execution.js").read_text(encoding="utf-8")
        self.assertIn("retrying_task_id", js)
        self.assertIn("Retrying ·", js)
        self.assertIn("last_retryable_error", js)

    def test_run_detail_renders_bpmn_operator_retry_exhausted(self):
        pd = {
            "failure_reason": "retry_exhausted",
            "failed_node_id": "taskX",
            "condition_failure_metadata": {"retry_attempts": 3, "last_error": "boom"},
        }
        op = build_operator_diagnostics(pd, "failed")
        t = get_template("workflows/includes/bpmn_operator_panel.html")
        html = t.render(
            {
                "bpmn_operator": op,
                "progress_info": {},
                "run": SimpleNamespace(progress_data=pd),
                "bpmn_progress_json": "{}",
            }
        )
        self.assertIn("bpmn-operator-diagnostics", html)
        self.assertIn("exhausted", html.lower())
        self.assertIn("taskX", html)

    def test_run_detail_renders_cancelled_parallel_context(self):
        pd = {
            "failure_reason": "cancelled",
            "cancelled_at": "2026-01-01T00:00:00Z",
            "engine_state": {"pending_joins": {"joinGW": {}}},
        }
        op = build_operator_diagnostics(pd, "cancelled")
        t = get_template("workflows/includes/bpmn_operator_panel.html")
        html = t.render(
            {
                "bpmn_operator": op,
                "progress_info": {},
                "run": SimpleNamespace(progress_data=pd),
                "bpmn_progress_json": "{}",
            }
        )
        self.assertIn("Parallel run stopped", html)
        self.assertIn("joinGW", html)

    def test_build_progress_info_includes_timeline_companion_running_retry(self):
        """Running + retry fields remain available for panel alongside timeline helper."""
        run = SimpleNamespace(
            status="running",
            progress_data={
                "completed_node_ids": ["t0"],
                "current_node_ids": ["t1"],
                "retrying_task_id": "t1",
                "retry_attempt": 1,
                "bpmn_max_task_retries": 2,
                "engine_state": {"last_retryable_error": {"message": "try again"}},
            },
        )
        info = _build_progress_info(run)
        assert info is not None
        self.assertEqual(info["retrying_task_id"], "t1")
        op = build_operator_diagnostics(run.progress_data, "running")
        self.assertIn("Retrying", op.get("headline") or "")

    def test_task_detail_renders_bpmn_run_context_fragment(self):
        ctx = {
            "run_id": "ab12cd34",
            "next_step": "userTask1",
            "current_nodes_display": "userTask1",
            "join_summary": "Waiting at join: j1 (1/2)",
            "retrying_task_id": None,
        }
        t = Template(
            "{% if bpmn_task_run_context %}"
            "<div class='bpmn-ctx'>{{ bpmn_task_run_context.run_id }}"
            "{{ bpmn_task_run_context.next_step }}"
            "{{ bpmn_task_run_context.join_summary }}</div>{% endif %}"
        )
        html = t.render(Context({"bpmn_task_run_context": ctx}))
        self.assertIn("ab12cd34", html)
        self.assertIn("userTask1", html)
        self.assertIn("Waiting at join", html)
