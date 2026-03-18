"""
Workflow Registry for RealtyIQ

Central registry of all available BeeAI workflows with metadata,
input schemas, and executor references.

Auto-discovers workflows from the workflows/ directory by scanning
for metadata.yaml files.
"""

import logging
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml

# Version subfolder pattern: v1, v2, ... or currentVersion (preferred name for working copy)
VERSION_SUBFOLDER_PATTERN = re.compile(r"^v(\d+)$")
CURRENT_VERSION_FOLDER = "currentVersion"

logger = logging.getLogger(__name__)


def _resolve_repo_root() -> Path:
    """
    Root directory that contains ``workflows/`` (the workflow packages).

    ``agent_app`` may live at ``…/beeai/agent_ui/agent_app``; walking up a fixed
    number of parents can land on ``…/CloudDocs`` instead of ``…/beeai``. Scan
    upward for the first directory whose ``workflows/`` subfolder looks like our
    registry (at least one subdir with ``metadata.yaml``).
    """
    here = Path(__file__).resolve().parent

    def _looks_like_workflows_registry(w: Path) -> bool:
        if not w.is_dir():
            return False
        try:
            for d in w.iterdir():
                if d.is_dir() and not d.name.startswith(".") and (d / "metadata.yaml").is_file():
                    return True
        except OSError:
            return False
        return False

    for p in (here, *here.parents):
        if _looks_like_workflows_registry(p / "workflows"):
            return p

    # Fallback: previous behavior (repo root = parent of agent_ui)
    return here.parent.parent.parent


# Add repo root to path for ``import workflows.*``
REPO_ROOT = _resolve_repo_root()
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@dataclass
class WorkflowMetadata:
    """Metadata for a registered workflow"""

    id: str
    name: str
    description: str
    icon: str
    diagram_mermaid: str  # Deprecated; always "" (we use BPMN only)
    input_schema: dict
    category: str
    estimated_duration: str
    workflow_number: int  # Numerical ID for display (e.g., 1, 2, 3)
    documentation_path: str | None = None  # Path to detailed documentation file
    diagram_bpmn_xml: str | None = None  # BPMN 2.0 XML (workflow.bpmn)
    current_version_path: Path | None = None  # e.g. workflow_path / "v1"; None if flat layout
    outputs: list = field(default_factory=list)  # List of {name, type} for end component
    hide_from_catalog: bool = False  # True for test-only workflows; excluded from get_all()

    def to_dict(self):
        """Convert to dictionary for template rendering"""
        d = asdict(self)
        # Path not JSON-serializable
        if "current_version_path" in d and d["current_version_path"] is not None:
            d["current_version_path"] = str(d["current_version_path"])
        return d


class WorkflowRegistry:
    """
    Registry of all available workflows.

    Auto-discovers workflows from the workflows/ directory by scanning
    for metadata.yaml files and attempting to import workflow implementations.
    """

    def __init__(self):
        self.workflows = {}
        self._auto_discover_workflows()
        # Do not call _sync_workflow_model() here: DB sync runs on first DB connection
        # (connection_created in apps.py) and on explicit reload(), to avoid Django's
        # "Accessing the database during app initialization" warning.

    def _should_skip_path(self, workflow_path):
        """Check if workflow path should be skipped during discovery."""
        if not workflow_path.is_dir():
            return True
        if workflow_path.name.startswith("."):
            return True
        return workflow_path.name in ["__pycache__", "docs", "templates", ".versions"]

    def _resolve_current_version_path(self, workflow_path: Path) -> tuple[Path | None, Path]:
        """
        Resolve the directory that contains workflow assets (BPMN).
        Prefer currentVersion folder if present; else version subfolders (v1, v2, ...); else workflow root.
        Returns (version_path_or_none, path_to_use). path_to_use is where to look for workflow.bpmn.
        """
        current_version_path = workflow_path / CURRENT_VERSION_FOLDER
        if current_version_path.is_dir():
            return (current_version_path, current_version_path)
        version_dirs = []
        for p in workflow_path.iterdir():
            if p.is_dir() and VERSION_SUBFOLDER_PATTERN.match(p.name):
                version_dirs.append(p)
        if version_dirs:
            # Sort by version number (v2 > v1)
            version_dirs.sort(key=lambda p: int(VERSION_SUBFOLDER_PATTERN.match(p.name).group(1)))
            current = version_dirs[-1]
            return (current, current)
        return (None, workflow_path)

    def _load_bpmn_if_present(self, base_path: Path) -> str | None:
        """Load workflow.bpmn from base_path (version folder or workflow root). Return None if missing."""
        bpmn_file = base_path / "workflow.bpmn"
        if bpmn_file.exists():
            return bpmn_file.read_text()
        return None

    def _load_workflow_metadata(self, workflow_path, metadata_dict, workflow_number):
        """Load and create workflow metadata object."""
        workflow_id = metadata_dict.get("id", workflow_path.name)

        version_path, assets_path = self._resolve_current_version_path(workflow_path)
        diagram_bpmn_xml = self._load_bpmn_if_present(assets_path)

        return WorkflowMetadata(
            id=workflow_id,
            name=metadata_dict.get("name", workflow_id.replace("_", " ").title()),
            description=metadata_dict.get("description", "No description"),
            icon=metadata_dict.get("icon", "🔄"),
            diagram_mermaid="",  # Mermaid deprecated; we use BPMN only
            input_schema=metadata_dict.get("input_schema", {}),
            category=metadata_dict.get("category", "Other"),
            estimated_duration=metadata_dict.get("estimated_duration", "Unknown"),
            workflow_number=workflow_number,  # Caller ensures uniqueness
            documentation_path=metadata_dict.get("documentation_path"),
            diagram_bpmn_xml=diagram_bpmn_xml,
            current_version_path=version_path,
            outputs=metadata_dict.get("outputs")
            if isinstance(metadata_dict.get("outputs"), list)
            else [],
            hide_from_catalog=bool(metadata_dict.get("hide_from_catalog", False)),
        )

    def _load_workflow_executor(self, workflow_id):
        """Try to import and instantiate workflow executor."""
        try:
            module_name = f"workflows.{workflow_id}"
            workflow_module = __import__(module_name, fromlist=[""])

            class_name = workflow_id.title().replace("_", "") + "Workflow"
            if hasattr(workflow_module, class_name):
                workflow_class = getattr(workflow_module, class_name)
                logger.debug(f"Loaded executor for workflow: {workflow_id}")
                return workflow_class()
            logger.debug(f"No executor class found for workflow: {workflow_id}")
            return None

        except ImportError as e:
            logger.debug(f"Could not import workflow {workflow_id}: {e}")
            return None
        except Exception as e:
            logger.warning(f"Error loading executor for {workflow_id}: {e}")
            return None

    def _auto_discover_workflows(self):
        """
        Auto-discover workflows by scanning the workflows/ directory.
        Each subdirectory with a metadata.yaml file is treated as a workflow.
        """
        workflows_dir = REPO_ROOT / "workflows"

        if not workflows_dir.exists():
            logger.warning(f"Workflows directory not found: {workflows_dir}")
            return

        next_number = 1
        used_numbers = set()

        for workflow_path in sorted(workflows_dir.iterdir()):
            if self._should_skip_path(workflow_path):
                continue

            metadata_file = workflow_path / "metadata.yaml"
            if not metadata_file.exists():
                logger.debug(f"Skipping {workflow_path.name}: No metadata.yaml found")
                continue

            try:
                with open(metadata_file) as f:
                    metadata_dict = yaml.safe_load(f)

                # Assign a unique workflow_number: prefer value from metadata, else next_number
                requested = metadata_dict.get("workflow_number")
                if requested is not None:
                    requested = int(requested)
                if requested is not None and requested not in used_numbers:
                    workflow_number = requested
                else:
                    while next_number in used_numbers:
                        next_number += 1
                    workflow_number = next_number
                used_numbers.add(workflow_number)

                metadata = self._load_workflow_metadata(
                    workflow_path, metadata_dict, workflow_number
                )
                executor = self._load_workflow_executor(metadata.id)

                self.workflows[metadata.id] = {"metadata": metadata, "executor": executor}

                logger.info(f"✓ Discovered workflow: {metadata.name} ({metadata.id})")
                next_number = max(next_number, workflow_number + 1)

            except Exception as e:
                logger.error(
                    "Failed to load workflow from %s: %s", workflow_path.name, e, exc_info=True
                )

    def register(self, metadata: WorkflowMetadata, executor: Any):
        """
        Manually register a workflow with metadata and executor.

        Args:
            metadata: WorkflowMetadata with UI display information
            executor: Workflow instance or callable that can be executed
        """
        self.workflows[metadata.id] = {"metadata": metadata, "executor": executor}
        logger.info(f"✓ Registered workflow: {metadata.name} ({metadata.id})")

    def get_all(self, include_internal: bool = False):
        """
        Get workflow metadata for UI and scheduling.
        By default excludes workflows with hide_from_catalog (e.g. test-only integrations).
        """
        metas = [w["metadata"] for w in self.workflows.values()]
        if include_internal:
            return metas
        return [m for m in metas if not getattr(m, "hide_from_catalog", False)]

    def get(self, workflow_id: str):
        """Get workflow by ID"""
        return self.workflows.get(workflow_id)

    def list_by_category(self, category: str):
        """Get workflows filtered by category"""
        return [
            w["metadata"] for w in self.workflows.values() if w["metadata"].category == category
        ]

    def reload(self):
        """Reload workflows from filesystem and sync canonical IDs to the Workflow model."""
        self.workflows = {}
        self._auto_discover_workflows()
        self._sync_workflow_model()

    def _sync_workflow_model(self):
        """Upsert discovered workflows into the Workflow model (enforces unique workflow_id and workflow_number).
        Must not be called from module import; use connection_created (apps.py) or reload() instead."""
        try:
            import asyncio

            try:
                asyncio.get_running_loop()
            except RuntimeError:
                logger.debug("Async context detected, skipping Workflow model sync")
            else:
                # Called from async context (e.g. ASGI); skip DB sync to avoid "cannot call from async context"
                logger.debug(
                    "Skipping Workflow model sync in async context (will sync on next sync reload)"
                )
                return
            from django.apps import apps

            if not apps.is_installed("agent_app"):
                return
            from agent_app.models import Workflow

            seen_ids = set()
            for w in self.workflows.values():
                meta = w["metadata"]
                seen_ids.add(meta.id)
                Workflow.objects.update_or_create(
                    workflow_id=meta.id,
                    defaults={"workflow_number": meta.workflow_number, "name": meta.name},
                )
            # Remove rows for workflows no longer on the filesystem
            Workflow.objects.exclude(workflow_id__in=seen_ids).delete()
        except Exception as e:
            logger.warning(
                "Could not sync workflow registry to Workflow model: %s", e, exc_info=True
            )


# Global registry instance. Created on import; only does filesystem discovery here.
# DB sync (Workflow model) is triggered later via connection_created or reload().
workflow_registry = WorkflowRegistry()


def _should_skip_workflow_path(workflow_path):
    """Check if workflow path should be skipped during validation."""
    if not workflow_path.is_dir():
        return True
    if workflow_path.name.startswith("."):
        return True
    return workflow_path.name in ["__pycache__", "docs", "templates"]


def _validate_metadata_file(workflow_id, metadata_file, results):
    """Validate workflow metadata file exists and has required fields."""
    if not metadata_file.exists():
        results["errors"].append(f"Workflow '{workflow_id}': Missing metadata.yaml")
        results["valid"] = False
        return None

    try:
        with open(metadata_file) as f:
            metadata = yaml.safe_load(f)

        required_fields = ["id", "name", "description"]
        for field in required_fields:
            if field not in metadata:
                results["errors"].append(
                    f"Workflow '{workflow_id}': metadata.yaml missing '{field}'"
                )
                results["valid"] = False

        return metadata

    except yaml.YAMLError as e:
        results["errors"].append(f"Workflow '{workflow_id}': Invalid YAML in metadata.yaml: {e}")
        results["valid"] = False
        return None
    except Exception as e:
        results["errors"].append(f"Workflow '{workflow_id}': Error reading metadata.yaml: {e}")
        results["valid"] = False
        return None


def _resolve_assets_path(workflow_path: Path) -> Path:
    """Resolve the directory that contains workflow.bpmn. Same logic as registry: currentVersion first, then v1/v2, then root."""
    current_version_path = workflow_path / CURRENT_VERSION_FOLDER
    if current_version_path.is_dir():
        return current_version_path
    version_dirs = [
        p for p in workflow_path.iterdir() if p.is_dir() and VERSION_SUBFOLDER_PATTERN.match(p.name)
    ]
    if version_dirs:
        version_dirs.sort(key=lambda p: int(VERSION_SUBFOLDER_PATTERN.match(p.name).group(1)))
        return version_dirs[-1]
    return workflow_path


def _check_optional_files(workflow_id, workflow_path, results):
    """Check for optional but recommended workflow files."""
    workflow_file = workflow_path / "workflow.py"
    if not workflow_file.exists():
        results["warnings"].append(f"Workflow '{workflow_id}': Missing workflow.py implementation")

    init_file = workflow_path / "__init__.py"
    if not init_file.exists():
        results["warnings"].append(f"Workflow '{workflow_id}': Missing __init__.py")

    # We use BPMN only; warn when workflow.bpmn is missing.
    assets_path = _resolve_assets_path(workflow_path)
    has_bpmn = (assets_path / "workflow.bpmn").exists()
    if not has_bpmn:
        results["warnings"].append(
            f"Workflow '{workflow_id}': No BPMN diagram (add workflow.bpmn in currentVersion/)"
        )


def validate_workflow_integrity(fix_issues: bool = False) -> dict[str, Any]:
    """
    Validate workflow directory structure, metadata files, and executor availability.

    Ensures each workflow has a loadable executor (workflow module and *Workflow class).
    Executor import failures are treated as errors so broken workflows are not reported as valid.

    Args:
        fix_issues: If True, attempts to fix issues (not yet implemented)

    Returns:
        dict: Validation results with errors, warnings, and summary
    """
    results = {"valid": True, "errors": [], "warnings": [], "checked": 0, "fixed": 0}

    workflows_dir = REPO_ROOT / "workflows"

    if not workflows_dir.exists():
        results["errors"].append(f"Workflows directory not found: {workflows_dir}")
        results["valid"] = False
        return results

    for workflow_path in workflows_dir.iterdir():
        if _should_skip_workflow_path(workflow_path):
            continue

        results["checked"] += 1
        workflow_id = workflow_path.name
        metadata_file = workflow_path / "metadata.yaml"

        metadata = _validate_metadata_file(workflow_id, metadata_file, results)
        if metadata is None:
            continue

        _check_optional_files(workflow_id, workflow_path, results)

        # Require that the executor can be imported (registry sets executor=None on import failure)
        canonical_id = metadata.get("id", workflow_id)
        entry = workflow_registry.get(canonical_id)
        if entry is None:
            results["errors"].append(
                f"Workflow '{workflow_id}': Not in registry (discovery may have failed)"
            )
            results["valid"] = False
        elif entry.get("executor") is None:
            results["errors"].append(
                f"Workflow '{workflow_id}': Executor failed to load (check workflow module and {canonical_id.title().replace('_', '')}Workflow class)"
            )
            results["valid"] = False

    return results


# Export for easy access
__all__ = [
    "workflow_registry",
    "WorkflowMetadata",
    "WorkflowRegistry",
    "REPO_ROOT",
    "validate_workflow_integrity",
]
