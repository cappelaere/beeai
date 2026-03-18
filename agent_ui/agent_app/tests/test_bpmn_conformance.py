"""BPMN conformance fixtures: validation, happy-path execution, pause/resume, failure metadata."""

from __future__ import annotations

from django.test import TestCase

from agent_app.tests.bpmn_conformance.fixtures import (
    EXECUTION_COMPLETE_FIXTURES,
    FAILURE_METADATA_FIXTURE_IDS,
    PAUSE_RESUME_FIXTURES,
    VALIDATION_FIXTURES,
    execution_fixture_by_id,
)
from agent_app.tests.bpmn_conformance.harness import (
    run_execution_fixture,
    run_pause_resume_fixture,
    run_validation_fixture,
)


class BpmnConformanceTests(TestCase):
    def test_bpmn_validation_fixtures(self):
        for f in VALIDATION_FIXTURES:
            with self.subTest(fixture_id=f.id):
                run_validation_fixture(f)

    def test_bpmn_execution_fixtures(self):
        for f in EXECUTION_COMPLETE_FIXTURES:
            with self.subTest(fixture_id=f.id):
                run_execution_fixture(f)

    def test_bpmn_pause_resume_fixtures(self):
        for f in PAUSE_RESUME_FIXTURES:
            with self.subTest(fixture_id=f.id):
                run_pause_resume_fixture(f)

    def test_bpmn_failure_metadata_fixtures(self):
        for fid in sorted(FAILURE_METADATA_FIXTURE_IDS):
            f = execution_fixture_by_id(fid)
            with self.subTest(fixture_id=f.id):
                run_execution_fixture(f)
