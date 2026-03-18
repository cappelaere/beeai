"""
Notifications API: list, mark read, mark all read.
"""

import logging

from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from agent_app.constants import ANONYMOUS_USER_ID
from agent_app.models import Notification
from agent_app.notifications import ensure_due_soon_notifications_for_user

logger = logging.getLogger(__name__)


@require_GET
def notifications_list_api(request):
    """List notifications for the current user. Unread first, then by created_at desc."""
    user_id = request.session.get("user_id", ANONYMOUS_USER_ID)
    ensure_due_soon_notifications_for_user(user_id)
    limit = min(int(request.GET.get("limit", 50)), 100)
    notifications = (
        Notification.objects.filter(user_id=user_id)
        .order_by("-created_at")[:limit]
        .values(
            "id", "kind", "title", "message", "task_id", "workflow_run_id", "created_at", "read_at"
        )
    )
    items = []
    for n in notifications:
        items.append(
            {
                "id": n["id"],
                "kind": n["kind"],
                "title": n["title"],
                "message": n["message"],
                "task_id": n["task_id"],
                "workflow_run_id": n["workflow_run_id"],
                "created_at": n["created_at"].isoformat() if n["created_at"] else None,
                "read_at": n["read_at"].isoformat() if n["read_at"] else None,
            }
        )
    # Unread first, then newest first (by created_at desc within group)
    items.sort(key=lambda x: x["created_at"] or "", reverse=True)
    items.sort(key=lambda x: x["read_at"] is not None)
    unread_count = Notification.objects.filter(user_id=user_id, read_at__isnull=True).count()
    return JsonResponse({"notifications": items, "unread_count": unread_count})


@require_POST
@csrf_exempt
def notification_mark_read_api(request, notification_id):
    """Mark a single notification as read."""
    user_id = request.session.get("user_id", ANONYMOUS_USER_ID)
    updated = Notification.objects.filter(id=notification_id, user_id=user_id).update(
        read_at=timezone.now()
    )
    if not updated:
        return JsonResponse({"error": "Not found or forbidden"}, status=404)
    return JsonResponse({"success": True})


@require_POST
@csrf_exempt
def notification_mark_all_read_api(request):
    """Mark all notifications for the current user as read."""
    user_id = request.session.get("user_id", ANONYMOUS_USER_ID)
    count = Notification.objects.filter(user_id=user_id, read_at__isnull=True).update(
        read_at=timezone.now()
    )
    return JsonResponse({"success": True, "marked_count": count})
