"""
Admin and System Views
Dashboard, settings, logs, prometheus, diagrams, and documentation.
Refactored from monolithic views.py - complexity reduced.
"""

import logging
import os
import re
from datetime import timedelta
from pathlib import Path

import markdown
from django.db import models
from django.db.models import Avg, Count, Max, Min, Q, Sum
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound, JsonResponse
from django.shortcuts import render
from django.utils import timezone

from agent_app.constants import ANONYMOUS_USER_ID
from agent_app.models import (
    AssistantCard,
    ChatMessage,
    ChatSession,
    Document,
    HumanTask,
    WorkflowRun,
)

logger = logging.getLogger(__name__)


# ===== Dashboard View with Helper Functions =====


def _calculate_message_stats(user_id):
    """Calculate message-related statistics."""
    total_sessions = ChatSession.objects.filter(user_id=user_id).count()
    total_messages = ChatMessage.objects.filter(session__user_id=user_id).count()
    user_messages = ChatMessage.objects.filter(
        session__user_id=user_id, role=ChatMessage.ROLE_USER
    ).count()
    assistant_messages = ChatMessage.objects.filter(
        session__user_id=user_id, role=ChatMessage.ROLE_ASSISTANT
    ).count()

    # Error detection
    error_messages = (
        ChatMessage.objects.filter(session__user_id=user_id, role=ChatMessage.ROLE_ASSISTANT)
        .filter(
            Q(content__icontains="Error (")
            | Q(content__icontains="**Error")
            | Q(content__icontains="ToolError")
            | Q(content__icontains="API error")
        )
        .count()
    )

    error_rate = 0
    if assistant_messages > 0:
        error_rate = round((error_messages / assistant_messages) * 100, 1)

    return {
        "total_sessions": total_sessions,
        "total_messages": total_messages,
        "user_messages": user_messages,
        "assistant_messages": assistant_messages,
        "error_messages": error_messages,
        "error_rate": error_rate,
    }


def _calculate_feedback_stats(user_id):
    """Calculate feedback statistics."""
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

    total_feedback = positive_feedback + negative_feedback
    satisfaction_rate = 0
    if total_feedback > 0:
        satisfaction_rate = round((positive_feedback / total_feedback) * 100, 1)

    return {
        "positive_feedback": positive_feedback,
        "negative_feedback": negative_feedback,
        "total_feedback": total_feedback,
        "satisfaction_rate": satisfaction_rate,
    }


def _calculate_performance_stats(user_id):
    """Calculate performance statistics."""
    perf_stats = ChatMessage.objects.filter(
        session__user_id=user_id, role=ChatMessage.ROLE_ASSISTANT
    ).aggregate(
        avg_ms=Avg("elapsed_ms"),
        min_ms=Min("elapsed_ms"),
        max_ms=Max("elapsed_ms"),
        total_ms=Sum("elapsed_ms"),
        total_tokens=Sum("tokens_used"),
    )

    return {
        "avg_response_time": round((perf_stats["avg_ms"] or 0) / 1000, 2),
        "min_response_time": round((perf_stats["min_ms"] or 0) / 1000, 2),
        "max_response_time": round((perf_stats["max_ms"] or 0) / 1000, 2),
        "total_elapsed_time": round((perf_stats["total_ms"] or 0) / 1000, 2),
        "total_tokens": perf_stats["total_tokens"] or 0,
    }


def _get_system_stats():
    """Get system-level statistics."""
    total_documents = Document.objects.count()
    total_doc_size = Document.objects.aggregate(total_size=Sum("file_size"))["total_size"] or 0

    def format_bytes(size_bytes):
        if size_bytes < 1024:
            return f"{size_bytes} B"
        if size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        if size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

    total_cards = AssistantCard.objects.count()
    favorite_cards = AssistantCard.objects.filter(is_favorite=True).count()

    # Get database size
    from django.db import connection

    db_size = "N/A"
    try:
        db_engine = connection.settings_dict["ENGINE"]
        if "sqlite" in db_engine.lower():
            db_path = connection.settings_dict.get("NAME")
            db_file = Path(db_path) if db_path and db_path != ":memory:" else None
            if db_file and db_file.exists():
                size_bytes = db_file.stat().st_size
                db_size = format_bytes(size_bytes)
        elif "postgres" in db_engine.lower():
            with connection.cursor() as cursor:
                db_name = connection.settings_dict["NAME"]
                cursor.execute("SELECT pg_size_pretty(pg_database_size(%s));", [db_name])
                result = cursor.fetchone()
                db_size = result[0] if result else "N/A"
    except Exception as e:
        logger.warning(f"Could not determine database size: {e}")

    return {
        "total_documents": total_documents,
        "total_doc_size": format_bytes(total_doc_size),
        "total_cards": total_cards,
        "favorite_cards": favorite_cards,
        "db_size": db_size,
    }


def _calculate_workflow_stats(user_id):
    """Calculate workflow statistics."""
    total_workflow_runs = WorkflowRun.objects.filter(user_id=user_id).count()
    pending_workflows = WorkflowRun.objects.filter(
        user_id=user_id, status=WorkflowRun.STATUS_PENDING
    ).count()
    running_workflows = WorkflowRun.objects.filter(
        user_id=user_id, status=WorkflowRun.STATUS_RUNNING
    ).count()
    completed_workflows = WorkflowRun.objects.filter(
        user_id=user_id, status=WorkflowRun.STATUS_COMPLETED
    ).count()
    failed_workflows = WorkflowRun.objects.filter(
        user_id=user_id, status=WorkflowRun.STATUS_FAILED
    ).count()
    waiting_workflows = WorkflowRun.objects.filter(
        user_id=user_id, status=WorkflowRun.STATUS_WAITING_FOR_TASK
    ).count()

    total_finished = completed_workflows + failed_workflows
    workflow_success_rate = 0
    if total_finished > 0:
        workflow_success_rate = round((completed_workflows / total_finished) * 100, 1)

    # Task statistics - Basic counts
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

    # Enhanced task statistics
    now = timezone.now()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    # Tasks completed this week/month
    tasks_completed_this_week = HumanTask.objects.filter(
        workflow_run__user_id=user_id,
        status=HumanTask.STATUS_COMPLETED,
        completed_at__gte=week_ago,
    ).count()

    tasks_completed_this_month = HumanTask.objects.filter(
        workflow_run__user_id=user_id,
        status=HumanTask.STATUS_COMPLETED,
        completed_at__gte=month_ago,
    ).count()

    # Average task completion time
    task_completion_stats = HumanTask.objects.filter(
        workflow_run__user_id=user_id,
        status=HumanTask.STATUS_COMPLETED,
        created_at__isnull=False,
        completed_at__isnull=False,
    ).aggregate(
        avg_completion_time=Avg(models.F("completed_at") - models.F("created_at")),
        min_completion_time=Min(models.F("completed_at") - models.F("created_at")),
        max_completion_time=Max(models.F("completed_at") - models.F("created_at")),
    )

    # Tasks by type breakdown
    tasks_by_type = dict(
        HumanTask.objects.filter(workflow_run__user_id=user_id)
        .values("task_type")
        .annotate(count=Count("task_id"))
        .values_list("task_type", "count")
    )

    # Overdue tasks count
    overdue_tasks = HumanTask.objects.filter(
        workflow_run__user_id=user_id,
        status__in=[HumanTask.STATUS_OPEN, HumanTask.STATUS_IN_PROGRESS],
        expires_at__lt=now,
    ).count()

    # Performance stats
    workflow_perf = WorkflowRun.objects.filter(
        user_id=user_id,
        status=WorkflowRun.STATUS_COMPLETED,
        started_at__isnull=False,
        completed_at__isnull=False,
    ).aggregate(
        avg_duration=Avg(models.F("completed_at") - models.F("started_at")),
        min_duration=Min(models.F("completed_at") - models.F("started_at")),
        max_duration=Max(models.F("completed_at") - models.F("started_at")),
    )

    def format_duration(td):
        if td:
            seconds = td.total_seconds()
            if seconds < 60:
                return f"{seconds:.1f}s"
            if seconds < 3600:
                return f"{seconds / 60:.1f}m"
            return f"{seconds / 3600:.1f}h"
        return "N/A"

    return {
        "total_workflow_runs": total_workflow_runs,
        "pending_workflows": pending_workflows,
        "running_workflows": running_workflows,
        "completed_workflows": completed_workflows,
        "failed_workflows": failed_workflows,
        "waiting_workflows": waiting_workflows,
        "workflow_success_rate": workflow_success_rate,
        "total_tasks": total_tasks,
        "open_tasks": open_tasks,
        "claimed_tasks": claimed_tasks,
        "completed_tasks": completed_tasks,
        "tasks_completed_this_week": tasks_completed_this_week,
        "tasks_completed_this_month": tasks_completed_this_month,
        "avg_task_completion_time": format_duration(
            task_completion_stats.get("avg_completion_time")
        ),
        "min_task_completion_time": format_duration(
            task_completion_stats.get("min_completion_time")
        ),
        "max_task_completion_time": format_duration(
            task_completion_stats.get("max_completion_time")
        ),
        "tasks_by_type": tasks_by_type,
        "overdue_tasks": overdue_tasks,
        "avg_workflow_duration": format_duration(workflow_perf.get("avg_duration")),
        "min_workflow_duration": format_duration(workflow_perf.get("min_duration")),
        "max_workflow_duration": format_duration(workflow_perf.get("max_duration")),
    }


def dashboard_view(request):
    """
    Display dashboard with usage statistics.
    Complexity reduced from 19 to ~7 by extracting helper functions.
    """
    from agent_app.health_checks import check_all_services, get_overall_status

    # Get session key
    if not request.session.session_key:
        request.session.create()

    user_id = request.session.get("user_id", ANONYMOUS_USER_ID)

    # Check service health
    services_health = check_all_services()
    overall_status = get_overall_status(services_health)

    # Calculate all statistics using helper functions
    message_stats = _calculate_message_stats(user_id)
    feedback_stats = _calculate_feedback_stats(user_id)
    performance_stats = _calculate_performance_stats(user_id)
    system_stats = _get_system_stats()
    workflow_stats = _calculate_workflow_stats(user_id)

    # Recent activity
    yesterday = timezone.now() - timedelta(days=1)
    recent_sessions = (
        ChatSession.objects.filter(user_id=user_id, messages__created_at__gte=yesterday)
        .annotate(message_count=Count("messages"))
        .order_by("-created_at")[:10]
    )

    active_sessions = (
        ChatSession.objects.filter(user_id=user_id, messages__created_at__gte=yesterday)
        .distinct()
        .count()
    )

    recent_workflows = WorkflowRun.objects.filter(user_id=user_id).order_by("-created_at")[:5]

    # Combine all stats
    stats = {
        **message_stats,
        **feedback_stats,
        **performance_stats,
        **system_stats,
        **workflow_stats,
        "active_sessions": active_sessions,
        "recent_sessions": recent_sessions,
        "recent_workflows": recent_workflows,
        "total_queries": message_stats["user_messages"],  # Alias
        "total_responses": message_stats["assistant_messages"],  # Alias
        "cache": services_health.get("redis", {}),
    }

    return render(
        request,
        "dashboard.html",
        {"stats": stats, "services": services_health, "overall_status": overall_status},
    )


# ===== Docs View with Helper Functions =====


def _validate_doc_path(path):
    """Validate and sanitize documentation path."""
    if ".." in path or path.startswith("/"):
        return None, "Invalid path"
    return path, None


def _get_doc_path(path):
    """Get and validate absolute documentation path."""
    docs_root = Path(__file__).resolve().parent.parent.parent / "docs"
    doc_path = docs_root / path

    try:
        doc_path = doc_path.resolve()
        if not str(doc_path).startswith(str(docs_root.resolve())):
            return None, "Access denied"
        if not doc_path.exists() or not doc_path.is_file():
            return None, f"Documentation file not found: {path}"
        return doc_path, None
    except Exception:
        return None, "Invalid path"


def _convert_markdown_to_html(markdown_content):
    """Convert markdown to HTML with extensions."""
    return markdown.markdown(
        markdown_content, extensions=["fenced_code", "tables", "toc", "nl2br", "sane_lists"]
    )


def _post_process_html(html_content, path):
    """Post-process HTML for mermaid diagrams, Section 508, and links."""
    # Convert Mermaid code blocks
    html_content = re.sub(
        r'<pre><code class="language-mermaid">(.*?)</code></pre>',
        r'<pre class="mermaid">\1</pre>',
        html_content,
        flags=re.DOTALL,
    )

    # Add Section 508 compliant CSS classes
    html_content = re.sub(
        r"<h1(\s[^>]*)?>",
        lambda m: f'<h1{m.group(1) or ""} class="doc-section-title">',
        html_content,
    )
    html_content = re.sub(
        r"<h2(\s[^>]*)?>",
        lambda m: f'<h2{m.group(1) or ""} class="doc-section-heading">',
        html_content,
    )
    html_content = re.sub(
        r"<h3(\s[^>]*)?>",
        lambda m: f'<h3{m.group(1) or ""} class="doc-subsection-heading">',
        html_content,
    )
    html_content = re.sub(
        r"<h4(\s[^>]*)?>",
        lambda m: f'<h4{m.group(1) or ""} class="doc-minor-heading">',
        html_content,
    )

    # Convert relative .md links
    def convert_md_link(match):
        link_text = match.group(1)
        link_path = match.group(2)
        if link_path.endswith(".md") and not link_path.startswith("http"):
            if link_path.startswith("../"):
                parent_path = "/".join(path.split("/")[:-1])
                resolved_path = link_path.replace("../", parent_path + "/" if parent_path else "")
            elif "/" not in link_path:
                parent_path = "/".join(path.split("/")[:-1])
                resolved_path = (parent_path + "/" if parent_path else "") + link_path
            else:
                resolved_path = link_path
            return f'<a href="/docs/{resolved_path}">{link_text}</a>'
        return match.group(0)

    html_content = re.sub(r'<a href="([^"]*\.md)">(.*?)</a>', convert_md_link, html_content)
    return html_content


def _extract_title(html_content, path):
    """Extract title from HTML or use filename."""
    import html as html_module

    title_match = re.search(r"<h1[^>]*>(.*?)</h1>", html_content)
    if title_match:
        title = title_match.group(1)
        title = re.sub(r"<[^>]+>", "", title)  # Strip HTML tags
        title = html_module.unescape(title)  # Unescape entities
    else:
        title = path.replace(".md", "").replace("_", " ").title()

    return title


def docs_view(request, path):
    """
    Display markdown documentation from docs/ directory.
    Complexity reduced from 11 to ~6 by extracting helper functions.
    """
    # Validate path
    path, error = _validate_doc_path(path)
    if error:
        return HttpResponseForbidden(error)

    # Get document path
    doc_path, error = _get_doc_path(path)
    if error:
        return HttpResponseNotFound(error)

    try:
        # Read markdown file
        with doc_path.open(encoding="utf-8") as f:
            markdown_content = f.read()

        # Convert to HTML
        html_content = _convert_markdown_to_html(markdown_content)

        # Post-process HTML
        html_content = _post_process_html(html_content, path)

        # Extract title
        title = _extract_title(html_content, path)

        return render(
            request,
            "docs/view.html",
            {"content": html_content, "page_title": title, "doc_path": path},
        )

    except Exception as e:
        logger.error(f"Error reading documentation file {path}: {e}")
        return HttpResponseNotFound(f"Error reading documentation: {str(e)}")


# ===== Other Admin Views =====


def tools_view(request):
    """Tools and utilities page: list tools for a selected agent (default or ?agent=<id>)."""
    from agents.registry import (
        get_agent_display_name,
        get_agents_for_template,
        get_default_agent_id,
    )
    from tools.list_tools import get_tools_list

    agents = get_agents_for_template()
    valid_ids = {a["id"] for a in agents}
    requested = (request.GET.get("agent") or "").strip().lower()
    selected_agent = requested if requested in valid_ids else get_default_agent_id()
    tools_list = get_tools_list(selected_agent)
    agent_display_name = get_agent_display_name(selected_agent, "Agent")

    return render(
        request,
        "tools.html",
        {
            "selected_agent": selected_agent,
            "agent_display_name": agent_display_name,
            "tools_list": tools_list,
        },
    )


def settings_view(request):
    """Settings page with user preferences"""
    from ..models import UserPreference

    user_id = request.session.get("user_id", ANONYMOUS_USER_ID)

    # Get or create user preference
    pref, created = UserPreference.objects.get_or_create(
        user_id=user_id, defaults={"context_message_count": 0, "section_508_enabled": False}
    )

    # Get default Section 508 mode from environment
    default_508 = os.getenv("SECTION_508_MODE", "false").lower() in ("true", "1", "yes")

    # Cache stats for Cache Management section (enables Clear Cache button when cache is on)
    try:
        import sys

        _agent_ui_root = Path(__file__).resolve().parent.parent.parent
        if str(_agent_ui_root) not in sys.path:
            sys.path.insert(0, str(_agent_ui_root))
        from cache import get_cache

        cache = get_cache()
        stats = cache.get_stats()
        cache_stats = {
            "enabled": stats.get("enabled", False),
            "connected": stats.get("connected", False),
            "cached_prompts": stats.get("cached_prompts", 0),
            "cache_hits": stats.get("total_hits", 0),
            "cache_misses": stats.get("total_misses", 0),
            "hit_rate": stats.get("hit_rate", 0),
            "ttl": getattr(cache, "ttl", 3600),
            "redis_db": "0",
            "memory_used": "N/A",
        }
    except Exception:
        cache_stats = {
            "enabled": False,
            "connected": False,
            "cached_prompts": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "hit_rate": 0,
            "ttl": 3600,
            "redis_db": "0",
            "memory_used": "N/A",
        }

    return render(
        request,
        "settings.html",
        {
            "context_message_count": pref.context_message_count,
            "section_508_enabled": pref.section_508_enabled
            if pref.section_508_enabled is not None
            else default_508,
            "default_508": default_508,
            "cache_stats": cache_stats,
        },
    )


def logs_api(request):
    """API endpoint to list available log files"""
    log_dir = Path(__file__).parent.parent.parent.parent / "logs"

    if not log_dir.exists():
        return JsonResponse({"logs": []})

    log_files = []
    for file_path in log_dir.glob("*.log"):
        log_files.append(
            {
                "name": file_path.name,
                "size": file_path.stat().st_size,
                "modified": file_path.stat().st_mtime,
            }
        )

    return JsonResponse({"logs": sorted(log_files, key=lambda x: x["modified"], reverse=True)})


def log_view(request, log_name):
    """View a specific log file"""
    from django.core.paginator import Paginator

    log_dir = Path(__file__).parent.parent.parent.parent / "logs"
    log_path = log_dir / log_name

    # Security: Prevent directory traversal
    if ".." in log_name or "/" in log_name:
        return HttpResponseForbidden("Invalid log name")

    if not log_path.exists():
        return HttpResponseNotFound(f"Log file not found: {log_name}")

    try:
        with log_path.open() as f:
            lines = f.readlines()

        # Reverse for newest first
        lines = list(reversed(lines))

        # Pagination
        paginator = Paginator(lines, 100)  # 100 lines per page
        page_number = request.GET.get("page", 1)
        page_obj = paginator.get_page(page_number)

        return render(
            request,
            "logs/view.html",
            {"log_name": log_name, "lines": page_obj, "page_obj": page_obj},
        )

    except Exception as e:
        logger.error(f"Error reading log file {log_name}: {e}")
        return HttpResponseNotFound(f"Error reading log file: {str(e)}")


def logs_view(request):
    """Logs listing page"""
    return render(request, "logs.html")


def prometheus_metrics(request):
    """Expose Prometheus metrics (includes property metrics from Api when API_URL/AUTH_TOKEN set)."""
    from django_prometheus.exports import ExportToDjangoView

    from agent_app.metrics_collector import collect_all_metrics

    collect_all_metrics()
    return ExportToDjangoView(request)


def prometheus_metrics_bi(request):
    """Expose only property (BI) metrics for scraping at 5m. Use /metrics/ for app metrics at 15s."""
    from agent_app.metrics_collector import get_property_metrics_output, update_property_metrics

    update_property_metrics()
    return HttpResponse(
        get_property_metrics_output(),
        content_type="text/plain; version=0.0.4; charset=utf-8",
    )


def prometheus_view(request):
    """Prometheus metrics dashboard"""
    return render(request, "prometheus.html")


def diagram_view(request, diagram_name):
    """Display Mermaid diagram"""
    from pathlib import Path

    # Security: Prevent directory traversal
    if ".." in diagram_name or "/" in diagram_name:
        return HttpResponseForbidden("Invalid diagram name")

    diagram_path = Path(__file__).parent.parent / "diagrams" / f"{diagram_name}.mmd"

    if not diagram_path.exists():
        return HttpResponseNotFound(f"Diagram not found: {diagram_name}")

    try:
        with diagram_path.open() as f:
            diagram_content = f.read()

        return render(
            request,
            "diagram.html",
            {"diagram_name": diagram_name, "diagram_content": diagram_content},
        )
    except Exception as e:
        logger.error(f"Error reading diagram {diagram_name}: {e}")
        return HttpResponseNotFound(f"Error reading diagram: {str(e)}")
