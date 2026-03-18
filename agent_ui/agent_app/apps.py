import logging
import os

from django.apps import AppConfig

logger = logging.getLogger(__name__)
_SKIP_STARTUP_COMMANDS = frozenset({"check", "migrate", "makemigrations", "shell", "test"})


def run_startup_checks() -> None:
    """
    Run environment and registry checks on startup. Log one consolidated
    summary of failures and warnings. Non-fatal for optional deps; required
    paths (agents.yaml, workflows dir) are logged as errors but do not block startup.
    """
    failed: list[str] = []
    warnings: list[str] = []

    # Critical paths
    try:
        from agents.registry import get_registry_path

        registry_path = get_registry_path()
        if not registry_path.exists():
            failed.append(f"Agent registry not found: {registry_path}")
    except Exception as e:
        failed.append(f"Agent registry path check failed: {e}")

    try:
        from agent_app.workflow_registry import REPO_ROOT

        workflows_dir = REPO_ROOT / "workflows"
        if not workflows_dir.is_dir():
            failed.append(f"Workflows directory not found: {workflows_dir}")
    except Exception as e:
        failed.append(f"Workflows path check failed: {e}")

    # Optional: Langfuse env when observability enabled
    if os.getenv("LANGFUSE_ENABLED", "false").lower() in ("true", "1", "yes"):
        if not os.getenv("LANGFUSE_PUBLIC_KEY") or not os.getenv("LANGFUSE_SECRET_KEY"):
            warnings.append(
                "LANGFUSE_ENABLED is set but LANGFUSE_PUBLIC_KEY or LANGFUSE_SECRET_KEY is missing"
            )

    # Optional: piper_tts (lazy import is fine; we only check module loads)
    try:
        import sys
        from pathlib import Path

        # piper_tts may live in repo; ensure it's on path for import
        repo_root = Path(__file__).resolve().parent.parent.parent
        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))
        import piper_tts.app.tts_engine  # noqa: F401
    except ModuleNotFoundError:
        warnings.append("Optional: piper_tts.app.tts_engine not importable (piper TTS disabled)")
    except Exception as e:
        warnings.append(f"Optional: piper_tts check failed: {e}")

    # YAML/metadata schema validation
    try:
        from agent_app.schema_validation import validate_all_metadata

        schema_errors, schema_warnings = validate_all_metadata()
        failed.extend(schema_errors)
        warnings.extend(schema_warnings)
    except Exception as e:
        failed.append(f"Schema validation failed: {e}")

    # Log consolidated summary
    if failed:
        logger.error("Startup checks — failures: %s", failed)
    if warnings:
        logger.warning("Startup checks — warnings: %s", warnings)
    if not failed and not warnings:
        logger.info("Startup checks: all passed (paths and optional deps)")


def _log_agent_validation_results(validation_results):
    """Log agent registry validation results."""
    if validation_results["valid"]:
        logger.info(
            f"✅ Agent Registry: {validation_results['checked']} agents validated successfully"
        )
    else:
        logger.error("❌ Agent Registry: Validation failed!")
        for error in validation_results["errors"]:
            logger.error(f"   - {error}")

    for warning in validation_results["warnings"]:
        logger.warning(f"⚠️  Agent Registry: {warning}")

    if validation_results["fixed"] > 0:
        logger.info(f"🔧 Agent Registry: Fixed {validation_results['fixed']} issues")


def _log_workflow_validation_results(workflow_results):
    """Log workflow registry validation results."""
    if workflow_results["valid"]:
        logger.info(
            f"✅ Workflow Registry: {workflow_results['checked']} workflows validated successfully"
        )
    else:
        logger.error("❌ Workflow Registry: Validation failed!")
        for error in workflow_results["errors"]:
            logger.error(f"   - {error}")

    for warning in workflow_results["warnings"]:
        logger.warning(f"⚠️  Workflow Registry: {warning}")


def _validate_agent_registry():
    """Validate agent registry integrity on startup."""
    try:
        from agents.registry import validate_registry_integrity

        logger.info("🔍 Startup: Validating agent registry integrity...")
        validation_results = validate_registry_integrity(fix_issues=True)
        _log_agent_validation_results(validation_results)

    except Exception as e:
        logger.exception("Agent Registry: Validation check failed: %s", e)


def _validate_workflow_registry():
    """Validate workflow registry integrity on startup."""
    try:
        from agent_app.workflow_registry import validate_workflow_integrity

        logger.info("🔍 Startup: Validating workflow registry integrity...")
        workflow_results = validate_workflow_integrity(fix_issues=False)
        _log_workflow_validation_results(workflow_results)

    except Exception as e:
        logger.exception("Workflow Registry: Validation check failed: %s", e)


def _clear_startup_cache():
    """Clear LLM cache on startup."""
    try:
        from cache import get_cache

        cache = get_cache()
        if cache.enabled:
            cache.clear_all()
            logger.info("🔄 Startup: Cleared all cached LLM responses to load fresh agent tools")
        else:
            logger.info("🔄 Startup: Cache not enabled, skipping cache clear")
    except Exception as e:
        logger.warning("Startup: Failed to clear cache: %s", e, exc_info=True)


class AgentAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "agent_app"
    verbose_name = "RealtyIQ Agent"

    def ready(self):
        """
        Called when Django starts up.
        Clear cache on startup to ensure fresh agent responses with latest tools.
        """
        import sys

        # Skip during Django checks and migrations
        if any(arg in _SKIP_STARTUP_COMMANDS for arg in sys.argv):
            return

        run_startup_checks()
        _validate_agent_registry()
        _validate_workflow_registry()
        _clear_startup_cache()
