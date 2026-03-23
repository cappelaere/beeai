"""
Opt-in **diagnostic** runs for catalog BPMN workflows (Issue #7 helper).

These are **not** proof of staging/production success and **not** a substitute for
hosted validation. They only exercise `execute_workflow_run` against the Django
**test** database.

- **Completion checks:** `bi_weekly_report` and `property_due_diligence` must end
  `completed` for the test to pass (local test-DB only).
- **Observability checks:** `bidder_onboarding` and `dap_report` only assert a
  terminal outcome and run-detail HTML markers; failures/timeouts are expected
  until GitHub issue #9 (BPMN gateway) is fixed.

Skipped unless ``ISSUE7_PRODUCT_BPMN_DIAGNOSTIC=1`` (CI stays fast).

Run::

  cd agent_ui && ISSUE7_PRODUCT_BPMN_DIAGNOSTIC=1 ../venv/bin/python manage.py test \\
    agent_app.tests.test_issue7_product_bpmn_diagnostic --settings=agent_ui.settings -v 2
"""

import asyncio
import os
import uuid

from django.test import Client, TransactionTestCase

from agent_app.constants import ANONYMOUS_USER_ID
from agent_app.models import WorkflowRun
from agent_app.workflow_registry import workflow_registry
from agent_app.workflow_runner import execute_workflow_run

_SKIP = os.environ.get("ISSUE7_PRODUCT_BPMN_DIAGNOSTIC", "").lower() not in ("1", "true", "yes")


def _skip_msg():
    return (
        "Set ISSUE7_PRODUCT_BPMN_DIAGNOSTIC=1 to run Issue #7 product BPMN "
        "diagnostic tests (local test DB only; not staging validation)."
    )


class Issue7ProductBpmnDiagnostic(TransactionTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        workflow_registry.reload()

    def setUp(self):
        super().setUp()
        if _SKIP:
            self.skipTest(_skip_msg())

    def _run_workflow(self, workflow_id: str, input_data: dict, *, timeout: float = 240.0):
        rid = uuid.uuid4().hex[:8]
        WorkflowRun.objects.create(
            run_id=rid,
            workflow_id=workflow_id,
            workflow_name=workflow_id,
            status=WorkflowRun.STATUS_PENDING,
            user_id=ANONYMOUS_USER_ID,
            input_data=input_data,
        )

        async def _go():
            await asyncio.wait_for(
                execute_workflow_run(rid, send_message=None),
                timeout=timeout,
            )

        try:
            asyncio.run(_go())
        except TimeoutError:
            return rid, "timeout", None, "asyncio.wait_for exceeded"

        run = WorkflowRun.objects.get(run_id=rid)
        return rid, run.status, run.progress_data, run.error_message

    def _assert_run_detail_contains_bpmn_ui(self, run_id: str):
        client = Client()
        resp = client.get(f"/workflows/runs/{run_id}/")
        self.assertEqual(resp.status_code, 200, msg=getattr(resp, "content", b"")[:500])
        body = resp.content.decode("utf-8", errors="replace")
        self.assertTrue(
            "workflow-diagram-bpmn" in body or "bpmn_operator_panel" in body or "BPMN diagram" in body,
            msg="run detail should include BPMN diagram or operator panel markers",
        )

    def test_bi_weekly_report_completes_local_test_db(self):
        """Local test DB only: must reach completed (not a staging sign-off)."""
        rid, status, _pd, err = self._run_workflow(
            "bi_weekly_report",
            {"start_date": "2025-06-01", "end_date": "2025-06-07"},
        )
        self.assertIsNotNone(rid)
        self.assertEqual(
            status,
            WorkflowRun.STATUS_COMPLETED,
            msg=f"expected completed in test DB; got {status!r} err={err!r}",
        )
        self._assert_run_detail_contains_bpmn_ui(rid)

    def test_property_due_diligence_completes_local_test_db(self):
        """Local test DB only: must reach completed (not a staging sign-off)."""
        rid, status, _pd, err = self._run_workflow(
            "property_due_diligence",
            {"property_id": 1},
        )
        self.assertIsNotNone(rid)
        self.assertEqual(
            status,
            WorkflowRun.STATUS_COMPLETED,
            msg=f"expected completed in test DB; got {status!r} err={err!r}",
        )
        self._assert_run_detail_contains_bpmn_ui(rid)

    def test_bidder_onboarding_bpmn_diagnostic_observability(self):
        """Terminal outcome + run-detail only; known BPMN gateway gaps (issue #9)."""
        rid, status, _pd, err = self._run_workflow(
            "bidder_onboarding",
            {
                "bidder_name": "Issue7 Diagnostic User",
                "property_id": 1,
                "registration_data": {
                    "email": "issue7-bpmn@example.invalid",
                    "phone": "555-0199",
                    "terms_accepted": True,
                    "age_accepted": True,
                },
            },
        )
        self.assertIsNotNone(rid)
        self.assertIn(
            status,
            (
                WorkflowRun.STATUS_COMPLETED,
                WorkflowRun.STATUS_FAILED,
                WorkflowRun.STATUS_WAITING_FOR_TASK,
                "timeout",
            ),
            msg=f"unexpected non-terminal status={status!r} err={err!r}",
        )
        self._assert_run_detail_contains_bpmn_ui(rid)

    def test_dap_report_bpmn_diagnostic_observability(self):
        """Terminal outcome + run-detail only; gateway defect (issue #9)."""
        rid, status, _pd, err = self._run_workflow(
            "dap_report",
            {"report_date": "2025-06-01", "lookback_days": 7},
        )
        self.assertIsNotNone(rid)
        self.assertIn(
            status,
            (
                WorkflowRun.STATUS_COMPLETED,
                WorkflowRun.STATUS_FAILED,
                WorkflowRun.STATUS_WAITING_FOR_TASK,
                "timeout",
            ),
            msg=f"unexpected non-terminal status={status!r} err={err!r}",
        )
        self._assert_run_detail_contains_bpmn_ui(rid)
