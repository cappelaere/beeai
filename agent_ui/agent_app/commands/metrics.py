"""
/metrics command handler - Display dashboard metrics
"""


def _format_doc_size(total_doc_size):
    """Format document size in human-readable format."""
    if total_doc_size > 1024 * 1024:
        return f"{total_doc_size / (1024 * 1024):.2f}MB"
    if total_doc_size > 1024:
        return f"{total_doc_size / 1024:.2f}KB"
    return f"{total_doc_size}B"


def _get_database_size():
    """Get database size in human-readable format."""
    import logging
    from pathlib import Path

    from django.db import connection

    logger = logging.getLogger(__name__)
    db_size = "N/A"
    try:
        db_engine = connection.settings_dict["ENGINE"]
        if "sqlite" in db_engine.lower():
            db_path = connection.settings_dict.get("NAME")
            db_file = Path(db_path) if db_path and db_path != ":memory:" else None
            if db_file and db_file.exists():
                size_bytes = db_file.stat().st_size
                if size_bytes < 1024:
                    db_size = f"{size_bytes} B"
                elif size_bytes < 1024 * 1024:
                    db_size = f"{size_bytes / 1024:.1f} KB"
                elif size_bytes < 1024 * 1024 * 1024:
                    db_size = f"{size_bytes / (1024 * 1024):.1f} MB"
                else:
                    db_size = f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
        elif "postgres" in db_engine.lower():
            with connection.cursor() as cursor:
                db_name = connection.settings_dict["NAME"]
                cursor.execute("SELECT pg_size_pretty(pg_database_size(%s));", [db_name])
                result = cursor.fetchone()
                db_size = result[0] if result else "N/A"
    except Exception as e:
        logger.warning(f"Could not determine database size: {e}")
        db_size = "N/A"
    return db_size


def _format_service_status(service):
    """Format service status with appropriate emoji and details."""
    if service["status"] == "healthy":
        return f"✓ {service.get('response_time_ms', 'N/A')}ms"
    if service["status"] == "unhealthy":
        return f"✗ {service.get('error', 'Error')}"
    if service["status"] == "disabled":
        return "○ Disabled"
    return "? Unknown"


def handle_metrics(request, args, session_key):
    """
    Display dashboard metrics for the current user.
    Matches all statistics shown on the dashboard view.

    Args:
        request: Django HTTP request
        args: Command arguments (unused)
        session_key: User session key

    Returns:
        Dictionary with content and metadata
    """
    from django.db.models import Avg, Max, Min, Sum

    from agent_app.constants import ANONYMOUS_USER_ID
    from agent_app.health_checks import check_all_services, get_overall_status
    from agent_app.models import (
        AssistantCard,
        ChatMessage,
        ChatSession,
        Document,
        HumanTask,
        WorkflowRun,
    )

    # Get user_id from session
    user_id = request.session.get("user_id", ANONYMOUS_USER_ID)

    # Session statistics
    total_sessions = ChatSession.objects.filter(user_id=user_id).count()
    total_messages = ChatMessage.objects.filter(session__user_id=user_id).count()
    user_messages = ChatMessage.objects.filter(
        session__user_id=user_id, role=ChatMessage.ROLE_USER
    ).count()
    assistant_messages = ChatMessage.objects.filter(
        session__user_id=user_id, role=ChatMessage.ROLE_ASSISTANT
    ).count()

    # Performance statistics (for assistant messages only)
    perf_stats = ChatMessage.objects.filter(
        session__user_id=user_id, role=ChatMessage.ROLE_ASSISTANT
    ).aggregate(
        avg_ms=Avg("elapsed_ms"),
        min_ms=Min("elapsed_ms"),
        max_ms=Max("elapsed_ms"),
        total_ms=Sum("elapsed_ms"),
        total_tokens=Sum("tokens_used"),
    )

    # Feedback statistics
    positive_feedback = ChatMessage.objects.filter(
        session__user_id=user_id,
        role=ChatMessage.ROLE_ASSISTANT,
        feedback=ChatMessage.FEEDBACK_POSITIVE,
    ).count()

    negative_feedback = ChatMessage.objects.filter(
        session__user_id=user_id,
        role=ChatMessage.ROLE_ASSISTANT,
        feedback=ChatMessage.FEEDBACK_NEGATIVE,
    ).count()

    # Workflow statistics
    total_workflow_runs = WorkflowRun.objects.filter(user_id=user_id).count()
    completed_workflows = WorkflowRun.objects.filter(
        user_id=user_id, status=WorkflowRun.STATUS_COMPLETED
    ).count()
    failed_workflows = WorkflowRun.objects.filter(
        user_id=user_id, status=WorkflowRun.STATUS_FAILED
    ).count()
    running_workflows = WorkflowRun.objects.filter(
        user_id=user_id, status=WorkflowRun.STATUS_RUNNING
    ).count()
    waiting_workflows = WorkflowRun.objects.filter(
        user_id=user_id, status=WorkflowRun.STATUS_WAITING_FOR_TASK
    ).count()

    # Task statistics
    total_tasks = HumanTask.objects.filter(workflow_run__user_id=user_id).count()
    open_tasks = HumanTask.objects.filter(
        workflow_run__user_id=user_id, status=HumanTask.STATUS_OPEN
    ).count()
    claimed_tasks = HumanTask.objects.filter(
        workflow_run__user_id=user_id, status=HumanTask.STATUS_IN_PROGRESS
    ).count()
    completed_tasks = HumanTask.objects.filter(
        workflow_run__user_id=user_id, status=HumanTask.STATUS_COMPLETED
    ).count()

    total_feedback = positive_feedback + negative_feedback
    satisfaction_rate = 0
    if total_feedback > 0:
        satisfaction_rate = round((positive_feedback / total_feedback) * 100, 1)

    # Response times in seconds
    avg_response_time = round((perf_stats["avg_ms"] or 0) / 1000, 2)
    min_response_time = round((perf_stats["min_ms"] or 0) / 1000, 2)
    max_response_time = round((perf_stats["max_ms"] or 0) / 1000, 2)
    total_elapsed_time = round((perf_stats["total_ms"] or 0) / 1000, 2)
    total_tokens = perf_stats["total_tokens"] or 0

    # Card statistics
    total_cards = AssistantCard.objects.count()
    favorite_cards = AssistantCard.objects.filter(is_favorite=True).count()

    # Document statistics
    total_documents = Document.objects.count()
    total_doc_size = Document.objects.aggregate(total_size=Sum("file_size"))["total_size"] or 0
    doc_size_str = _format_doc_size(total_doc_size)

    # Unrated responses
    unrated_responses = assistant_messages - total_feedback

    # Database size
    db_size = _get_database_size()

    # Service health checks
    services = check_all_services()
    overall_status = get_overall_status(services)

    lines = [
        "📊 Dashboard Metrics",
        "",
        "═══ Service Health ═══",
        f"Overall Status: {'✓ All Systems Operational' if overall_status == 'healthy' else '⚠ Partially Degraded' if overall_status == 'degraded' else '✗ System Issues'}",
        f"BidHom API: {_format_service_status(services['api'])}",
        f"Piper TTS: {_format_service_status(services['piper'])}",
        f"Redis Cache: {_format_service_status(services['redis'])}",
        f"Database: {_format_service_status(services['postgres'])}",
        "",
        "═══ Key Metrics ═══",
        f"Sessions: {total_sessions}",
        f"Total Queries (User): {user_messages}",
        f"Total Tokens: {total_tokens:,}",
        f"Documents Uploaded: {total_documents} ({doc_size_str})",
        "",
        "═══ Workflow Metrics ═══",
        f"Total Workflow Runs: {total_workflow_runs}",
        f"Completed: {completed_workflows}",
        f"Failed: {failed_workflows}",
        f"Running: {running_workflows}",
        f"Waiting for Tasks: {waiting_workflows}",
        f"Total Tasks: {total_tasks}",
        f"Open Tasks: {open_tasks}",
        f"Claimed Tasks: {claimed_tasks}",
        f"Completed Tasks: {completed_tasks}",
        "",
        "═══ Performance ═══",
        f"Total Messages: {total_messages}",
        f"User Messages: {user_messages}",
        f"Assistant Responses: {assistant_messages}",
        f"Average Response Time: {avg_response_time}s",
        f"Fastest Response: {min_response_time}s",
        f"Slowest Response: {max_response_time}s",
        f"Total Elapsed Time: {total_elapsed_time}s",
        "",
        "═══ User Satisfaction ═══",
        f"Satisfaction Rate: {satisfaction_rate}%",
        f"Positive Feedback: 👍 {positive_feedback}",
        f"Negative Feedback: 👎 {negative_feedback}",
        f"Total Rated: {total_feedback}",
        f"Unrated Responses: {unrated_responses}",
        "",
        "═══ System Info ═══",
        f"Total Cards: {total_cards}",
        f"Favorite Cards: {favorite_cards}",
        f"Total Documents: {total_documents}",
        f"Document Storage: {doc_size_str}",
        f"Database Size: {db_size}",
    ]

    return {
        "content": "\n".join(lines),
        "metadata": {
            "command": "metrics",
            "sessions": total_sessions,
            "messages": total_messages,
            "satisfaction": satisfaction_rate,
            "cards": total_cards,
            "documents": total_documents,
            "overall_status": overall_status,
            "services": services,
            "workflows": {
                "total_runs": total_workflow_runs,
                "completed": completed_workflows,
                "failed": failed_workflows,
                "running": running_workflows,
                "waiting": waiting_workflows,
                "total_tasks": total_tasks,
                "open_tasks": open_tasks,
                "claimed_tasks": claimed_tasks,
                "completed_tasks": completed_tasks,
            },
        },
    }
