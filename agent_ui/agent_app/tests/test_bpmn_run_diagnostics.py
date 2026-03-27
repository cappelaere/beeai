"""Unit tests for bpmn_run_diagnostics (PAR-013)."""

from django.test import SimpleTestCase

from agent_app.bpmn_run_diagnostics import (
    build_bpmn_task_run_context,
    build_operator_diagnostics,
    build_operator_timeline_lines,
    failure_reason_operator_label,
    is_bpmn_operator_view,
)


class FailureReasonLabelTests(SimpleTestCase):
    def test_known_reasons(self):
        self.assertIn("handler", failure_reason_operator_label("handler_error").lower())
        self.assertIn("cancelled", failure_reason_operator_label("cancelled").lower())
        self.assertIn("exhaust", failure_reason_operator_label("retry_exhausted").lower())

    def test_unknown_reason(self):
        self.assertEqual(failure_reason_operator_label("custom_reason"), "Custom Reason")


class TimelineTests(SimpleTestCase):
    def test_completed_nodes(self):
        pd = {"completed_node_ids": ["a", "b"]}
        lines = build_operator_timeline_lines("running", pd)
        self.assertTrue(any("Completed nodes" in L and "a" in L for L in lines))

    def test_join_wait(self):
        pd = {
            "engine_state": {
                "pending_joins": {
                    "j1": {"arrived_branch_ids": ["b1"], "expected_branch_ids": ["b1", "b2"]}
                }
            }
        }
        lines = build_operator_timeline_lines("running", pd)
        self.assertTrue(any("join" in L.lower() and "1/2" in L for L in lines))

    def test_retrying(self):
        pd = {"retrying_task_id": "t1", "retry_attempt": 2, "bpmn_max_task_retries": 2}
        lines = build_operator_timeline_lines("running", pd)
        self.assertTrue(any("Retrying" in L and "t1" in L for L in lines))

    def test_cancelled(self):
        pd = {"failure_reason": "cancelled", "cancelled_at": "2025-01-01T00:00:00Z"}
        lines = build_operator_timeline_lines("cancelled", pd)
        self.assertTrue(any("Cancel" in L for L in lines))

    def test_timeout(self):
        pd = {
            "failure_reason": "timeout",
            "timeout_seconds": 60,
            "timed_out_at": "2025-01-01T00:01:00Z",
        }
        lines = build_operator_timeline_lines("failed", pd)
        self.assertTrue(any("limit" in L.lower() or "time" in L.lower() for L in lines))

    def test_waiting_bpmn_timer_and_message(self):
        pd = {
            "next_step": "ic1",
            "engine_state": {
                "bpmn_event_wait": {
                    "timer_deadline_iso": "2026-01-01T12:00:00+00:00",
                    "message_key": "k1",
                }
            },
        }
        lines_t = build_operator_timeline_lines("waiting_for_bpmn_timer", pd)
        self.assertTrue(any("timer" in L.lower() for L in lines_t))
        lines_m = build_operator_timeline_lines("waiting_for_bpmn_message", pd)
        self.assertTrue(any("message" in L.lower() and "k1" in L for L in lines_m))

    def test_intermediate_catch_transition_line(self):
        pd = {
            "engine_state": {
                "intermediate_catch_transitions": [{"event_id": "c1", "catch_type": "timer"}]
            }
        }
        lines = build_operator_timeline_lines("completed", pd)
        self.assertTrue(any("intermediate" in L.lower() and "c1" in L for L in lines))

    def test_subprocess_transitions_in_timeline(self):
        pd = {
            "engine_state": {
                "subprocess_transitions": [
                    {"subprocess_id": "sp1", "action": "entered", "name": "Inner"},
                    {"subprocess_id": "sp1", "action": "completed"},
                ],
                "subprocess_stack": [{"name": "ActiveSP", "subprocess_id": "sp2"}],
            },
            "current_node_ids": ["t1"],
        }
        lines = build_operator_timeline_lines("running", pd)
        self.assertTrue(any("Entered subprocess" in L and "sp1" in L for L in lines))
        self.assertTrue(any("Completed subprocess" in L and "sp1" in L for L in lines))
        self.assertTrue(any("Active subprocess" in L or "ActiveSP" in L for L in lines))

    def test_boundary_transitions_timer_and_error(self):
        pd = {
            "engine_state": {
                "boundary_transitions": [
                    {
                        "boundary_type": "timer",
                        "attached_to_task_id": "taskA",
                        "reason": "timer_deadline",
                    },
                    {
                        "boundary_type": "error",
                        "attached_to_task_id": "taskB",
                        "reason": "x",
                    },
                    {
                        "boundary_type": "timer",
                        "attached_to_task_id": "taskC",
                        "reason": "run_timeout_routed_to_timer_boundary",
                    },
                ]
            }
        }
        lines = build_operator_timeline_lines("completed", pd)
        self.assertTrue(any("Deadline path" in L and "taskA" in L for L in lines))
        self.assertTrue(any("Error boundary" in L and "taskB" in L for L in lines))
        self.assertTrue(any("time limit" in L.lower() and "taskC" in L for L in lines))


class DiagnosticsTests(SimpleTestCase):
    def test_retry_exhausted_headline(self):
        pd = {
            "failure_reason": "retry_exhausted",
            "failed_node_id": "taskX",
            "condition_failure_metadata": {
                "retry_attempts": 3,
                "branch_id": "f:b1",
                "last_error": "boom",
            },
        }
        d = build_operator_diagnostics(pd, "failed")
        self.assertIn("exhausted", d["headline"].lower())
        self.assertIn("taskX", d["terminal_block"])

    def test_cancelled_parallel(self):
        pd = {
            "failure_reason": "cancelled",
            "cancelled_at": "Z",
            "engine_state": {"pending_joins": {"j1": {}}},
        }
        d = build_operator_diagnostics(pd, "cancelled")
        self.assertIsNotNone(d["parallel_context"])
        self.assertIn("join", d["parallel_context"].lower())

    def test_is_bpmn_gating(self):
        self.assertTrue(is_bpmn_operator_view(diagram_bpmn_xml=True, progress_data=None))
        self.assertTrue(
            is_bpmn_operator_view(diagram_bpmn_xml=False, progress_data={"engine_state": {}})
        )
        self.assertFalse(is_bpmn_operator_view(diagram_bpmn_xml=False, progress_data={}))
        self.assertFalse(is_bpmn_operator_view(diagram_bpmn_xml=False, progress_data=None))


class TaskContextTests(SimpleTestCase):
    def test_waiting_context(self):
        pd = {
            "next_step": "humanTask1",
            "current_node_ids": ["humanTask1"],
            "engine_state": {},
        }
        ctx = build_bpmn_task_run_context(pd, "waiting_for_task", "abc12345")
        self.assertEqual(ctx["next_step"], "humanTask1")
        self.assertEqual(ctx["run_id"], "abc12345")

    def test_non_bpmn_no_context(self):
        self.assertIsNone(build_bpmn_task_run_context({}, "waiting_for_task", "x"))
