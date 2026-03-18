"""
Workflow API Endpoints
API endpoints for workflow creation and management.
Refactored from monolithic views.py - complexity reduced.
"""

import json
import logging
import re
from pathlib import Path

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from agent_app.constants import ANONYMOUS_USER_ID
from agent_app.exceptions import ValidationError, WorkflowExistsError, WorkflowNotFoundError
from agent_app.http_utils import json_response_500

logger = logging.getLogger(__name__)


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


@require_http_methods(["POST"])
def generate_workflow_user_story(request, workflow_id):
    """Generate a draft USER_STORY.md for an existing workflow using the LLM (admin only)."""
    user_role = request.session.get("user_role", "user")
    if user_role != "admin":
        return JsonResponse({"success": False, "error": "Unauthorized"}, status=403)

    from agent_app.workflow_registry import workflow_registry

    workflow = workflow_registry.get(workflow_id)
    if not workflow:
        return JsonResponse(
            {"success": False, "error": f"Workflow '{workflow_id}' not found"}, status=404
        )

    metadata = workflow["metadata"]
    name = metadata.name
    description = metadata.description or ""
    category = metadata.category or "Other"
    prompt = description  # no original prompt for existing workflows; use description

    try:
        body = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        body = {}
    model_short_key = (body.get("model") or "").strip() or "claude-sonnet-4"

    from agent_app.services import workflow_service

    service_task_ids = workflow_service.get_service_task_ids_for_workflow(workflow_id)
    user_story_content = workflow_service.generate_user_story_content(
        model_short_key,
        name,
        workflow_id,
        category,
        description,
        prompt,
        service_task_ids,
    )

    workflow_dir = REPO_ROOT / "workflows" / workflow_id
    user_story_path = workflow_dir / "USER_STORY.md"
    user_story_path.write_text(user_story_content.strip() + "\n", encoding="utf-8")

    return JsonResponse({"success": True, "path": str(user_story_path), "workflow_id": workflow_id})


@require_http_methods(["POST"])
def workflow_create(request):
    """Create a new workflow with AI-generated implementation (admin only). Delegates to workflow_service."""
    if request.session.get("user_role", "user") != "admin":
        return JsonResponse({"success": False, "error": "Unauthorized"}, status=403)

    workflow_id = ""
    try:
        data = json.loads(request.body)
        workflow_id = (data.get("workflow_id") or "").strip()
        from agent_app.services import workflow_service

        name, wf_id, icon, category, description, prompt, model_short_key = (
            workflow_service.validate_workflow_input(data)
        )
        workflow_id = workflow_service.create_workflow(
            name=name,
            workflow_id=wf_id,
            icon=icon,
            category=category,
            description=description,
            prompt=prompt,
            model_short_key=model_short_key,
        )
        return JsonResponse(
            {
                "success": True,
                "workflow_id": workflow_id,
                "message": f'Workflow "{name}" created successfully',
            }
        )
    except (ValidationError, WorkflowExistsError) as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)
    except Exception:
        return json_response_500(
            "Error creating workflow", workflow_id=workflow_id or "(validation failed)"
        )


@require_http_methods(["POST"])
def workflow_favorite_api(request, workflow_id):
    """Toggle workflow favorite status for the current user session."""
    from agent_app.models import UserPreference
    from agent_app.workflow_registry import workflow_registry

    try:
        # Verify workflow exists
        workflow = workflow_registry.get(workflow_id)
        if not workflow:
            return JsonResponse({"success": False, "error": "Workflow not found"}, status=404)

        # Get or create user preference
        if not request.session.session_key:
            request.session.create()

        session_key = request.session.session_key
        user_id = request.session.get("user_id", ANONYMOUS_USER_ID)

        user_pref, created = UserPreference.objects.get_or_create(
            session_key=session_key, user_id=user_id
        )

        # Parse current favorites
        try:
            favorites = json.loads(user_pref.favorite_workflows or "[]")
        except (json.JSONDecodeError, TypeError):
            favorites = []

        # Toggle favorite
        is_favorite = False
        if workflow_id in favorites:
            favorites.remove(workflow_id)
            is_favorite = False
        else:
            favorites.append(workflow_id)
            is_favorite = True

        # Save updated favorites
        user_pref.favorite_workflows = json.dumps(favorites)
        user_pref.save()

        return JsonResponse({"success": True, "is_favorite": is_favorite})

    except Exception:
        return json_response_500("Error toggling workflow favorite", workflow_id=workflow_id)


@require_http_methods(["POST"])
def workflow_save(request, workflow_id):
    """Save workflow changes and create new version. Delegates to workflow_service."""
    if request.session.get("user_role") != "admin":
        return JsonResponse({"success": False, "error": "Admin access required"}, status=403)

    try:
        from agent_app.services import workflow_service

        data = json.loads(request.body)
        metadata_updates = data.get("metadata", {})
        file_updates = data.get("files", {})
        bindings_json = data.get("bindings_json")
        version_info = data.get("version", {})
        user_id = request.session.get("user_id", ANONYMOUS_USER_ID)

        version, validation = workflow_service.save_workflow(
            workflow_id=workflow_id,
            metadata_updates=metadata_updates,
            file_updates=file_updates,
            bindings_json=bindings_json,
            version_info=version_info,
            user_id=user_id,
        )
        return JsonResponse(
            {
                "success": True,
                "version_number": version.version_number,
                "message": f"Version {version.version_number} created successfully",
                "validation": validation,
            }
        )
    except WorkflowNotFoundError:
        return JsonResponse({"success": False, "error": "Workflow not found"}, status=404)
    except ValueError as e:
        return JsonResponse(
            {"success": False, "error": str(e), "validation_error": True},
            status=400,
        )
    except Exception:
        return json_response_500("Error saving workflow", workflow_id=workflow_id)


@require_http_methods(["POST"])
def workflow_restore_version(request, workflow_id, version_number):
    """Restore workflow to specific version. Delegates to workflow_service."""
    if request.session.get("user_role") != "admin":
        return JsonResponse({"success": False, "error": "Admin access required"}, status=403)

    try:
        from agent_app.services import workflow_service

        version_number = int(version_number)
        user_id = request.session.get("user_id", ANONYMOUS_USER_ID)
        new_version = workflow_service.restore_version(workflow_id, version_number, user_id)
        return JsonResponse(
            {
                "success": True,
                "new_version_number": new_version.version_number,
                "message": f"Restored to version {version_number}. New version {new_version.version_number} created.",
            }
        )
    except ValueError as e:
        return JsonResponse({"success": False, "error": str(e)}, status=404)
    except Exception:
        return json_response_500(
            "Error restoring version", workflow_id=workflow_id, version_number=version_number
        )


@require_http_methods(["POST"])
def workflow_tag_version(request, workflow_id, version_number):
    """Add or update tag for version. Delegates to workflow_service."""
    if request.session.get("user_role") != "admin":
        return JsonResponse({"success": False, "error": "Admin access required"}, status=403)

    try:
        from agent_app.services import workflow_service

        data = json.loads(request.body)
        tag = (data.get("tag") or "").strip()
        if not tag:
            return JsonResponse({"success": False, "error": "Tag is required"}, status=400)
        version_number = int(version_number)
        workflow_service.tag_version(workflow_id, version_number, tag)
        return JsonResponse(
            {"success": True, "message": f"Version {version_number} tagged as '{tag}'"}
        )
    except ValueError as e:
        return JsonResponse({"success": False, "error": str(e)}, status=404)
    except Exception:
        return json_response_500(
            "Error tagging version", workflow_id=workflow_id, version_number=version_number
        )


@require_http_methods(["GET"])
def workflow_version_files(request, workflow_id, version_number):
    """Get files for specific version. Delegates to workflow_service."""
    if request.session.get("user_role") != "admin":
        return JsonResponse({"success": False, "error": "Admin access required"}, status=403)

    try:
        from agent_app.services import workflow_service

        version_number = int(version_number)
        files = workflow_service.get_version_files(workflow_id, version_number)
        return JsonResponse({"success": True, "files": files})
    except ValueError as e:
        return JsonResponse({"success": False, "error": str(e)}, status=404)
    except Exception:
        return json_response_500(
            "Error getting version files", workflow_id=workflow_id, version_number=version_number
        )
