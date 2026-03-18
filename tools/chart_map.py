"""
Map charting tool for agent use.
Accepts JSON array of objects with latitude/longitude, plots points on a map
with Plotly Scattergeo, exports PNG via Kaleido (no external access). Uses the
same cache+URL pattern as chart_time_series for chat display.
"""

import base64
import io
import json
import uuid
from numbers import Number

from beeai_framework.tools import StringToolOutput, tool
from plotly import graph_objects as go

CHART_CACHE_PREFIX = "agent_chart_"
CHART_CACHE_TIMEOUT = 3600  # 1 hour
MAX_POINTS = 500  # Cap to avoid huge images


def _parse_data_json(data_json: str) -> list[dict]:
    """Parse data_json into a list of objects."""
    data = json.loads(data_json)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for k in ("data", "results", "rows", "features"):
            if k in data and isinstance(data[k], list) and data[k] and isinstance(data[k][0], dict):
                return data[k]
        for v in data.values():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                return v
    raise ValueError(
        "data_json must be a JSON array of objects or an object containing such an array"
    )


def _find_lat_lon_pair(first: dict, lat_set: set, lon_set: set) -> tuple[str, str] | None:
    """Return (lat_key, lon_key) if first has one key in lat_set and one in lon_set, else None."""
    lat_key = next((k for k in first if k.lower() in lat_set), None)
    lon_key = next((k for k in first if k.lower() in lon_set), None)
    return (lat_key, lon_key) if lat_key and lon_key else None


def _infer_lat_lon_columns(rows: list[dict]) -> tuple[str, str]:
    """Return (lat_col, lon_col). Prefer latitude/longitude, then lat/lon, then y/x."""
    if not rows or not rows[0]:
        raise ValueError("No data rows")
    first = rows[0]
    for lat_cand, lon_cand in [
        ("latitude", "longitude"),
        ("lat", "lon"),
        ("lat", "lng"),
        ("y", "x"),
    ]:
        if lat_cand in first and lon_cand in first:
            return lat_cand, lon_cand
    pair = _find_lat_lon_pair(
        first,
        {"latitude", "lat"},
        {"longitude", "lon", "lng"},
    )
    if pair:
        return pair
    raise ValueError(
        "No latitude/longitude columns found. Use lat_column and lon_column (e.g. latitude, longitude)."
    )


def _to_number(val) -> float:
    if val is None:
        return 0.0
    if isinstance(val, Number):
        return float(val)
    s = str(val).strip().replace(",", "")
    try:
        return float(s)
    except ValueError:
        return 0.0


def _prepare_map_points(rows, lat_col, lon_col, label_column, size_column):
    """Return (lats, lons, texts, sizes) or raise ValueError."""
    if len(rows) > MAX_POINTS:
        rows = rows[:MAX_POINTS]
    lats = [_to_number(r.get(lat_col)) for r in rows]
    lons = [_to_number(r.get(lon_col)) for r in rows]
    valid_rows, valid_lats, valid_lons = [], [], []
    for r, la, lo in zip(rows, lats, lons, strict=False):
        if -90 <= la <= 90 and -180 <= lo <= 180 and (la != 0 or lo != 0):
            valid_rows.append(r)
            valid_lats.append(la)
            valid_lons.append(lo)
    if not valid_lats:
        raise ValueError(
            "No valid latitude/longitude values in the data (need -90..90, -180..180)."
        )
    texts = None
    if label_column and valid_rows and label_column in valid_rows[0]:
        texts = [str(r.get(label_column, "")) for r in valid_rows]
    sizes = None
    if size_column and valid_rows and size_column in valid_rows[0]:
        raw = [_to_number(r.get(size_column)) for r in valid_rows]
        if any(s > 0 for s in raw):
            lo_s, hi_s = min(raw), max(raw)
            sizes = (
                [5 + 35 * (s - lo_s) / (hi_s - lo_s) for s in raw]
                if hi_s > lo_s
                else [15] * len(raw)
            )
    return valid_lats, valid_lons, texts, sizes


def _build_map_figure(lats, lons, title, scope, texts, sizes):
    """Build Plotly Scattergeo figure."""
    scope = (scope or "world").strip().lower()
    if scope not in ("world", "usa"):
        scope = "world"
    fig = go.Figure()
    fig.add_trace(
        go.Scattergeo(
            lat=lats,
            lon=lons,
            text=texts,
            mode="markers",
            marker={
                "size": sizes if sizes else 10,
                "color": "rgb(15, 98, 254)",
                "line": {"width": 1, "color": "white"},
            },
            name="",
        )
    )
    fig.update_layout(
        title=title,
        geo={
            "scope": scope,
            "showland": True,
            "showlakes": True,
            "showcountries": True,
            "landcolor": "rgb(243, 243, 243)",
            "lakecolor": "rgb(204, 224, 255)",
            "countrycolor": "rgb(200, 200, 200)",
            "coastlinecolor": "rgb(200, 200, 200)",
            "projection": {"type": "natural earth" if scope == "world" else "albers usa"},
        },
        margin={"t": 50, "b": 20, "l": 20, "r": 20},
        height=400,
        showlegend=False,
    )
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
def chart_map(
    data_json: str,
    title: str,
    lat_column: str | None = None,
    lon_column: str | None = None,
    label_column: str | None = None,
    size_column: str | None = None,
    scope: str = "world",
) -> StringToolOutput:
    """
    Plot individual locations as points on a map from latitude/longitude data. For density or counts by state/region use chart_choropleth instead.
    Use for locations, properties, or any geo-tagged data (e.g. properties with lat/lon, office locations).
    data_json: JSON string - array of objects with latitude and longitude (or lat/lon, y/x). Optional: label, size.
    title: Map title.
    lat_column: Key for latitude (default: infer from latitude, lat, y).
    lon_column: Key for longitude (default: infer from longitude, lon, lng, x).
    label_column: Optional key for point labels/hover (e.g. name, address, title).
    size_column: Optional numeric key for marker size (e.g. value, count).
    scope: Map extent - 'world' or 'usa'.
    """
    try:
        rows = _parse_data_json(data_json)
    except json.JSONDecodeError as e:
        return StringToolOutput(f"Error: Invalid JSON in data_json: {e}")
    except ValueError as e:
        return StringToolOutput(f"Error: {e}")
    if not rows:
        return StringToolOutput("Error: No data rows to plot on map.")
    try:
        lat_col = lat_column or _infer_lat_lon_columns(rows)[0]
        lon_col = lon_column or _infer_lat_lon_columns(rows)[1]
    except ValueError as e:
        return StringToolOutput(f"Error: {e}")
    try:
        lats, lons, texts, sizes = _prepare_map_points(
            rows, lat_col, lon_col, label_column, size_column
        )
    except ValueError as e:
        return StringToolOutput(f"Error: {e}")
    fig = _build_map_figure(lats, lons, title, scope, texts, sizes)
    buf = io.BytesIO()
    try:
        fig.write_image(buf, format="png", engine="kaleido", scale=1.5)
    except Exception as e:
        return StringToolOutput(
            f"Error generating map image: {e}. Ensure kaleido is installed: pip install kaleido"
        )
    buf.seek(0)
    return _export_chart_markdown(buf.read(), f"Map: {title}")
