"""
Time series charting tool for agent use.
Accepts JSON array of objects (e.g. DAP API response), builds a line or bar chart
with Plotly, exports PNG via Kaleido (no external access). When Django cache is
available, stores the PNG and returns a short URL so the LLM context stays small
(avoids rate limits). Otherwise returns base64-embedded markdown for CLI use.
"""

import base64
import io
import json
import re
import uuid
from datetime import datetime
from numbers import Number

from beeai_framework.tools import StringToolOutput, tool
from plotly import graph_objects as go

CHART_CACHE_PREFIX = "agent_chart_"
CHART_CACHE_TIMEOUT = 3600  # 1 hour

MAX_POINTS = 500  # Cap to avoid huge images


def _parse_data_json(data_json: str) -> list[dict]:
    """Parse data_json into a list of objects. Accepts array or object with array value."""
    data = json.loads(data_json)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for v in data.values():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                return v
        # Single key might be the array name
        for k in ("data", "results", "rows"):
            if k in data and isinstance(data[k], list):
                return data[k]
    raise ValueError(
        "data_json must be a JSON array of objects or an object containing such an array"
    )


def _infer_date_column(rows: list[dict]) -> str:
    for candidate in ("date", "report_date", "Date", "report_date_time"):
        if rows and candidate in rows[0]:
            return candidate
    if not rows or not rows[0]:
        raise ValueError("No date column found")
    for key in rows[0]:
        val = rows[0].get(key)
        if val is None:
            continue
        s = str(val).strip()
        if re.match(r"\d{4}-\d{2}-\d{2}", s) or "T" in s:
            return key
    raise ValueError("No date-like column found in data")


def _infer_value_columns(rows: list[dict], date_col: str) -> list[str]:
    numeric_candidates = (
        "visits",
        "pageviews",
        "pageviews_per_session",
        "users",
        "views",
        "unique_sessions",
        "value",
        "count",
        "total",
    )
    found = []
    if not rows:
        return found
    first = rows[0]
    for c in numeric_candidates:
        if c in first and c != date_col:
            found.append(c)
    if found:
        return found
    for key in first:
        if key == date_col:
            continue
        val = first.get(key)
        if val is not None and (
            isinstance(val, Number)
            or (isinstance(val, str) and val.replace(".", "").replace("-", "").isdigit())
        ):
            found.append(key)
    return found


def _parse_date(val) -> str:
    """Return a string suitable for x-axis (YYYY-MM-DD or ISO date part)."""
    if val is None:
        return ""
    s = str(val).strip()
    if re.match(r"^\d{4}-\d{2}-\d{2}", s):
        return s[:10]
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return s


def _to_number(val):
    if val is None:
        return 0
    if isinstance(val, Number):
        return float(val)
    s = str(val).strip().replace(",", "")
    try:
        return float(s)
    except ValueError:
        return 0


def _build_time_series_figure(rows, date_col, value_cols, chart_type, title):
    """Build Plotly figure for time series."""
    dates = [_parse_date(r.get(date_col)) for r in rows]
    fig = go.Figure()
    for col in value_cols:
        values = [_to_number(r.get(col)) for r in rows]
        if chart_type == "line":
            fig.add_trace(go.Scatter(x=dates, y=values, mode="lines+markers", name=col))
        else:
            fig.add_trace(go.Bar(x=dates, y=values, name=col))
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Value",
        template="plotly_white",
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
        margin={"t": 50, "b": 50, "l": 60, "r": 40},
        height=400,
    )
    if chart_type == "bar" and len(value_cols) > 1:
        fig.update_layout(barmode="group")
    return fig


def _export_chart_markdown(png_bytes: bytes, caption: str) -> StringToolOutput:
    """Return markdown with cache URL or base64 fallback."""
    try:
        from django.core.cache import cache

        chart_id = str(uuid.uuid4())
        cache.set(f"{CHART_CACHE_PREFIX}{chart_id}", png_bytes, timeout=CHART_CACHE_TIMEOUT)
        return StringToolOutput(f"![{caption}](/api/agent-chart/{chart_id}/)\n\n{caption}")
    except Exception:
        b64 = base64.b64encode(png_bytes).decode("ascii")
        return StringToolOutput(f"![{caption}](data:image/png;base64,{b64})\n\n{caption}")


@tool
def chart_time_series(
    data_json: str,
    title: str,
    date_column: str | None = None,
    value_columns: str | None = None,
    chart_type: str = "line",
) -> StringToolOutput:
    """
    Plot time series data as a chart and return markdown with an embedded PNG image.
    Use after fetching DAP or other time-series data (e.g. get_dap_domain_analytics) to visualize visits or other metrics over time.
    data_json: JSON string - array of objects with at least one date field and one or more numeric fields (e.g. DAP API response).
    title: Chart title.
    date_column: Key for x-axis (default: infer from date, report_date, or first date-like column).
    value_columns: Comma-separated numeric keys to plot (default: infer e.g. visits, pageviews).
    chart_type: 'line' or 'bar'.
    """
    try:
        rows = _parse_data_json(data_json)
    except json.JSONDecodeError as e:
        return StringToolOutput(f"Error: Invalid JSON in data_json: {e}")
    except ValueError as e:
        return StringToolOutput(f"Error: {e}")
    if not rows:
        return StringToolOutput("Error: No data rows to chart.")
    try:
        date_col = date_column or _infer_date_column(rows)
    except ValueError as e:
        return StringToolOutput(f"Error: {e}")
    value_cols = value_columns.split(",") if value_columns else _infer_value_columns(rows, date_col)
    value_cols = [c.strip() for c in value_cols if c.strip()]
    if not value_cols:
        return StringToolOutput(
            "Error: No numeric columns found to plot. Specify value_columns (e.g. visits, pageviews)."
        )
    if len(rows) > MAX_POINTS:
        rows = rows[-MAX_POINTS:]
    dates = [_parse_date(r.get(date_col)) for r in rows]
    if not dates or all(not d for d in dates):
        return StringToolOutput("Error: No valid dates in the date column.")
    chart_type = (chart_type or "line").strip().lower()
    if chart_type not in ("line", "bar"):
        chart_type = "line"
    fig = _build_time_series_figure(rows, date_col, value_cols, chart_type, title)
    buf = io.BytesIO()
    try:
        fig.write_image(buf, format="png", engine="kaleido", scale=1.5)
    except Exception as e:
        return StringToolOutput(
            f"Error generating chart image: {e}. Ensure kaleido is installed: pip install kaleido"
        )
    buf.seek(0)
    return _export_chart_markdown(buf.read(), f"Chart: {title}")
