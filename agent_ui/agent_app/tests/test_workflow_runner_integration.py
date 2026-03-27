"""
Full-stack tests: execute_workflow_run and resume_bpmn_after_pause with persisted WorkflowRun.
"""

import asyncio
import uuid
from unittest.mock import patch

from django.test import TransactionTestCase

from agent_app.bpmn_engine import BpmnEngineError, _get_bindings_and_bpmn, normalize_engine_state
from agent_app.models import WorkflowRun
from agent_app.task_service import TaskPendingError
from agent_app.workflow_context import get_workflow_context, normalize_bindings
from agent_app.workflow_registry import workflow_registry
from agent_app.workflow_runner import (
    _execution_abort_reason_sync,
    _handle_workflow_paused,
    execute_workflow_run,
    resume_bpmn_after_pause,
)


def _run_id():
    return uuid.uuid4().hex[:8]


class WorkflowRunnerIntegrationTests(TransactionTestCase):
    """Hit workflow_runner + DB progress_data (pause, resume, failure)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        workflow_registry.reload()

    def _create_workflow_run(self, workflow_id: str, input_data: dict):
        rid = _run_id()
        WorkflowRun.objects.create(
            run_id=rid,
            workflow_id=workflow_id,
            workflow_name=workflow_id,
            status=WorkflowRun.STATUS_PENDING,
            user_id=9,
            input_data=input_data,
        )
        return rid

    def test_issue9_bidder_onboarding_routes_gateway_in_runner_path(self):
        """Issue #9 regression: real runner path must pass Gateway_SAM_Decision."""
        from agent_app import bpmn_engine

        ctx = get_workflow_context("bidder_onboarding")
        self.assertIn("/currentVersion/", ctx.get("files", {}).get("bpmn_path", ""))

        gateway_calls = []
        original_select = bpmn_engine.select_exclusive_flow

        class _FakeCursor:
            def __init__(self, rows):
                self._rows = rows

            def fetchall(self):
                return self._rows

        class _FakeConn:
            def execute(self, _query, _params):
                rows = [
                    {
                        "name": "Issue9 Regression Bidder",
                        "classification": "Entity",
                        "excluding_agency": "Test Agency",
                        "exclusion_type": "Debarment",
                        "active_date": "2025-01-01",
                        "termination_date": "Indefinite",
                        "record_status": "Active",
                        "sam_number": "SAM-ISSUE9",
                    }
                ]
                return _FakeCursor(rows)

        class _FakeSamDbContext:
            def __enter__(self):
                return _FakeConn()

            def __exit__(self, exc_type, exc, tb):
                return False

        def _spy_select(bpmn, gateway_element_id, state, bindings):
            target_id = original_select(bpmn, gateway_element_id, state, bindings)
            if gateway_element_id == "Gateway_SAM_Decision":
                gateway_calls.append(
                    {
                        "gateway": gateway_element_id,
                        "sam_passed": getattr(state, "sam_passed", None),
                        "default_flow_id": (bpmn.get("elements", {}).get(gateway_element_id) or {}).get(
                            "default_flow_id"
                        ),
                        "target_id": target_id,
                    }
                )
            return target_id

        rid = self._create_workflow_run(
            "bidder_onboarding",
            {
                "bidder_name": "Issue9 Regression Bidder",
                "property_id": 1,
                "registration_data": {
                    "email": "issue9@example.invalid",
                    "phone": "555-0100",
                    "terms_accepted": True,
                    "age_accepted": True,
                },
            },
        )

        with (
            patch("agent_app.bpmn_engine.select_exclusive_flow", side_effect=_spy_select),
            patch("workflows.bidder_onboarding.workflow.get_sam_db", return_value=_FakeSamDbContext()),
        ):
            asyncio.run(execute_workflow_run(rid, send_message=None))

        run = WorkflowRun.objects.get(run_id=rid)
        self.assertEqual(run.status, WorkflowRun.STATUS_COMPLETED)
        self.assertTrue(gateway_calls, msg="expected Gateway_SAM_Decision to be evaluated")
        self.assertEqual(gateway_calls[0]["sam_passed"], False)
        self.assertEqual(gateway_calls[0]["default_flow_id"], "Flow_gateway_no")
        self.assertEqual(gateway_calls[0]["target_id"], "finalize_status")

    def test_issue9_dap_report_routes_gateway_in_runner_path(self):
        """Issue #9 regression: real runner path must pass Gateway_1."""
        from agent_app import bpmn_engine

        ctx = get_workflow_context("dap_report")
        self.assertIn("/currentVersion/", ctx.get("files", {}).get("bpmn_path", ""))

        gateway_calls = []
        original_select = bpmn_engine.select_exclusive_flow

        class _FakeGresAgent:
            async def process(self, query, _context):
                q = str(query)
                if "Retrieve Daily Activity Performance (DAP) data" in q:
                    return {
                        "status": "ok",
                        "data": {
                            "auctions_active": 1,
                            "auctions_new": 0,
                            "auctions_closed": 0,
                            "total_bids": 2,
                            "new_bidders": 1,
                            "average_bid": 1000,
                            "property_views": 10,
                            "unique_visitors": 5,
                            "total_revenue": 2000,
                            "compliance_checks": 3,
                            "compliance_failures": 0,
                            "uptime": 99.9,
                            "response_time": 120,
                        },
                    }
                if "Retrieve daily metrics from" in q:
                    return {
                        "status": "ok",
                        "data": {
                            "time_series": [
                                {
                                    "date": "2025-05-30",
                                    "metrics": {
                                        "auctions": {"active": 1},
                                        "bidding": {"total_bids": 1},
                                        "revenue": {"total": 1000},
                                        "compliance": {"checks_failed": 0},
                                    },
                                },
                                {
                                    "date": "2025-06-01",
                                    "metrics": {
                                        "auctions": {"active": 1},
                                        "bidding": {"total_bids": 2},
                                        "revenue": {"total": 2000},
                                        "compliance": {"checks_failed": 0},
                                    },
                                },
                            ]
                        },
                    }
                # Analysis query
                return {
                    "status": "ok",
                    "data": {
                        "summary": "Stable performance",
                        "score": 85,
                        "highlights": ["No major issues"],
                        "concerns": [],
                        "anomalies": [],
                        "recommendations": ["Continue monitoring"],
                        "risk_level": "low",
                        "detailed_analysis": "All key metrics are within expected bounds.",
                    },
                }

        def _spy_select(bpmn, gateway_element_id, state, bindings):
            target_id = original_select(bpmn, gateway_element_id, state, bindings)
            if gateway_element_id == "Gateway_1":
                gateway_calls.append(
                    {
                        "gateway": gateway_element_id,
                        "has_issues": getattr(state, "has_issues", None),
                        "default_flow_id": (bpmn.get("elements", {}).get(gateway_element_id) or {}).get(
                            "default_flow_id"
                        ),
                        "target_id": target_id,
                    }
                )
            return target_id

        rid = self._create_workflow_run(
            "dap_report",
            {"report_date": "2025-06-01", "lookback_days": 7},
        )

        with (
            patch("agent_app.bpmn_engine.select_exclusive_flow", side_effect=_spy_select),
            patch("workflows.dap_report.workflow._get_agent", return_value=_FakeGresAgent()),
        ):
            asyncio.run(execute_workflow_run(rid, send_message=None))

        run = WorkflowRun.objects.get(run_id=rid)
        self.assertEqual(run.status, WorkflowRun.STATUS_COMPLETED)
        self.assertTrue(gateway_calls, msg="expected Gateway_1 to be evaluated")
        self.assertEqual(gateway_calls[0]["has_issues"], False)
        self.assertEqual(gateway_calls[0]["default_flow_id"], "Flow_6")
        self.assertEqual(gateway_calls[0]["target_id"], "Gateway_2")

    def test_par015_message_catch_execute_then_resume(self):
        workflow_registry.reload()
        rid = _run_id()
        WorkflowRun.objects.create(
            run_id=rid,
            workflow_id="par015_message_runner",
            workflow_name="PAR015 message",
            status=WorkflowRun.STATUS_PENDING,
            user_id=9,
            input_data={},
        )
        asyncio.run(execute_workflow_run(rid, send_message=None))
        run = WorkflowRun.objects.get(run_id=rid)
        self.assertEqual(run.status, WorkflowRun.STATUS_WAITING_BPMN_MESSAGE)
        pd = run.progress_data or {}
        self.assertEqual(pd.get("next_step"), "msg_catch")
        eng = normalize_engine_state(pd.get("engine_state"))
        eng["satisfied_intermediate_messages"] = ["ext_msg"]
        pd["engine_state"] = eng
        run.progress_data = pd
        run.status = WorkflowRun.STATUS_RUNNING
        run.save(update_fields=["progress_data", "status"])
        run.refresh_from_db()
        asyncio.run(resume_bpmn_after_pause(run, send_message=None))
        run.refresh_from_db()
        self.assertEqual(run.status, WorkflowRun.STATUS_COMPLETED)
        steps = (run.output_data or {}).get("workflow_steps") or []
        self.assertIn("task_msg_b", steps)

    def test_execute_pauses_and_persists_progress(self):
        rid = _run_id()
        WorkflowRun.objects.create(
            run_id=rid,
            workflow_id="runner_integration_test",
            workflow_name="RIT",
            status=WorkflowRun.STATUS_PENDING,
            user_id=9,
            input_data={},
        )
        asyncio.run(execute_workflow_run(rid, send_message=None))
        run = WorkflowRun.objects.get(run_id=rid)
        self.assertEqual(run.status, WorkflowRun.STATUS_WAITING_FOR_TASK)
        self.assertIsNotNone(run.progress_data)
        pd = run.progress_data
        self.assertEqual(pd.get("next_step"), "task_b")
        self.assertIn("engine_state", pd)
        self.assertIn("state_data", pd)
        self.assertEqual(pd.get("state_class"), "RunnerIntegrationTestState")
        eng = pd.get("engine_state") or {}
        self.assertIn("task_a", eng.get("completed_node_ids", []))
        self.assertEqual(eng.get("current_node_ids"), ["task_b"])

    def test_resume_completes_via_runner(self):
        rid = _run_id()
        WorkflowRun.objects.create(
            run_id=rid,
            workflow_id="runner_integration_test",
            workflow_name="RIT",
            status=WorkflowRun.STATUS_PENDING,
            user_id=9,
            input_data={},
        )
        asyncio.run(execute_workflow_run(rid, send_message=None))
        run = WorkflowRun.objects.get(run_id=rid)
        self.assertEqual(run.status, WorkflowRun.STATUS_WAITING_FOR_TASK)

        run.status = WorkflowRun.STATUS_PENDING
        run.save(update_fields=["status"])

        asyncio.run(resume_bpmn_after_pause(run, send_message=None))
        run.refresh_from_db()
        self.assertEqual(run.status, WorkflowRun.STATUS_COMPLETED)
        self.assertIsNotNone(run.output_data)
        steps = run.output_data.get("workflow_steps") or []
        self.assertIn("task_b", steps)

    def test_failure_persists_metadata_through_runner(self):
        rid = _run_id()
        WorkflowRun.objects.create(
            run_id=rid,
            workflow_id="runner_integration_test",
            workflow_name="RIT",
            status=WorkflowRun.STATUS_PENDING,
            user_id=9,
            input_data={},
        )
        bpmn, _ = _get_bindings_and_bpmn("runner_integration_test")
        bad_bindings = normalize_bindings(
            {
                "workflow_id": "runner_integration_test",
                "serviceTasks": {"task_b": {"handler": "task_b"}},
            },
            workflow_id="runner_integration_test",
            executor="workflows.runner_integration_test.workflow.RunnerIntegrationTestWorkflow",
        )

        def _bad_bindings(wid):
            return bpmn, bad_bindings

        with patch("agent_app.workflow_runner._get_bindings_and_bpmn", side_effect=_bad_bindings):
            asyncio.run(execute_workflow_run(rid, send_message=None))

        run = WorkflowRun.objects.get(run_id=rid)
        self.assertEqual(run.status, WorkflowRun.STATUS_FAILED)
        pd = run.progress_data or {}
        self.assertEqual(pd.get("failure_reason"), "missing_binding")
        self.assertEqual(pd.get("failed_node_id"), "task_a")

    def test_pause_persists_multi_current_from_active_tokens(self):
        """_handle_workflow_paused uses current_node_ids_for_progress (multi-token)."""

        class _PauseState:
            __class__ = type("PauseMultiState", (), {})

            def __init__(self):
                self.__dict__["_bpmn_engine_state"] = {
                    "completed_node_ids": ["t0"],
                    "current_node_ids": ["legacy_only"],
                    "active_tokens": [
                        {"current_element_id": "branch_a", "branch_id": "b1"},
                        {"current_element_id": "branch_b", "branch_id": "b2"},
                    ],
                }

            def model_dump(self):
                return {"workflow_steps": ["t0"]}

        rid = _run_id()
        WorkflowRun.objects.create(
            run_id=rid,
            workflow_id="runner_integration_test",
            workflow_name="RIT",
            status=WorkflowRun.STATUS_WAITING_FOR_TASK,
            user_id=9,
            input_data={},
        )
        st = _PauseState()
        exc = TaskPendingError("ht1", "human_task", st, "branch_a")
        asyncio.run(_handle_workflow_paused(rid, exc, send_message=None))
        run = WorkflowRun.objects.get(run_id=rid)
        self.assertEqual(
            run.progress_data.get("current_node_ids"),
            ["branch_a", "branch_b"],
        )

    def test_resume_second_pause_sets_waiting_for_task(self):
        """After resume, another TaskPendingError must not mark the run failed."""
        rid = _run_id()
        WorkflowRun.objects.create(
            run_id=rid,
            workflow_id="runner_integration_test",
            workflow_name="RIT",
            status=WorkflowRun.STATUS_PENDING,
            user_id=9,
            input_data={},
        )
        asyncio.run(execute_workflow_run(rid, send_message=None))
        run = WorkflowRun.objects.get(run_id=rid)
        self.assertEqual(run.status, WorkflowRun.STATUS_WAITING_FOR_TASK)
        run.status = WorkflowRun.STATUS_PENDING
        run.save(update_fields=["status"])

        async def pause_again(executor_instance, state, bpmn, bindings, **kwargs):
            raise TaskPendingError(
                "second_pause_task",
                "human",
                state,
                "task_after_second",
            )

        with patch("agent_app.workflow_runner.run_bpmn_workflow", side_effect=pause_again):
            asyncio.run(resume_bpmn_after_pause(run, send_message=None))

        run.refresh_from_db()
        self.assertEqual(run.status, WorkflowRun.STATUS_WAITING_FOR_TASK)
        pd = run.progress_data or {}
        self.assertEqual(pd.get("next_step"), "task_after_second")
        self.assertIn("second_pause_task", pd.get("pending_tasks") or [])

    def test_resume_bpmn_engine_error_persists_progress(self):
        rid = _run_id()
        WorkflowRun.objects.create(
            run_id=rid,
            workflow_id="runner_integration_test",
            workflow_name="RIT",
            status=WorkflowRun.STATUS_PENDING,
            user_id=9,
            input_data={},
        )
        asyncio.run(execute_workflow_run(rid, send_message=None))
        run = WorkflowRun.objects.get(run_id=rid)
        run.status = WorkflowRun.STATUS_PENDING
        run.save(update_fields=["status"])

        async def engine_fail(executor_instance, state, bpmn, bindings, **kwargs):
            raise BpmnEngineError(
                "gateway stuck",
                state=state,
                failure_reason="exclusive_gateway_no_match",
                failed_node_id="gw_resume",
                condition_failure_metadata={"edge": "e1"},
            )

        with patch("agent_app.workflow_runner.run_bpmn_workflow", side_effect=engine_fail):
            asyncio.run(resume_bpmn_after_pause(run, send_message=None))

        run.refresh_from_db()
        self.assertEqual(run.status, WorkflowRun.STATUS_FAILED)
        pd = run.progress_data or {}
        self.assertEqual(pd.get("failure_reason"), "exclusive_gateway_no_match")
        self.assertEqual(pd.get("failed_node_id"), "gw_resume")
        self.assertEqual(pd.get("condition_failure_metadata"), {"edge": "e1"})

    def test_runner_retry_state_survives_resume(self):
        rid = _run_id()
        WorkflowRun.objects.create(
            run_id=rid,
            workflow_id="runner_integration_test",
            workflow_name="RIT",
            status=WorkflowRun.STATUS_PENDING,
            user_id=9,
            input_data={"retry_resume_test": True, "bpmn_max_task_retries": 2},
        )
        asyncio.run(execute_workflow_run(rid, send_message=None))
        run = WorkflowRun.objects.get(run_id=rid)
        self.assertEqual(run.status, WorkflowRun.STATUS_WAITING_FOR_TASK)
        trc = (run.progress_data or {}).get("engine_state", {}).get("task_retry_counts") or {}
        self.assertEqual(trc.get("_|task_b"), 1)

        run.status = WorkflowRun.STATUS_PENDING
        run.save(update_fields=["status"])
        asyncio.run(resume_bpmn_after_pause(run, send_message=None))
        run.refresh_from_db()
        self.assertEqual(run.status, WorkflowRun.STATUS_COMPLETED)

    def test_runner_retry_exhausted_persists_metadata(self):
        rid = _run_id()
        WorkflowRun.objects.create(
            run_id=rid,
            workflow_id="runner_integration_test",
            workflow_name="RIT",
            status=WorkflowRun.STATUS_PENDING,
            user_id=9,
            input_data={
                "retry_resume_test": True,
                "bpmn_max_task_retries": 0,
            },
        )
        asyncio.run(execute_workflow_run(rid, send_message=None))
        run = WorkflowRun.objects.get(run_id=rid)
        self.assertEqual(run.status, WorkflowRun.STATUS_FAILED)
        pd = run.progress_data or {}
        self.assertEqual(pd.get("failure_reason"), "retry_exhausted")
        self.assertEqual(pd.get("failed_node_id"), "task_b")
        self.assertEqual(pd.get("retry_attempts"), 1)


class RunnerParallelFjIntegrationTests(TransactionTestCase):
    """Fork/join BPMN via execute_workflow_run / resume_bpmn_after_pause (runner_parallel_fj_test)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        workflow_registry.reload()

    def test_runner_parallel_fork_join_completes(self):
        rid = _run_id()
        WorkflowRun.objects.create(
            run_id=rid,
            workflow_id="runner_parallel_fj_test",
            workflow_name="PFJ",
            status=WorkflowRun.STATUS_PENDING,
            user_id=9,
            input_data={},
        )
        asyncio.run(execute_workflow_run(rid, send_message=None))
        run = WorkflowRun.objects.get(run_id=rid)
        self.assertEqual(run.status, WorkflowRun.STATUS_COMPLETED)
        out = run.output_data or {}
        steps = out.get("workflow_steps") or []
        self.assertIn("taskAfter", steps)
        self.assertIn("task0", steps)
        self.assertIn("taskA", steps)
        self.assertIn("taskB", steps)
        eng = (run.progress_data or {}).get("engine_state") or {}
        self.assertEqual(eng.get("pending_joins") or {}, {})
        tokens = eng.get("active_tokens") or []
        cur = {t.get("current_element_id") for t in tokens if isinstance(t, dict)}
        self.assertTrue(
            len(cur) == 0 or cur == {None} or "end" in cur,
            msg=f"expected drained tokens after end, got {cur!r}",
        )

    def test_runner_parallel_pause_before_join_then_resume(self):
        rid = _run_id()
        WorkflowRun.objects.create(
            run_id=rid,
            workflow_id="runner_parallel_fj_test",
            workflow_name="PFJ",
            status=WorkflowRun.STATUS_PENDING,
            user_id=9,
            input_data={"pause_on_task_b": True},
        )
        asyncio.run(execute_workflow_run(rid, send_message=None))
        run = WorkflowRun.objects.get(run_id=rid)
        self.assertEqual(run.status, WorkflowRun.STATUS_WAITING_FOR_TASK)
        pd = run.progress_data or {}
        self.assertEqual(pd.get("next_step"), "taskB")
        cur_ids = set(pd.get("current_node_ids") or [])
        self.assertIn("joinGW", cur_ids)
        self.assertIn("taskB", cur_ids)
        eng = pd.get("engine_state") or {}
        self.assertEqual(len(eng.get("active_tokens") or []), 2)
        self.assertIn("joinGW", (eng.get("pending_joins") or {}))

        pd2 = dict(pd)
        sd = dict(pd2.get("state_data") or {})
        sd["pause_on_task_b"] = False
        pd2["state_data"] = sd
        run.progress_data = pd2
        run.status = WorkflowRun.STATUS_PENDING
        run.save(update_fields=["progress_data", "status"])

        asyncio.run(resume_bpmn_after_pause(run, send_message=None))
        run.refresh_from_db()
        self.assertEqual(run.status, WorkflowRun.STATUS_COMPLETED)
        steps = (run.output_data or {}).get("workflow_steps") or []
        self.assertIn("taskAfter", steps)
        eng2 = (run.progress_data or {}).get("engine_state") or {}
        self.assertEqual(eng2.get("pending_joins") or {}, {})

    def test_runner_parallel_resume_with_branch_waiting_at_join(self):
        rid = _run_id()
        eng = {
            "active_tokens": [
                {"current_element_id": "joinGW", "branch_id": "forkGW:ffa"},
                {"current_element_id": "taskB", "branch_id": "forkGW:ffb"},
            ],
            "pending_joins": {
                "joinGW": {
                    "fork_id": "forkGW",
                    "join_element_id": "joinGW",
                    "expected_branch_ids": ["forkGW:ffa", "forkGW:ffb"],
                    "arrived_branch_ids": ["forkGW:ffa"],
                }
            },
            "completed_node_ids": ["task0", "taskA", "forkGW"],
            "current_node_ids": ["joinGW", "taskB"],
        }
        WorkflowRun.objects.create(
            run_id=rid,
            workflow_id="runner_parallel_fj_test",
            workflow_name="PFJ",
            status=WorkflowRun.STATUS_PENDING,
            user_id=9,
            input_data={},
            progress_data={
                "state_class": "RunnerParallelFjState",
                "state_data": {
                    "workflow_steps": ["task0", "taskA"],
                    "pause_on_task_b": False,
                    "fail_branch_b": False,
                },
                "next_step": "taskB",
                "engine_state": eng,
            },
        )
        run = WorkflowRun.objects.get(run_id=rid)
        asyncio.run(resume_bpmn_after_pause(run, send_message=None))
        run.refresh_from_db()
        self.assertEqual(run.status, WorkflowRun.STATUS_COMPLETED)
        steps = (run.output_data or {}).get("workflow_steps") or []
        self.assertIn("taskAfter", steps)
        eng2 = (run.progress_data or {}).get("engine_state") or {}
        self.assertEqual(eng2.get("pending_joins") or {}, {})

    def test_runner_parallel_branch_failure_preserves_join_state(self):
        rid = _run_id()
        WorkflowRun.objects.create(
            run_id=rid,
            workflow_id="runner_parallel_fj_test",
            workflow_name="PFJ",
            status=WorkflowRun.STATUS_PENDING,
            user_id=9,
            input_data={"fail_branch_b": True},
        )
        asyncio.run(execute_workflow_run(rid, send_message=None))
        run = WorkflowRun.objects.get(run_id=rid)
        self.assertEqual(run.status, WorkflowRun.STATUS_FAILED)
        pd = run.progress_data or {}
        self.assertEqual(pd.get("failed_node_id"), "taskB")
        self.assertEqual(pd.get("failure_reason"), "handler_error")
        self.assertIn("branch_b", run.error_message or "")
        eng = pd.get("engine_state") or {}
        self.assertIn("joinGW", eng.get("pending_joins") or {})
        cur = {t.get("current_element_id") for t in (eng.get("active_tokens") or [])}
        self.assertIn("joinGW", cur)
        self.assertIn("taskB", cur)

    def test_runner_parallel_join_clears_pending_joins_on_completion(self):
        rid = _run_id()
        WorkflowRun.objects.create(
            run_id=rid,
            workflow_id="runner_parallel_fj_test",
            workflow_name="PFJ",
            status=WorkflowRun.STATUS_PENDING,
            user_id=9,
            input_data={},
        )
        asyncio.run(execute_workflow_run(rid, send_message=None))
        run = WorkflowRun.objects.get(run_id=rid)
        self.assertEqual(run.status, WorkflowRun.STATUS_COMPLETED)
        eng = (run.progress_data or {}).get("engine_state") or {}
        self.assertEqual(
            eng.get("pending_joins") or {},
            {},
            "pending_joins must be empty after successful join completion",
        )

    def test_runner_parallel_cancelled_before_join_completion(self):
        rid = _run_id()
        n = [0]

        def abort_check(r):
            n[0] += 1
            if n[0] >= 3:
                return "cancelled"
            return _execution_abort_reason_sync(r)

        WorkflowRun.objects.create(
            run_id=rid,
            workflow_id="runner_parallel_fj_test",
            workflow_name="PFJ",
            status=WorkflowRun.STATUS_PENDING,
            user_id=9,
            input_data={},
        )
        with patch(
            "agent_app.workflow_runner._execution_abort_reason_sync",
            side_effect=abort_check,
        ):
            asyncio.run(execute_workflow_run(rid, send_message=None))
        run = WorkflowRun.objects.get(run_id=rid)
        self.assertEqual(run.status, WorkflowRun.STATUS_CANCELLED)
        pd = run.progress_data or {}
        self.assertEqual(pd.get("failure_reason"), "cancelled")
        eng = pd.get("engine_state") or {}
        self.assertIn("joinGW", eng.get("pending_joins") or {})
        cur = {t.get("current_element_id") for t in (eng.get("active_tokens") or [])}
        self.assertIn("joinGW", cur)
        self.assertIn("taskB", cur)

    def test_runner_parallel_timeout_with_branch_waiting_at_join(self):
        rid = _run_id()
        n = [0]

        def abort_check(r):
            n[0] += 1
            if n[0] >= 3:
                return "timeout"
            return _execution_abort_reason_sync(r)

        WorkflowRun.objects.create(
            run_id=rid,
            workflow_id="runner_parallel_fj_test",
            workflow_name="PFJ",
            status=WorkflowRun.STATUS_PENDING,
            user_id=9,
            input_data={"execution_timeout_seconds": 3600},
        )
        with patch(
            "agent_app.workflow_runner._execution_abort_reason_sync",
            side_effect=abort_check,
        ):
            asyncio.run(execute_workflow_run(rid, send_message=None))
        run = WorkflowRun.objects.get(run_id=rid)
        self.assertEqual(run.status, WorkflowRun.STATUS_FAILED)
        pd = run.progress_data or {}
        self.assertEqual(pd.get("failure_reason"), "timeout")
        self.assertEqual(pd.get("timeout_seconds"), 3600)
        self.assertIsNotNone(pd.get("timed_out_at"))
        eng = pd.get("engine_state") or {}
        self.assertIn("joinGW", eng.get("pending_joins") or {})

    def test_resume_cancelled_workflow_raises(self):
        rid = _run_id()
        WorkflowRun.objects.create(
            run_id=rid,
            workflow_id="runner_integration_test",
            workflow_name="RIT",
            status=WorkflowRun.STATUS_PENDING,
            user_id=9,
            input_data={},
        )
        asyncio.run(execute_workflow_run(rid, send_message=None))
        run = WorkflowRun.objects.get(run_id=rid)
        self.assertEqual(run.status, WorkflowRun.STATUS_WAITING_FOR_TASK)
        run.status = WorkflowRun.STATUS_CANCELLED
        run.save(update_fields=["status"])
        with self.assertRaises(ValueError) as ctx:
            asyncio.run(resume_bpmn_after_pause(run, send_message=None))
        self.assertIn("cancelled", str(ctx.exception).lower())
