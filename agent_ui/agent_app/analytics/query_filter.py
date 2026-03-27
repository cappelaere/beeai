"""
Query-parameter filtering for analytics capture.
"""

from __future__ import annotations

from collections.abc import Iterable

from .constants import MAX_QUERY_VALUE_LENGTH, MAX_QUERY_VALUES_PER_KEY


def _normalize_key(value: str) -> str:
    return (value or "").strip().lower()


def build_filtered_query_params(
    raw_query_params,
    *,
    allowlist: Iterable[str],
    denylist: Iterable[str],
) -> dict[str, str | list[str]]:
    """
    Return query params filtered to allowlist minus denylist.
    """
    allowed = {_normalize_key(x) for x in allowlist if _normalize_key(x)}
    denied = {_normalize_key(x) for x in denylist if _normalize_key(x)}
    effective_allowed = allowed - denied

    if not effective_allowed:
        return {}

    filtered: dict[str, str | list[str]] = {}
    for key in raw_query_params:
        norm_key = _normalize_key(key)
        if norm_key not in effective_allowed:
            continue
        values = raw_query_params.getlist(key)
        cleaned_values = [
            (v or "")[:MAX_QUERY_VALUE_LENGTH]
            for v in values[:MAX_QUERY_VALUES_PER_KEY]
            if v is not None and str(v).strip() != ""
        ]
        if not cleaned_values:
            continue
        filtered[norm_key] = cleaned_values[0] if len(cleaned_values) == 1 else cleaned_values
    return filtered
