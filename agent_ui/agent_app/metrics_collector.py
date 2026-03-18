"""
Prometheus Metrics Collector for RealtyIQ Agent

This module defines and collects application metrics for Prometheus scraping.
"""

import logging

import psutil
from prometheus_client import (
    REGISTRY,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    Info,
    generate_latest,
)

logger = logging.getLogger(__name__)

# Application Info
app_info = Info("realtyiq_app", "RealtyIQ Application Information")
app_info.info(
    {
        "version": "1.0.0",
        "application": "RealtyIQ Agent",
        "description": "GSA Real Estate Sales Auction Assistant",
    }
)

# HTTP Request Metrics
http_requests_total = Counter(
    "realtyiq_http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"]
)

http_request_duration_seconds = Histogram(
    "realtyiq_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
)

# Agent Execution Metrics
agent_executions_total = Counter(
    "realtyiq_agent_executions_total", "Total agent executions", ["agent_type", "status"]
)

agent_execution_duration_seconds = Histogram(
    "realtyiq_agent_execution_duration_seconds",
    "Agent execution duration in seconds",
    ["agent_type"],
)

agent_tokens_used = Counter(
    "realtyiq_agent_tokens_used_total", "Total tokens used by agents", ["agent_type", "model"]
)

# Chat Session Metrics
chat_sessions_active = Gauge("realtyiq_chat_sessions_active", "Number of active chat sessions")

chat_messages_total = Counter(
    "realtyiq_chat_messages_total",
    "Total chat messages",
    ["role"],  # user, assistant, system
)

chat_errors_total = Gauge("realtyiq_chat_errors_total", "Total error messages in chat responses")

# Database Metrics
database_queries_total = Counter(
    "realtyiq_database_queries_total",
    "Total database queries",
    ["operation"],  # select, insert, update, delete
)

database_query_duration_seconds = Histogram(
    "realtyiq_database_query_duration_seconds", "Database query duration in seconds", ["operation"]
)

# Cache Metrics
cache_operations_total = Counter(
    "realtyiq_cache_operations_total",
    "Total cache operations",
    ["operation", "status"],  # get/set/delete, hit/miss/success/error
)

cache_size_bytes = Gauge("realtyiq_cache_size_bytes", "Current cache size in bytes")

# Document Library Metrics
documents_total = Gauge("realtyiq_documents_total", "Total documents in library")

document_searches_total = Counter(
    "realtyiq_document_searches_total", "Total document searches", ["status"]
)

# Assistant Card Metrics
cards_total = Gauge("realtyiq_cards_total", "Total assistant cards")

card_executions_total = Counter(
    "realtyiq_card_executions_total", "Total card executions", ["card_id", "status"]
)

# API Health Metrics
api_health_checks_total = Counter(
    "realtyiq_api_health_checks_total", "Total API health checks", ["service", "status"]
)

# System Resource Metrics
system_cpu_usage_percent = Gauge("realtyiq_system_cpu_usage_percent", "System CPU usage percentage")

system_memory_usage_bytes = Gauge(
    "realtyiq_system_memory_usage_bytes", "System memory usage in bytes"
)

system_memory_available_bytes = Gauge(
    "realtyiq_system_memory_available_bytes", "System memory available in bytes"
)

system_disk_usage_percent = Gauge(
    "realtyiq_system_disk_usage_percent", "System disk usage percentage"
)

# Error Metrics
errors_total = Counter("realtyiq_errors_total", "Total errors", ["error_type", "component"])

# Workflow Metrics
workflow_runs_total = Counter(
    "realtyiq_workflow_runs_total", "Total workflow runs", ["workflow_id", "status"]
)

workflow_runs_active = Gauge(
    "realtyiq_workflow_runs_active", "Number of currently active workflow runs"
)

workflow_execution_duration_seconds = Histogram(
    "realtyiq_workflow_execution_duration_seconds",
    "Workflow execution duration in seconds",
    ["workflow_id"],
)

workflow_tasks_total = Counter(
    "realtyiq_workflow_tasks_total", "Total workflow tasks", ["task_type", "status"]
)

workflow_tasks_pending = Gauge(
    "realtyiq_workflow_tasks_pending", "Number of pending workflow tasks"
)

workflow_tasks_claimed = Gauge(
    "realtyiq_workflow_tasks_claimed", "Number of claimed workflow tasks"
)

workflow_tasks_completed_weekly = Gauge(
    "realtyiq_workflow_tasks_completed_weekly", "Number of tasks completed in the last 7 days"
)

workflow_tasks_completed_monthly = Gauge(
    "realtyiq_workflow_tasks_completed_monthly", "Number of tasks completed in the last 30 days"
)

workflow_tasks_overdue = Gauge(
    "realtyiq_workflow_tasks_overdue", "Number of overdue tasks (past expiration date)"
)

workflow_task_completion_duration_seconds = Histogram(
    "realtyiq_workflow_task_completion_duration_seconds",
    "Task completion duration in seconds (from creation to completion)",
    ["task_type"],
)

workflow_tasks_by_type = Gauge(
    "realtyiq_workflow_tasks_by_type", "Number of tasks by type", ["task_type"]
)

# Property metrics (BI) - on separate registry so /metrics/ (15s) does not export or update them.
# Only /metrics/bi/ (5m) updates and exports these; avoids Api calls every 15s and duplicate series.
_property_registry = CollectorRegistry()
property_metrics_properties_with_activity_24h = Gauge(
    "property_metrics_properties_with_activity_24h",
    "Count of property_ids with at least one event in last 24h",
    registry=_property_registry,
)
property_metrics_properties_with_activity_7d = Gauge(
    "property_metrics_properties_with_activity_7d",
    "Count of property_ids with at least one event in last 7d",
    registry=_property_registry,
)
property_metrics_funnel_last_7d = Gauge(
    "property_metrics_funnel_last_7d",
    "Portfolio 7d totals by metric (views, brochure_downloads, ifb_downloads, etc.)",
    ["metric"],
    registry=_property_registry,
)
property_metrics_num_viewers = Gauge(
    "property_metrics_num_viewers",
    "Total views for the property in the window",
    ["property_id"],
    registry=_property_registry,
)
property_metrics_num_bidders = Gauge(
    "property_metrics_num_bidders",
    "Bidder registrations for the property",
    ["property_id"],
    registry=_property_registry,
)
property_metrics_num_subscribers = Gauge(
    "property_metrics_num_subscribers",
    "Subscriber registrations for the property",
    ["property_id"],
    registry=_property_registry,
)
property_metrics_brochure_downloads = Gauge(
    "property_metrics_brochure_downloads",
    "Brochure downloads for the property",
    ["property_id"],
    registry=_property_registry,
)
property_metrics_ifb_downloads = Gauge(
    "property_metrics_ifb_downloads",
    "IFB downloads for the property",
    ["property_id"],
    registry=_property_registry,
)
property_metrics_unique_sessions = Gauge(
    "property_metrics_unique_sessions",
    "Unique sessions for the property",
    ["property_id"],
    registry=_property_registry,
)


def update_system_metrics():
    """Update system resource metrics"""
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=0.1)
        system_cpu_usage_percent.set(cpu_percent)

        # Memory usage
        memory = psutil.virtual_memory()
        system_memory_usage_bytes.set(memory.used)
        system_memory_available_bytes.set(memory.available)

        # Disk usage
        disk = psutil.disk_usage("/")
        system_disk_usage_percent.set(disk.percent)

    except Exception:
        errors_total.labels(error_type="system_metrics", component="metrics_collector").inc()


def update_database_metrics():
    """Update database-related metrics"""
    try:
        from datetime import timedelta

        from django.db import models as django_models
        from django.db.models import Q
        from django.utils import timezone

        from agent_app.models import (
            AssistantCard,
            ChatMessage,
            ChatSession,
            Document,
            HumanTask,
            WorkflowRun,
        )

        # Active sessions (last 24 hours)
        yesterday = timezone.now() - timedelta(days=1)
        active_sessions = (
            ChatSession.objects.filter(messages__created_at__gte=yesterday).distinct().count()
        )
        chat_sessions_active.set(active_sessions)

        # Error messages count (detect error patterns in content)
        error_messages = (
            ChatMessage.objects.filter(role=ChatMessage.ROLE_ASSISTANT)
            .filter(
                Q(content__icontains="Error (")
                | Q(content__icontains="**Error")
                | Q(content__icontains="ToolError")
                | Q(content__icontains="API error")
            )
            .count()
        )

        # Update error gauge
        chat_errors_total.set(error_messages)

        # Total documents
        doc_count = Document.objects.count()
        documents_total.set(doc_count)

        # Total cards
        card_count = AssistantCard.objects.count()
        cards_total.set(card_count)

        # Workflow metrics
        # Active workflow runs (running or waiting for task)
        active_runs = WorkflowRun.objects.filter(
            status__in=[WorkflowRun.STATUS_RUNNING, WorkflowRun.STATUS_WAITING_FOR_TASK]
        ).count()
        workflow_runs_active.set(active_runs)

        # Pending tasks (open and in progress)
        pending_tasks = HumanTask.objects.filter(
            status__in=[HumanTask.STATUS_OPEN, HumanTask.STATUS_IN_PROGRESS]
        ).count()
        workflow_tasks_pending.set(pending_tasks)

        # Claimed/In-progress tasks
        claimed_tasks = HumanTask.objects.filter(status=HumanTask.STATUS_IN_PROGRESS).count()
        workflow_tasks_claimed.set(claimed_tasks)

        # Enhanced task metrics
        week_ago = timezone.now() - timedelta(days=7)
        month_ago = timezone.now() - timedelta(days=30)

        # Tasks completed this week/month
        tasks_week = HumanTask.objects.filter(
            status=HumanTask.STATUS_COMPLETED, completed_at__gte=week_ago
        ).count()
        workflow_tasks_completed_weekly.set(tasks_week)

        tasks_month = HumanTask.objects.filter(
            status=HumanTask.STATUS_COMPLETED, completed_at__gte=month_ago
        ).count()
        workflow_tasks_completed_monthly.set(tasks_month)

        # Overdue tasks
        overdue = HumanTask.objects.filter(
            status__in=[HumanTask.STATUS_OPEN, HumanTask.STATUS_IN_PROGRESS],
            expires_at__lt=timezone.now(),
        ).count()
        workflow_tasks_overdue.set(overdue)

        # Tasks by type
        tasks_by_type = HumanTask.objects.values("task_type").annotate(
            count=django_models.Count("task_id")
        )
        for task_type_data in tasks_by_type:
            task_type = task_type_data["task_type"]
            count = task_type_data["count"]
            workflow_tasks_by_type.labels(task_type=task_type).set(count)

    except Exception:
        errors_total.labels(error_type="database_metrics", component="metrics_collector").inc()


def update_cache_metrics():
    """Update cache-related metrics"""
    try:
        from django.core.cache import cache

        # Try to get cache size
        try:
            redis_client = cache._cache.get_client(write=False)
            info = redis_client.info("memory")
            used_memory = info.get("used_memory", 0)
            cache_size_bytes.set(used_memory)
        except Exception as e:
            logger.debug("Could not get Redis cache memory info: %s", e)

    except Exception:
        errors_total.labels(error_type="cache_metrics", component="metrics_collector").inc()


def update_property_metrics():
    """
    Fetch property metrics from Api read APIs and set gauges.
    Only active properties (activity in last 7d) are included.
    Runs when /metrics is scraped (every 5m). Api is the data source; no scraping of Api.
    """
    import os

    import requests

    api_base = (os.environ.get("API_URL") or "").rstrip("/")
    auth_token = os.environ.get("AUTH_TOKEN") or ""
    if not api_base or not auth_token:
        return
    tls_verify = os.getenv("TLS_VERIFY", "true").lower() in ("1", "true", "yes")
    timeout = 30
    headers = {
        "Authorization": f"Token {auth_token}",
        "Accept": "application/json",
    }
    session = requests.Session()
    session.headers.update(headers)

    try:
        # Portfolio: properties with activity 24h and 7d
        for days_val, gauge in [
            (1, property_metrics_properties_with_activity_24h),
            (7, property_metrics_properties_with_activity_7d),
        ]:
            try:
                r = session.get(
                    f"{api_base}/api/metrics/properties-with-activity",
                    params={"days": days_val, "limit": 5000},
                    timeout=timeout,
                    verify=tls_verify,
                )
                r.raise_for_status()
                data = r.json()
                ids = data.get("property_ids", []) if isinstance(data, dict) else []
                gauge.set(len(ids))
            except Exception as e:
                logger.debug(
                    "Could not fetch properties-with-activity for days=%s: %s", days_val, e
                )

        # Active property IDs (last 7d)
        try:
            r = session.get(
                f"{api_base}/api/metrics/properties-with-activity",
                params={"days": 7, "limit": 500},
                timeout=timeout,
                verify=tls_verify,
            )
            r.raise_for_status()
            data = r.json()
            active_ids = data.get("property_ids", []) if isinstance(data, dict) else []
        except Exception:
            active_ids = []

        # Set per-property gauges for active IDs only; aggregate funnel from summaries
        funnel_totals = {
            "views": 0,
            "brochure_downloads": 0,
            "ifb_downloads": 0,
            "bidder_registrations": 0,
            "subscriber_registrations": 0,
            "photo_clicks": 0,
        }
        for prop_id in active_ids:
            try:
                pid = str(prop_id) if not isinstance(prop_id, str) else prop_id
                r = session.get(
                    f"{api_base}/api/metrics/properties/{pid}/summary",
                    params={"days": 7},
                    timeout=timeout,
                    verify=tls_verify,
                )
                r.raise_for_status()
                s = r.json()
                totals = s.get("totals", {}) if isinstance(s, dict) else {}
                if not isinstance(totals, dict):
                    totals = {}
                views = int(totals.get("views") or 0)
                unique_sessions = int(totals.get("unique_sessions") or 0)
                brochure_downloads = int(totals.get("brochure_downloads") or 0)
                ifb_downloads = int(totals.get("ifb_downloads") or 0)
                bidder_registrations = int(totals.get("bidder_registrations") or 0)
                subscriber_registrations = int(totals.get("subscriber_registrations") or 0)
                photo_clicks = int(totals.get("photo_clicks") or 0)
                property_metrics_num_viewers.labels(property_id=pid).set(views)
                property_metrics_num_bidders.labels(property_id=pid).set(bidder_registrations)
                property_metrics_num_subscribers.labels(property_id=pid).set(
                    subscriber_registrations
                )
                property_metrics_brochure_downloads.labels(property_id=pid).set(brochure_downloads)
                property_metrics_ifb_downloads.labels(property_id=pid).set(ifb_downloads)
                property_metrics_unique_sessions.labels(property_id=pid).set(unique_sessions)
                funnel_totals["views"] += views
                funnel_totals["brochure_downloads"] += brochure_downloads
                funnel_totals["ifb_downloads"] += ifb_downloads
                funnel_totals["bidder_registrations"] += bidder_registrations
                funnel_totals["subscriber_registrations"] += subscriber_registrations
                funnel_totals["photo_clicks"] += photo_clicks
            except Exception as e:
                logger.debug("Could not set property metrics for property %s: %s", pid, e)
                continue

        for metric_name, value in funnel_totals.items():
            property_metrics_funnel_last_7d.labels(metric=metric_name).set(value)
    except Exception:
        errors_total.labels(error_type="property_metrics", component="metrics_collector").inc()


def collect_all_metrics():
    """Collect app/infra metrics only (no property metrics). Use for /metrics/ (15s scrape)."""
    update_system_metrics()
    update_database_metrics()
    update_cache_metrics()
    return REGISTRY


def get_property_metrics_output():
    """Return Prometheus exposition format for property_metrics_* only. Use for /metrics/bi/ (5m scrape)."""
    return generate_latest(_property_registry)
