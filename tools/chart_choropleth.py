"""
Choropleth map tool for agent use.
Shows density or counts by region (e.g. US state). Uses Plotly Choropleth with
built-in USA-states geometry. Same cache+URL pattern as chart_map for chat display.
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

# US state and territory name -> 2-letter abbreviation (Plotly USA-states)
USA_STATE_ABBR = {
    "alabama": "AL",
    "alaska": "AK",
    "arizona": "AZ",
    "arkansas": "AR",
    "california": "CA",
    "colorado": "CO",
    "connecticut": "CT",
    "delaware": "DE",
    "district of columbia": "DC",
    "dc": "DC",
    "florida": "FL",
    "georgia": "GA",
    "hawaii": "HI",
    "idaho": "ID",
    "illinois": "IL",
    "indiana": "IN",
    "iowa": "IA",
    "kansas": "KS",
    "kentucky": "KY",
    "louisiana": "LA",
    "maine": "ME",
    "maryland": "MD",
    "massachusetts": "MA",
    "michigan": "MI",
    "minnesota": "MN",
    "mississippi": "MS",
    "missouri": "MO",
    "montana": "MT",
    "nebraska": "NE",
    "nevada": "NV",
    "new hampshire": "NH",
    "new jersey": "NJ",
    "new mexico": "NM",
    "new york": "NY",
    "north carolina": "NC",
    "north dakota": "ND",
    "ohio": "OH",
    "oklahoma": "OK",
    "oregon": "OR",
    "pennsylvania": "PA",
    "rhode island": "RI",
    "south carolina": "SC",
    "south dakota": "SD",
    "tennessee": "TN",
    "texas": "TX",
    "utah": "UT",
    "vermont": "VT",
    "virginia": "VA",
    "washington": "WA",
    "west virginia": "WV",
    "wisconsin": "WI",
    "wyoming": "WY",
    "puerto rico": "PR",
    "guam": "GU",
    "virgin islands": "VI",
    "american samoa": "AS",
    "northern mariana islands": "MP",
}


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


def _state_to_abbr(location: str) -> str | None:
    """Convert state name or existing abbreviation to 2-letter code."""
    if not location or not isinstance(location, str):
        return None
    s = location.strip()
    if len(s) == 2 and s.upper() in USA_STATE_ABBR.values():
        return s.upper()
    key = s.lower().strip()
    return USA_STATE_ABBR.get(key)


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


def _validate_choropleth_input(
    data_json: str,
    location_column: str,
    value_column: str,
    locationmode: str,
) -> tuple[list[dict], str, str, str] | tuple[None, StringToolOutput]:
    """Validate and parse choropleth inputs. Returns (rows, loc_col, val_col, mode) or (None, error)."""
    try:
        rows = _parse_data_json(data_json)
    except json.JSONDecodeError as e:
        return (None, StringToolOutput(f"Error: Invalid JSON in data_json: {e}"))
    except ValueError as e:
        return (None, StringToolOutput(f"Error: {e}"))
    if not rows:
        return (None, StringToolOutput("Error: No data rows for choropleth."))
    loc_col = location_column or "state"
    val_col = value_column or "count"
    if loc_col not in rows[0]:
        return (
            None,
            StringToolOutput(
                f"Error: location_column '{loc_col}' not found in data. Keys: {list(rows[0].keys())}"
            ),
        )
    if val_col not in rows[0]:
        return (
            None,
            StringToolOutput(
                f"Error: value_column '{val_col}' not found in data. Keys: {list(rows[0].keys())}"
            ),
        )
    mode = (locationmode or "USA-states").strip().lower()
    if mode not in ("usa-states", "country names"):
        mode = "usa-states"
    return (rows, loc_col, val_col, mode)


def _build_usa_states_figure(
    rows: list[dict], loc_col: str, val_col: str, title: str, value_column: str
) -> tuple[go.Figure | None, str | None]:
    """Build USA-states choropleth figure. Returns (fig, None) or (None, error_msg)."""
    state_to_count: dict[str, float] = {}
    for r in rows:
        loc = r.get(loc_col)
        abbr = _state_to_abbr(str(loc)) if loc is not None else None
        if abbr:
            state_to_count[abbr] = state_to_count.get(abbr, 0.0) + _to_number(r.get(val_col))
    locations = list(state_to_count.keys())
    if not locations:
        return (
            None,
            "No valid US state names or codes found in location_column. "
            "Use full state names (e.g. Kansas) or 2-letter codes (e.g. KS).",
        )
    z_vals = [state_to_count[abbr] for abbr in locations]
    fig = go.Figure(
        go.Choropleth(
            locationmode="USA-states",
            locations=locations,
            z=z_vals,
            colorscale="Blues",
            colorbar={"title": value_column or "Value"},
            autocolorscale=False,
        )
    )
    fig.update_layout(
        title=title,
        geo=dict(
            scope="usa",
            showlakes=True,
            lakecolor="rgb(204, 224, 255)",
        ),
        margin={"t": 50, "b": 20, "l": 20, "r": 20},
        height=400,
    )
    return (fig, None)


def _build_country_figure(
    rows: list[dict], loc_col: str, val_col: str, title: str, value_column: str
) -> tuple[go.Figure | None, str | None]:
    """Build country-names choropleth figure. Returns (fig, None) or (None, error_msg)."""
    locations = [str(r.get(loc_col, "")).strip() for r in rows]
    z_vals = [_to_number(r.get(val_col)) for r in rows]
    if not any(locations):
        return (None, "No valid locations in data for country names mode.")
    fig = go.Figure(
        go.Choropleth(
            locationmode="country names",
            locations=locations,
            z=z_vals,
            colorscale="Blues",
            colorbar={"title": value_column or "Value"},
            autocolorscale=False,
        )
    )
    fig.update_layout(
        title=title,
        geo=dict(showframe=False, showcoastlines=True),
        margin={"t": 50, "b": 20, "l": 20, "r": 20},
        height=400,
    )
    return (fig, None)


@tool
def chart_choropleth(
    data_json: str,
    title: str,
    location_column: str = "state",
    value_column: str = "count",
    locationmode: str = "USA-states",
) -> StringToolOutput:
    """
    Use for density or counts by region (e.g. property count by state). Do not use chart_map for density.
    Plot a choropleth map showing a value (e.g. property count or density) by region. Use when the user asks for a choropleth map, density by location/state, or property counts by state.
    data_json: JSON string - array of objects with a region identifier (e.g. state name or code) and a numeric value (e.g. count).
    title: Map title (e.g. 'Property density by state').
    location_column: Key for region (default 'state'). For USA-states, use full state name (e.g. Kansas) or 2-letter code (e.g. KS).
    value_column: Key for the numeric value to color by (default 'count').
    locationmode: 'USA-states' (default) for US state-level map, or 'country names' for world by country.
    """
    validated = _validate_choropleth_input(data_json, location_column, value_column, locationmode)
    if validated[0] is None:
        return validated[1]
    rows, loc_col, val_col, mode = validated

    if mode == "usa-states":
        fig, err = _build_usa_states_figure(rows, loc_col, val_col, title, value_column)
    else:
        fig, err = _build_country_figure(rows, loc_col, val_col, title, value_column)
    if err:
        return StringToolOutput(f"Error: {err}")

    buf = io.BytesIO()
    try:
        fig.write_image(buf, format="png", engine="kaleido", scale=1.5)
    except Exception as e:
        return StringToolOutput(
            f"Error generating choropleth image: {e}. Ensure kaleido is installed: pip install kaleido"
        )
    buf.seek(0)
    return _export_chart_markdown(buf.read(), f"Choropleth: {title}")
