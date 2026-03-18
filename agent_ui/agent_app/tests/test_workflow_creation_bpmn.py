"""
Workflow creation test: creating a workflow produces currentVersion/workflow.bpmn
and currentVersion/bpmn-bindings.yaml with expected structure.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import yaml
from django.test import TestCase

from agent_app.services import workflow_service

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

MINIMAL_WORKFLOW_PY = '''
"""Test workflow for creation test."""
from pydantic import BaseModel, Field

class TestCreateState(BaseModel):
    request_data: str = Field(description="Input")

class TestCreateWorkflow:
    async def task1(self, state):
        return None
    async def task2(self, state):
        return None
'''


class WorkflowCreationBpmnTests(TestCase):
    """Workflow creation produces BPMN and bindings in currentVersion/ with expected structure."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="beeai_workflow_test_")
        self.repo_root = Path(self.tmp)
        (self.repo_root / "context").mkdir(parents=True, exist_ok=True)
        (self.repo_root / "context" / "CONTEXT.md").write_text("Context")
        (self.repo_root / "context" / "WORKFLOW_GUIDELINES.md").write_text("Guidelines")

    def tearDown(self):
        import shutil

        try:
            shutil.rmtree(self.tmp, ignore_errors=True)
        except Exception:
            pass

    @patch("agent_app.workflow_registry.workflow_registry", new_callable=MagicMock)
    @patch.object(workflow_service, "_generate_workflow_code")
    @patch.object(workflow_service, "_generate_readme")
    @patch.object(workflow_service, "_generate_bpmn")
    @patch.object(workflow_service, "_generate_user_story")
    def test_create_workflow_produces_bpmn_and_bindings(
        self,
        mock_user_story,
        mock_bpmn,
        mock_readme,
        mock_code,
        mock_registry,
    ):
        original_repo_root = workflow_service.REPO_ROOT
        try:
            workflow_service.REPO_ROOT = self.repo_root
            mock_code.return_value = MINIMAL_WORKFLOW_PY
            mock_readme.return_value = "# Test\n"
            sample_bpmn = (FIXTURES_DIR / "sample.bpmn").read_text()
            mock_bpmn.return_value = (sample_bpmn, ["task1", "task2"])
            mock_user_story.return_value = "# User Story: Test\n"

            workflow_id = "test_create_workflow_bpmn"
            workflow_service.create_workflow(
                name="Test Create Workflow",
                workflow_id=workflow_id,
                icon="🔄",
                category="Testing",
                description="Test",
                prompt="Minimal prompt",
                model_short_key="claude-sonnet-4",
            )

            workflow_dir = self.repo_root / "workflows" / workflow_id
            self.assertTrue(workflow_dir.exists(), "Workflow dir should exist")
            current = workflow_dir / "currentVersion"
            self.assertTrue(current.exists(), "currentVersion/ should exist")
            bpmn_path = current / "workflow.bpmn"
            bindings_path = current / "bpmn-bindings.yaml"
            self.assertTrue(bpmn_path.exists(), "currentVersion/workflow.bpmn should exist")
            self.assertTrue(
                bindings_path.exists(), "currentVersion/bpmn-bindings.yaml should exist"
            )

            bindings = yaml.safe_load(bindings_path.read_text())
            self.assertEqual(bindings.get("workflow_id"), workflow_id)
            self.assertIn("executor", bindings)
            self.assertIn("serviceTasks", bindings)
            st = bindings["serviceTasks"]
            self.assertIn("task1", st)
            self.assertIn("task2", st)
            self.assertEqual(st["task1"].get("handler"), "task1")
            self.assertEqual(st["task2"].get("handler"), "task2")

            bpmn_xml = bpmn_path.read_text()
            self.assertIn("task1", bpmn_xml)
            self.assertIn("serviceTask", bpmn_xml)
        finally:
            workflow_service.REPO_ROOT = original_repo_root
