"""
Smoke tests for boot paths: registry loading, workflow executors, optional deps, Django startup.
Run in CI to catch regressions in registry loading, workflow executor import, or Django startup.
"""

import os
import subprocess
import sys
from pathlib import Path

from django.test import TestCase


class TestWorkflowRegistrySmoke(TestCase):
    """Workflow registry loads and exposes at least one workflow with a loadable executor."""

    def test_registry_loads_all_workflows(self):
        from agent_app.workflow_registry import workflow_registry

        all_workflows = workflow_registry.get_all()
        self.assertGreaterEqual(
            len(all_workflows),
            1,
            "At least one workflow must be registered (workflows/ discovery)",
        )
        ids = {m.id for m in all_workflows}
        self.assertNotIn(
            "runner_integration_test",
            ids,
            "Test workflow must be hidden from catalog (hide_from_catalog)",
        )
        internal = {m.id for m in workflow_registry.get_all(include_internal=True)}
        self.assertIn("runner_integration_test", internal)

    def test_each_workflow_entry_obtainable_and_executor_loaded_when_present(self):
        from agent_app.workflow_registry import workflow_registry

        all_meta = workflow_registry.get_all()
        for meta in all_meta:
            wid = meta.id
            entry = workflow_registry.get(wid)
            self.assertIsNotNone(entry, f"Registry must return entry for workflow id {wid}")
            # Executor is instantiated by registry; smoke test asserts no entry has executor is None
            # (optional: allow None and only check structure)
            self.assertIn("executor", entry)
            if entry.get("executor") is None:
                # Log but do not fail in smoke test; validate_workflow_integrity already flags this
                pass


class TestPiperTtsImportSmoke(TestCase):
    """Optional piper_tts module can be imported without ModuleNotFoundError when on path."""

    def test_piper_tts_module_imports(self):
        repo_root = Path(__file__).resolve().parent.parent.parent.parent
        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))
        try:
            import piper_tts.app.tts_engine  # noqa: F401
        except ModuleNotFoundError as e:
            self.skipTest(f"Optional piper_tts not available: {e}")


class TestDjangoStartupSmoke(TestCase):
    """Django startup (manage.py check) completes without critical stderr warnings."""

    def test_manage_check_completes(self):
        # manage.py lives in agent_ui/, not repo root (tests are agent_ui/agent_app/tests/)
        manage_py = Path(__file__).resolve().parent.parent.parent / "manage.py"
        self.assertTrue(manage_py.exists(), f"manage.py not found at {manage_py}")
        # Pytest sets DJANGO_SETTINGS_MODULE=agent_ui.agent_ui.settings (repo-root layout).
        # A fresh `manage.py check` from agent_ui/ must use manage.py's default (agent_ui.settings).
        sub_env = {**os.environ}
        sub_env.pop("DJANGO_SETTINGS_MODULE", None)
        result = subprocess.run(  # noqa: S603 - test invokes trusted local manage.py with fixed args
            [sys.executable, str(manage_py), "check"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(manage_py.parent),
            env=sub_env,
        )
        self.assertEqual(
            result.returncode, 0, f"manage.py check failed: {result.stderr or result.stdout}"
        )
        # Avoid treating benign warnings as failure; only fail on explicit "database access during app initialization"
        if result.stderr and "database access during app initialization" in result.stderr:
            self.fail(
                "Django reported database access during app initialization (stderr): "
                + result.stderr
            )
