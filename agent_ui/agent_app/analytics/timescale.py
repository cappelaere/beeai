"""
Helpers for TimescaleDB setup SQL.
"""

from __future__ import annotations


def timescale_setup_sql() -> list[str]:
    """
    SQL statements for hypertable, rollups, and policies.
    Safe to run idempotently on PostgreSQL+TimescaleDB.
    """
    return [
        "CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;",
        """
        SELECT create_hypertable(
            'agent_app_pageviewevent',
            'event_time',
            if_not_exists => TRUE
        );
        """,
        """
        CREATE MATERIALIZED VIEW IF NOT EXISTS analytics_pageviews_hourly
        WITH (timescaledb.continuous) AS
        SELECT
            time_bucket('1 hour', event_time) AS bucket,
            canonical_path,
            COUNT(*)::bigint AS page_view_count,
            COUNT(DISTINCT NULLIF(visitor_id, ''))::bigint AS unique_visitor_count,
            COUNT(DISTINCT app_user_id)::bigint AS unique_user_count
        FROM agent_app_pageviewevent
        GROUP BY bucket, canonical_path;
        """,
        """
        CREATE MATERIALIZED VIEW IF NOT EXISTS analytics_pageviews_daily
        WITH (timescaledb.continuous) AS
        SELECT
            time_bucket('1 day', event_time) AS bucket,
            canonical_path,
            COUNT(*)::bigint AS page_view_count,
            COUNT(DISTINCT NULLIF(visitor_id, ''))::bigint AS unique_visitor_count,
            COUNT(DISTINCT app_user_id)::bigint AS unique_user_count
        FROM agent_app_pageviewevent
        GROUP BY bucket, canonical_path;
        """,
        """
        CREATE MATERIALIZED VIEW IF NOT EXISTS analytics_pageviews_weekly
        WITH (timescaledb.continuous) AS
        SELECT
            time_bucket('1 week', event_time) AS bucket,
            canonical_path,
            COUNT(*)::bigint AS page_view_count,
            COUNT(DISTINCT NULLIF(visitor_id, ''))::bigint AS unique_visitor_count,
            COUNT(DISTINCT app_user_id)::bigint AS unique_user_count
        FROM agent_app_pageviewevent
        GROUP BY bucket, canonical_path;
        """,
        """
        CREATE MATERIALIZED VIEW IF NOT EXISTS analytics_pageviews_monthly
        WITH (timescaledb.continuous) AS
        SELECT
            time_bucket('1 month', event_time) AS bucket,
            canonical_path,
            COUNT(*)::bigint AS page_view_count,
            COUNT(DISTINCT NULLIF(visitor_id, ''))::bigint AS unique_visitor_count,
            COUNT(DISTINCT app_user_id)::bigint AS unique_user_count
        FROM agent_app_pageviewevent
        GROUP BY bucket, canonical_path;
        """,
        """
        SELECT add_continuous_aggregate_policy(
            'analytics_pageviews_hourly',
            start_offset => INTERVAL '35 days',
            end_offset => INTERVAL '1 hour',
            schedule_interval => INTERVAL '1 hour',
            if_not_exists => TRUE
        );
        """,
        """
        SELECT add_continuous_aggregate_policy(
            'analytics_pageviews_daily',
            start_offset => INTERVAL '180 days',
            end_offset => INTERVAL '1 day',
            schedule_interval => INTERVAL '1 day',
            if_not_exists => TRUE
        );
        """,
        """
        SELECT add_continuous_aggregate_policy(
            'analytics_pageviews_weekly',
            start_offset => INTERVAL '370 days',
            end_offset => INTERVAL '1 week',
            schedule_interval => INTERVAL '1 day',
            if_not_exists => TRUE
        );
        """,
        """
        SELECT add_continuous_aggregate_policy(
            'analytics_pageviews_monthly',
            start_offset => INTERVAL '370 days',
            end_offset => INTERVAL '1 month',
            schedule_interval => INTERVAL '1 day',
            if_not_exists => TRUE
        );
        """,
        """
        SELECT add_retention_policy(
            'agent_app_pageviewevent',
            drop_after => INTERVAL '365 days',
            if_not_exists => TRUE
        );
        """,
    ]

