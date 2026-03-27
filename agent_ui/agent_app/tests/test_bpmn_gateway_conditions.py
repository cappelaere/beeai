"""Targeted tests for production BPMN exclusive-gateway conditions/defaults."""

from pathlib import Path
from types import SimpleNamespace

from django.test import TestCase

from agent_app.bpmn_engine import select_exclusive_flow
from agent_app.workflow_context import parse_bpmn_xml, validate_exclusive_gateway_semantics
from agent_app.workflow_registry import REPO_ROOT


def _load_bpmn(relative_path: str) -> dict:
    xml = (Path(REPO_ROOT) / relative_path).read_text()
    return parse_bpmn_xml(xml)


class BidderOnboardingGatewayTests(TestCase):
    def test_gateway_conditions_are_parseable(self):
        bpmn = _load_bpmn("workflows/bidder_onboarding/currentVersion/workflow.bpmn")
        errs = validate_exclusive_gateway_semantics(bpmn)
        self.assertFalse(
            any("Gateway 'Gateway_SAM_Decision'" in err for err in errs),
            msg=f"unexpected gateway validation errors: {errs}",
        )

    def test_gateway_routes_yes_when_sam_passed_true(self):
        bpmn = _load_bpmn("workflows/bidder_onboarding/currentVersion/workflow.bpmn")
        state = SimpleNamespace(sam_passed=True)
        target = select_exclusive_flow(bpmn, "Gateway_SAM_Decision", state, {})
        self.assertEqual(target, "check_ofac_compliance")

    def test_gateway_routes_no_when_sam_passed_false(self):
        bpmn = _load_bpmn("workflows/bidder_onboarding/currentVersion/workflow.bpmn")
        state = SimpleNamespace(sam_passed=False)
        target = select_exclusive_flow(bpmn, "Gateway_SAM_Decision", state, {})
        self.assertEqual(target, "finalize_status")


class DapReportGatewayTests(TestCase):
    def test_gateway_conditions_are_parseable(self):
        bpmn = _load_bpmn("workflows/dap_report/currentVersion/workflow.bpmn")
        errs = validate_exclusive_gateway_semantics(bpmn)
        self.assertFalse(
            any("Gateway 'Gateway_1'" in err for err in errs),
            msg=f"unexpected gateway validation errors: {errs}",
        )

    def test_gateway_routes_yes_when_issues_present(self):
        bpmn = _load_bpmn("workflows/dap_report/currentVersion/workflow.bpmn")
        state = SimpleNamespace(has_issues=True)
        target = select_exclusive_flow(bpmn, "Gateway_1", state, {})
        self.assertEqual(target, "resolve_issue")

    def test_gateway_routes_no_when_no_issues(self):
        bpmn = _load_bpmn("workflows/dap_report/currentVersion/workflow.bpmn")
        state = SimpleNamespace(has_issues=False)
        target = select_exclusive_flow(bpmn, "Gateway_1", state, {})
        self.assertEqual(target, "Gateway_2")

    def test_gateway_uses_default_when_state_value_missing(self):
        bpmn = _load_bpmn("workflows/dap_report/currentVersion/workflow.bpmn")
        state = SimpleNamespace()
        target = select_exclusive_flow(bpmn, "Gateway_1", state, {})
        self.assertEqual(target, "Gateway_2")
