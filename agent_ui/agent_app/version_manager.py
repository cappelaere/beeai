"""
Workflow Version Control Manager
Handles versioning of workflow definitions using folder-based snapshots.
"""

import hashlib
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path

from django.db import transaction

from agent_app.models import WorkflowVersion

logger = logging.getLogger(__name__)


class VersionManager:
    """Manage workflow version control operations"""

    def __init__(self):
        # Base workflow directory
        self.workflows_base = Path(__file__).parent.parent.parent / "workflows"

    def _get_workflow_path(self, workflow_id):
        """Get path to workflow directory"""
        return self.workflows_base / workflow_id

    def _get_versions_path(self, workflow_id):
        """Get path to .versions directory for workflow"""
        return self._get_workflow_path(workflow_id) / ".versions"

    def _calculate_checksum(self, file_path):
        """Calculate SHA256 checksum of file"""
        if not file_path.exists():
            return ""

        sha256 = hashlib.sha256()
        with file_path.open("rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _resolve_assets_path(self, workflow_path):
        """Resolve directory for BPMN files (currentVersion, v1, v2, etc., or workflow root)."""
        import re

        # Prefer currentVersion folder
        current = workflow_path / "currentVersion"
        if current.is_dir():
            return current
        # Else v1, v2, ... (highest number)
        pat = re.compile(r"^v(\d+)$")
        version_dirs = [p for p in workflow_path.iterdir() if p.is_dir() and pat.match(p.name)]
        if version_dirs:
            version_dirs.sort(key=lambda p: int(pat.match(p.name).group(1)))
            return version_dirs[-1]
        return workflow_path

    def _copy_workflow_files(self, workflow_path, dest_dir, assets_path=None):
        """Copy workflow files from workflow (root + assets path) to destination."""
        if assets_path is None:
            assets_path = self._resolve_assets_path(workflow_path)
        root_files = ["metadata.yaml", "workflow.py", "README.md"]
        assets_files = ["workflow.bpmn", "bpmn-bindings.yaml"]
        dest_dir.mkdir(parents=True, exist_ok=True)
        for filename in root_files:
            source_file = workflow_path / filename
            if source_file.exists():
                shutil.copy2(source_file, dest_dir / filename)
                logger.debug(f"Copied {filename} to {dest_dir}")
        for filename in assets_files:
            source_file = assets_path / filename
            if source_file.exists():
                shutil.copy2(source_file, dest_dir / filename)
                logger.debug(f"Copied {filename} to {dest_dir}")

    def _validate_version_integrity(self, version_path):
        """Validate that version directory has required files"""
        required_files = ["metadata.yaml", "workflow.py"]
        for filename in required_files:
            if not (version_path / filename).exists():
                raise ValueError(f"Missing required file: {filename} in {version_path}")

    @transaction.atomic
    def create_version(self, workflow_id, user_id, comment="", tag=None):
        """
        Create new version snapshot of workflow

        Args:
            workflow_id: Unique workflow identifier
            user_id: User creating the version
            comment: Version description/changelog entry
            tag: Optional version tag (e.g., 'v1.0', 'stable')

        Returns:
            WorkflowVersion object
        """
        workflow_path = self._get_workflow_path(workflow_id)
        if not workflow_path.exists():
            raise ValueError(f"Workflow {workflow_id} does not exist")

        # Get next version number
        last_version = (
            WorkflowVersion.objects.filter(workflow_id=workflow_id)
            .order_by("-version_number")
            .first()
        )
        version_number = (last_version.version_number + 1) if last_version else 1

        # Create timestamp-based folder name
        timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
        version_folder_name = f"v{version_number}_{timestamp}"

        # Create version directory
        versions_path = self._get_versions_path(workflow_id)
        versions_path.mkdir(parents=True, exist_ok=True)

        # Create .gitkeep if it doesn't exist
        gitkeep_file = versions_path / ".gitkeep"
        if not gitkeep_file.exists():
            gitkeep_file.touch()

        version_path = versions_path / version_folder_name
        version_path.mkdir(parents=True, exist_ok=True)

        # Copy workflow files to version folder
        self._copy_workflow_files(workflow_path, version_path)

        # Validate version integrity
        self._validate_version_integrity(version_path)

        # Calculate checksums
        metadata_checksum = self._calculate_checksum(version_path / "metadata.yaml")
        workflow_checksum = self._calculate_checksum(version_path / "workflow.py")

        # Mark all other versions as not current
        WorkflowVersion.objects.filter(workflow_id=workflow_id, is_current=True).update(
            is_current=False
        )

        # Create version record
        version = WorkflowVersion.objects.create(
            workflow_id=workflow_id,
            version_number=version_number,
            version_tag=tag,
            created_by_user_id=user_id,
            comment=comment,
            is_current=True,
            version_path=f".versions/{version_folder_name}",
            metadata_checksum=metadata_checksum,
            workflow_checksum=workflow_checksum,
        )

        logger.info(
            f"Created version {version_number} for workflow {workflow_id} by user {user_id}"
        )

        return version

    @transaction.atomic
    def restore_version(self, workflow_id, version_number, user_id):
        """
        Restore workflow to specific version

        Args:
            workflow_id: Unique workflow identifier
            version_number: Version number to restore
            user_id: User performing the restoration

        Returns:
            New WorkflowVersion object (restoration creates a new version)
        """
        # Get the version to restore
        version = WorkflowVersion.objects.filter(
            workflow_id=workflow_id, version_number=version_number
        ).first()

        if not version:
            raise ValueError(f"Version {version_number} not found for workflow {workflow_id}")

        workflow_path = self._get_workflow_path(workflow_id)
        version_path = workflow_path / version.version_path

        if not version_path.exists():
            raise ValueError(f"Version files not found at {version_path}")

        # Validate version integrity
        self._validate_version_integrity(version_path)

        # Copy files from version snapshot back to workflow directory
        # Root files -> workflow root; BPMN files -> assets path (currentVersion/v1) when present
        assets_path = self._resolve_assets_path(workflow_path)
        root_files = ["metadata.yaml", "workflow.py", "README.md"]
        assets_files = ["workflow.bpmn", "bpmn-bindings.yaml"]
        for filename in root_files:
            src = version_path / filename
            if src.exists():
                shutil.copy2(src, workflow_path / filename)
        for filename in assets_files:
            src = version_path / filename
            if src.exists():
                dest = assets_path if assets_path != workflow_path else workflow_path
                dest.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest / filename)

        # Create new version record for the restoration
        comment = f"Restored from version {version_number}"
        if version.version_tag:
            comment += f" ({version.version_tag})"

        new_version = self.create_version(workflow_id=workflow_id, user_id=user_id, comment=comment)

        logger.info(
            f"Restored workflow {workflow_id} to version {version_number} by user {user_id}"
        )

        # Reload workflow registry to pick up changes
        try:
            from agent_app.workflow_registry import workflow_registry

            workflow_registry.reload()
            logger.info("Reloaded workflow registry after restoration")
        except Exception as e:
            logger.error(f"Failed to reload workflow registry: {e}")

        return new_version

    def get_version_history(self, workflow_id):
        """
        Get all versions for a workflow

        Args:
            workflow_id: Unique workflow identifier

        Returns:
            QuerySet of WorkflowVersion objects
        """
        return WorkflowVersion.objects.filter(workflow_id=workflow_id).order_by("-version_number")

    def get_version(self, workflow_id, version_number):
        """
        Get specific version

        Args:
            workflow_id: Unique workflow identifier
            version_number: Version number

        Returns:
            WorkflowVersion object or None
        """
        return WorkflowVersion.objects.filter(
            workflow_id=workflow_id, version_number=version_number
        ).first()

    def compare_versions(self, workflow_id, version1_number, version2_number):
        """
        Generate diff between two versions

        Args:
            workflow_id: Unique workflow identifier
            version1_number: First version number
            version2_number: Second version number

        Returns:
            List of dicts with filename and diff content
        """
        import difflib

        version1 = self.get_version(workflow_id, version1_number)
        version2 = self.get_version(workflow_id, version2_number)

        if not version1 or not version2:
            raise ValueError("One or both versions not found")

        workflow_path = self._get_workflow_path(workflow_id)
        version1_path = workflow_path / version1.version_path
        version2_path = workflow_path / version2.version_path

        files_to_compare = [
            "metadata.yaml",
            "workflow.py",
            "README.md",
            "workflow.bpmn",
            "bpmn-bindings.yaml",
        ]
        diffs = []

        for filename in files_to_compare:
            file1 = version1_path / filename
            file2 = version2_path / filename

            # Skip if neither file exists
            if not file1.exists() and not file2.exists():
                continue

            # Read file contents
            lines1 = []
            if file1.exists():
                with file1.open(encoding="utf-8") as f:
                    lines1 = f.readlines()

            lines2 = []
            if file2.exists():
                with file2.open(encoding="utf-8") as f:
                    lines2 = f.readlines()

            # Generate unified diff
            diff_lines = difflib.unified_diff(
                lines1,
                lines2,
                fromfile=f"{filename} (v{version1_number})",
                tofile=f"{filename} (v{version2_number})",
                lineterm="",
            )

            diff_content = "\n".join(diff_lines)

            # Only include files with differences
            if diff_content:
                diffs.append({"filename": filename, "unified_diff": diff_content})

        return diffs

    @transaction.atomic
    def tag_version(self, workflow_id, version_number, tag):
        """
        Add or update tag for version

        Args:
            workflow_id: Unique workflow identifier
            version_number: Version number to tag
            tag: Tag string (e.g., 'v1.0', 'stable')

        Returns:
            Updated WorkflowVersion object
        """
        version = self.get_version(workflow_id, version_number)
        if not version:
            raise ValueError(f"Version {version_number} not found for workflow {workflow_id}")

        version.version_tag = tag
        version.save()

        logger.info(f"Tagged version {version_number} of {workflow_id} as '{tag}'")

        return version

    def delete_version(self, workflow_id, version_number):
        """
        Delete specific version (cannot delete current version)

        Args:
            workflow_id: Unique workflow identifier
            version_number: Version number to delete

        Returns:
            Boolean success
        """
        version = self.get_version(workflow_id, version_number)
        if not version:
            raise ValueError(f"Version {version_number} not found for workflow {workflow_id}")

        if version.is_current:
            raise ValueError("Cannot delete current version")

        # Delete version files
        workflow_path = self._get_workflow_path(workflow_id)
        version_path = workflow_path / version.version_path

        if version_path.exists():
            shutil.rmtree(version_path)
            logger.info(f"Deleted version files at {version_path}")

        # Delete database record
        version.delete()

        logger.info(f"Deleted version {version_number} of workflow {workflow_id}")

        return True

    def cleanup_old_versions(self, workflow_id, keep_count=10):
        """
        Delete old versions, keeping only the most recent N versions

        Args:
            workflow_id: Unique workflow identifier
            keep_count: Number of recent versions to keep (default: 10)

        Returns:
            Number of versions deleted
        """
        versions = self.get_version_history(workflow_id)

        # Get versions to delete (excluding current version)
        versions_to_delete = []
        kept_count = 0

        for version in versions:
            if version.is_current:
                continue

            if kept_count < keep_count:
                kept_count += 1
            else:
                versions_to_delete.append(version)

        # Delete old versions
        deleted_count = 0
        for version in versions_to_delete:
            try:
                self.delete_version(workflow_id, version.version_number)
                deleted_count += 1
            except Exception as e:
                logger.error(f"Failed to delete version {version.version_number}: {e}")

        logger.info(
            f"Cleaned up {deleted_count} old versions for workflow {workflow_id}, kept {kept_count}"
        )

        return deleted_count

    def get_version_files(self, workflow_id, version_number):
        """
        Get file contents for specific version

        Args:
            workflow_id: Unique workflow identifier
            version_number: Version number

        Returns:
            Dict mapping filename to content
        """
        version = self.get_version(workflow_id, version_number)
        if not version:
            raise ValueError(f"Version {version_number} not found for workflow {workflow_id}")

        workflow_path = self._get_workflow_path(workflow_id)
        version_path = workflow_path / version.version_path

        files = {}
        files_to_read = [
            "metadata.yaml",
            "workflow.py",
            "README.md",
            "workflow.bpmn",
            "bpmn-bindings.yaml",
        ]

        for filename in files_to_read:
            file_path = version_path / filename
            if file_path.exists():
                with file_path.open(encoding="utf-8") as f:
                    files[filename] = f.read()

        return files

    def generate_changelog(self, workflow_id):
        """
        Generate CHANGELOG.md from version history

        Args:
            workflow_id: Unique workflow identifier

        Returns:
            String containing changelog content in Markdown format
        """
        versions = self.get_version_history(workflow_id)

        if not versions.exists():
            return "# Changelog\n\nNo versions yet.\n"

        changelog = "# Changelog\n\n"
        changelog += f"All notable changes to the **{workflow_id}** workflow.\n\n"

        for version in versions:
            # Version header
            changelog += f"## Version {version.version_number}"
            if version.version_tag:
                changelog += f" - {version.version_tag}"
            if version.is_current:
                changelog += " [CURRENT]"
            changelog += "\n\n"

            # Date and author
            changelog += f"**Date:** {version.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
            changelog += f"**Author:** User {version.created_by_user_id}\n\n"

            # Comment/description
            if version.comment:
                changelog += f"{version.comment}\n\n"
            else:
                changelog += "*No description provided*\n\n"

            changelog += "---\n\n"

        return changelog

    def save_changelog(self, workflow_id):
        """
        Generate and save CHANGELOG.md to workflow directory

        Args:
            workflow_id: Unique workflow identifier

        Returns:
            Path to saved changelog file
        """
        changelog_content = self.generate_changelog(workflow_id)

        workflow_path = self._get_workflow_path(workflow_id)
        changelog_path = workflow_path / "CHANGELOG.md"

        with changelog_path.open("w", encoding="utf-8") as f:
            f.write(changelog_content)

        logger.info(f"Saved changelog for workflow {workflow_id} to {changelog_path}")

        return changelog_path


# Global instance
version_manager = VersionManager()
