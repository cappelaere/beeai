"""
Read/query helpers for the internal website analytics dashboard.
"""
# ruff: noqa: S608

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

from django.db import connection
from django.db.models import Count, Q
from django.db.models.functions import TruncDay, TruncHour, TruncMonth, TruncWeek
from django.utils import timezone

from .models import PageViewEvent, TrackedPage

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DashboardFilters:
    start: datetime
    end: datetime
    range_key: str
    page: str


RANGE_TO_DELTA = {
    "24h": timedelta(hours=24),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
    "90d": timedelta(days=90),
}


def build_dashboard_filters(range_key: str, page: str = "") -> DashboardFilters:
    now = timezone.now()
    effective_range_key = range_key if range_key in RANGE_TO_DELTA else "30d"
    delta = RANGE_TO_DELTA[effective_range_key]
    return DashboardFilters(
        start=now - delta,
        end=now,
        range_key=effective_range_key,
        page=(page or "").strip(),
    )


ROLLUP_VIEW_BY_GRANULARITY = {
    "hour": "analytics_pageviews_hourly",
    "day": "analytics_pageviews_daily",
    "week": "analytics_pageviews_weekly",
    "month": "analytics_pageviews_monthly",
}


def _postgres_relation_exists(relation_name: str) -> bool:
    if connection.vendor != "postgresql":
        return False
    with connection.cursor() as cursor:
        cursor.execute("SELECT to_regclass(%s);", [relation_name])
        row = cursor.fetchone()
    return bool(row and row[0])


def _rollup_view_for_granularity(granularity: str) -> str:
    return ROLLUP_VIEW_BY_GRANULARITY[granularity]


def _can_use_rollup(granularity: str) -> bool:
    if connection.vendor != "postgresql":
        return False
    return _postgres_relation_exists(_rollup_view_for_granularity(granularity))


def _bucket_expr(granularity: str):
    if granularity == "hour":
        return TruncHour("event_time")
    if granularity == "day":
        return TruncDay("event_time")
    if granularity == "week":
        return TruncWeek("event_time")
    return TruncMonth("event_time")


def _top_pages_from_events(filters: DashboardFilters) -> list[dict]:
    qs = PageViewEvent.objects.filter(event_time__gte=filters.start, event_time__lt=filters.end)
    if filters.page:
        qs = qs.filter(canonical_path=filters.page)

    rows = (
        qs.values("canonical_path")
        .annotate(
            page_views=Count("id"),
            unique_visitors=Count("visitor_id", filter=~Q(visitor_id=""), distinct=True),
            unique_users=Count("app_user_id", distinct=True),
        )
        .order_by("-page_views", "canonical_path")[:10]
    )
    return list(rows)


def _trend_from_events(filters: DashboardFilters, granularity: str) -> list[dict]:
    qs = PageViewEvent.objects.filter(event_time__gte=filters.start, event_time__lt=filters.end)
    if filters.page:
        qs = qs.filter(canonical_path=filters.page)

    rows = (
        qs.annotate(bucket=_bucket_expr(granularity))
        .values("bucket")
        .annotate(
            page_views=Count("id"),
            unique_visitors=Count("visitor_id", filter=~Q(visitor_id=""), distinct=True),
            unique_users=Count("app_user_id", distinct=True),
        )
        .order_by("bucket")
    )
    return [
        {
            "bucket": row["bucket"].isoformat() if row["bucket"] else "",
            "page_views": int(row["page_views"]),
            "unique_visitors": int(row["unique_visitors"]),
            "unique_users": int(row["unique_users"]),
        }
        for row in rows
    ]


def _summary_from_events(filters: DashboardFilters) -> dict:
    qs = PageViewEvent.objects.filter(event_time__gte=filters.start, event_time__lt=filters.end)
    if filters.page:
        qs = qs.filter(canonical_path=filters.page)
    return {
        "page_views": int(qs.count()),
        "unique_visitors": int(qs.exclude(visitor_id="").values("visitor_id").distinct().count()),
        "unique_users": int(qs.values("app_user_id").distinct().count()),
    }


def _summary_from_rollup(filters: DashboardFilters) -> dict:
    view_name = _rollup_view_for_granularity("day")
    where_parts = ["bucket >= %s", "bucket < %s"]
    params: list = [filters.start, filters.end]
    if filters.page:
        where_parts.append("canonical_path = %s")
        params.append(filters.page)
    where_sql = " AND ".join(where_parts)
    sql = f"""
        SELECT
            COALESCE(SUM(page_view_count), 0) AS page_views,
            COALESCE(SUM(unique_visitor_count), 0) AS unique_visitors,
            COALESCE(SUM(unique_user_count), 0) AS unique_users
        FROM {view_name}
        WHERE {where_sql}
    """
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        row = cursor.fetchone() or [0, 0, 0]
    return {
        "page_views": int(row[0] or 0),
        "unique_visitors": int(row[1] or 0),
        "unique_users": int(row[2] or 0),
    }


def _top_pages_from_rollup(filters: DashboardFilters) -> list[dict]:
    view_name = _rollup_view_for_granularity("day")
    where_parts = ["bucket >= %s", "bucket < %s"]
    params: list = [filters.start, filters.end]
    if filters.page:
        where_parts.append("canonical_path = %s")
        params.append(filters.page)
    where_sql = " AND ".join(where_parts)
    sql = f"""
        SELECT
            canonical_path,
            COALESCE(SUM(page_view_count), 0) AS page_views,
            COALESCE(SUM(unique_visitor_count), 0) AS unique_visitors,
            COALESCE(SUM(unique_user_count), 0) AS unique_users
        FROM {view_name}
        WHERE {where_sql}
        GROUP BY canonical_path
        ORDER BY page_views DESC, canonical_path ASC
        LIMIT 10
    """
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        rows = cursor.fetchall()
    return [
        {
            "canonical_path": str(row[0]),
            "page_views": int(row[1] or 0),
            "unique_visitors": int(row[2] or 0),
            "unique_users": int(row[3] or 0),
        }
        for row in rows
    ]


def _trend_from_rollup(filters: DashboardFilters, granularity: str) -> list[dict]:
    view_name = _rollup_view_for_granularity(granularity)
    where_parts = ["bucket >= %s", "bucket < %s"]
    params: list = [filters.start, filters.end]
    if filters.page:
        where_parts.append("canonical_path = %s")
        params.append(filters.page)
    where_sql = " AND ".join(where_parts)
    sql = f"""
        SELECT
            bucket,
            COALESCE(SUM(page_view_count), 0) AS page_views,
            COALESCE(SUM(unique_visitor_count), 0) AS unique_visitors,
            COALESCE(SUM(unique_user_count), 0) AS unique_users
        FROM {view_name}
        WHERE {where_sql}
        GROUP BY bucket
        ORDER BY bucket ASC
    """
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        rows = cursor.fetchall()
    return [
        {
            "bucket": row[0].isoformat() if row[0] else "",
            "page_views": int(row[1] or 0),
            "unique_visitors": int(row[2] or 0),
            "unique_users": int(row[3] or 0),
        }
        for row in rows
    ]


def _available_pages() -> list[dict]:
    return list(
        TrackedPage.objects.filter(enabled=True)
        .order_by("canonical_path")
        .values("canonical_path", "name", "key")
    )


def get_dashboard_data(filters: DashboardFilters) -> dict:
    """
    Return summary/trend/top-pages dashboard payload.
    Uses Timescale rollups when available, otherwise raw events.
    """
    if _can_use_rollup("day"):
        try:
            summary = _summary_from_rollup(filters)
            top_pages = _top_pages_from_rollup(filters)
            summary_source = "rollup_day"
        except Exception as exc:
            logger.warning("Daily rollup query failed; falling back to raw events: %s", exc)
            summary = _summary_from_events(filters)
            top_pages = _top_pages_from_events(filters)
            summary_source = "raw_events_fallback"
    else:
        summary = _summary_from_events(filters)
        top_pages = _top_pages_from_events(filters)
        summary_source = "raw_events"

    trends: dict[str, list[dict]] = {}
    trend_sources: dict[str, str] = {}
    for granularity in ("hour", "day", "week", "month"):
        if _can_use_rollup(granularity):
            try:
                trends[granularity] = _trend_from_rollup(filters, granularity)
                trend_sources[granularity] = f"rollup_{granularity}"
                continue
            except Exception as exc:
                logger.warning(
                    "Rollup trend query failed for %s; fallback to raw events: %s",
                    granularity,
                    exc,
                )
                trend_sources[granularity] = "raw_events_fallback"
        else:
            trend_sources[granularity] = "raw_events"
        trends[granularity] = _trend_from_events(filters, granularity)

    return {
        "summary": summary,
        "top_pages": top_pages,
        "trends": trends,
        "trend_sources": trend_sources,
        "pages": _available_pages(),
        "source": summary_source,
    }
