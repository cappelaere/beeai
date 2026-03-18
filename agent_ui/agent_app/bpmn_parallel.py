"""
Canonical helper layer for parallel-gateway token and join bookkeeping.

Operates on normalized engine-state fragments only:
  - active_tokens: list of {"current_element_id", "branch_id"} (str | None each)
  - pending_joins: map join_element_id -> PendingJoinInfo.to_dict()

Does NOT perform BPMN traversal, handler invocation, DB access, or Django imports.
Token list order is preserved except where removal or explicit replace changes it.

See docs/architecture/BPMN_ENGINE_REVIEW.md section 7.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class PendingJoinInfo:
    """
    Bookkeeping when multiple branches must arrive at a join gateway.
    Stored under engine_state['pending_joins'][join_element_id] as dict (JSON-serializable).
    """

    fork_id: str
    join_element_id: str
    expected_branch_ids: list[str]
    arrived_branch_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> PendingJoinInfo:
        return cls(
            fork_id=str(d.get("fork_id") or ""),
            join_element_id=str(d.get("join_element_id") or ""),
            expected_branch_ids=list(d.get("expected_branch_ids") or []),
            arrived_branch_ids=list(d.get("arrived_branch_ids") or []),
        )


def ensure_active_tokens(engine_state: dict[str, Any]) -> list[Any]:
    """Ensure engine_state['active_tokens'] is a list; return it."""
    engine_state.setdefault("active_tokens", [])
    if not isinstance(engine_state["active_tokens"], list):
        engine_state["active_tokens"] = []
    return engine_state["active_tokens"]


def ensure_pending_joins(engine_state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    engine_state.setdefault("pending_joins", {})
    pj = engine_state["pending_joins"]
    if not isinstance(pj, dict):
        engine_state["pending_joins"] = {}
    return engine_state["pending_joins"]


def token_dict(
    current_element_id: str | None,
    branch_id: str | None,
) -> dict[str, Any]:
    """Stable token shape aligned with normalize_engine_state (empty string -> None)."""
    ce: str | None
    if current_element_id is None:
        ce = None
    else:
        s = str(current_element_id).strip()
        ce = s if s else None
    br: str | None
    if branch_id is None:
        br = None
    else:
        s = str(branch_id).strip()
        br = s if s else None
    return {"current_element_id": ce, "branch_id": br}


def append_token(
    engine_state: dict[str, Any],
    element_id: str | None,
    branch_id: str | None,
) -> None:
    """Append a token (e.g. after parallel fork). Preserves order of existing tokens."""
    ensure_active_tokens(engine_state).append(token_dict(element_id, branch_id))


def replace_token_at_index(
    engine_state: dict[str, Any],
    index: int,
    element_id: str | None,
    branch_id: str | None,
) -> None:
    """Replace token at index in place; no-op if index out of range."""
    tokens = ensure_active_tokens(engine_state)
    if index < 0 or index >= len(tokens):
        return
    tokens[index] = token_dict(element_id, branch_id)


def remove_token_at_index(engine_state: dict[str, Any], index: int) -> bool:
    """Remove token at index. Returns True if a token was removed."""
    tokens = ensure_active_tokens(engine_state)
    if index < 0 or index >= len(tokens):
        return False
    del tokens[index]
    return True


def replace_token_at_index_with_tokens(
    engine_state: dict[str, Any],
    index: int,
    new_tokens: list[dict[str, Any]],
) -> None:
    """
    Replace the token at index with zero or more tokens (fork split / nested fork).
    Each item should be token-shaped dicts; coerced via token_dict fields.
    """
    tokens = ensure_active_tokens(engine_state)
    if index < 0 or index >= len(tokens):
        return
    normalized = [
        token_dict(t.get("current_element_id"), t.get("branch_id"))
        for t in new_tokens
        if isinstance(t, dict)
    ]
    tokens[index : index + 1] = normalized


def replace_token_by_branch_id(
    engine_state: dict[str, Any],
    branch_id: str,
    element_id: str | None,
    new_branch_id: str | None = None,
) -> bool:
    """
    Update first token whose branch_id matches (empty string matches only "").
    If new_branch_id is not None, set branch_id to that value; else keep existing branch_id.
    """
    tokens = ensure_active_tokens(engine_state)
    bid = branch_id or ""
    for i, t in enumerate(tokens):
        if not isinstance(t, dict):
            continue
        if (t.get("branch_id") or "") != bid:
            continue
        br = new_branch_id if new_branch_id is not None else t.get("branch_id")
        tokens[i] = token_dict(element_id, br)
        return True
    return False


def tokens_at_element(engine_state: dict[str, Any], element_id: str | None) -> list[dict[str, Any]]:
    """All dict tokens whose current_element_id equals element_id."""
    tokens = engine_state.get("active_tokens") or []
    if not isinstance(tokens, list):
        return []
    return [t for t in tokens if isinstance(t, dict) and t.get("current_element_id") == element_id]


def tokens_at_join(engine_state: dict[str, Any], join_element_id: str) -> list[dict[str, Any]]:
    """Tokens waiting at the join gateway (alias for tokens_at_element)."""
    return tokens_at_element(engine_state, join_element_id)


def active_element_ids(engine_state: dict[str, Any]) -> list[str | None]:
    """Per-token current_element_id in list order (one entry per token)."""
    tokens = engine_state.get("active_tokens") or []
    if not isinstance(tokens, list):
        return []
    out: list[str | None] = []
    for t in tokens:
        if isinstance(t, dict):
            out.append(t.get("current_element_id"))
        else:
            out.append(None)
    return out


def active_branch_ids(engine_state: dict[str, Any]) -> list[str]:
    """Per-token branch_id (normalized to '' when missing) in list order."""
    tokens = engine_state.get("active_tokens") or []
    if not isinstance(tokens, list):
        return []
    return [(t.get("branch_id") or "") if isinstance(t, dict) else "" for t in tokens]


def remove_tokens_by_branch_ids(engine_state: dict[str, Any], branch_ids: set[str]) -> int:
    """
    Remove tokens whose branch_id is in branch_ids. Preserves relative order of survivors.

    Non-dict entries in active_tokens are dropped (not kept). That is intentional: normalized
    engine state should only contain token dicts; any other entries are treated as malformed.
    Call normalize_engine_state before resume if payloads may be legacy or dirty.
    """
    tokens = ensure_active_tokens(engine_state)
    keep = [
        t for t in tokens if isinstance(t, dict) and (t.get("branch_id") or "") not in branch_ids
    ]
    removed = len(tokens) - len(keep)
    engine_state["active_tokens"] = keep
    return removed


def register_pending_join(
    engine_state: dict[str, Any],
    join_element_id: str,
    fork_id: str,
    expected_branch_ids: list[str],
) -> None:
    pj = ensure_pending_joins(engine_state)
    pj[join_element_id] = PendingJoinInfo(
        fork_id=fork_id,
        join_element_id=join_element_id,
        expected_branch_ids=list(expected_branch_ids),
        arrived_branch_ids=[],
    ).to_dict()


def get_pending_join(engine_state: dict[str, Any], join_element_id: str) -> dict[str, Any] | None:
    """Shallow copy of pending join entry, or None if missing/invalid."""
    pj = ensure_pending_joins(engine_state)
    raw = pj.get(join_element_id)
    if not raw or not isinstance(raw, dict):
        return None
    return dict(raw)


def is_join_satisfied(engine_state: dict[str, Any], join_element_id: str) -> bool:
    """True if every expected_branch_id has arrived (set inclusion)."""
    pj = ensure_pending_joins(engine_state)
    raw = pj.get(join_element_id)
    if not raw or not isinstance(raw, dict):
        return False
    info = PendingJoinInfo.from_dict(raw)
    exp = set(info.expected_branch_ids)
    arr = set(info.arrived_branch_ids)
    return exp <= arr if exp else False


def clear_pending_join(engine_state: dict[str, Any], join_element_id: str) -> bool:
    """Remove join entry. Returns True if an entry existed."""
    pj = ensure_pending_joins(engine_state)
    if join_element_id not in pj:
        return False
    del pj[join_element_id]
    return True


def mark_branch_arrived_at_join(
    engine_state: dict[str, Any], join_element_id: str, branch_id: str
) -> bool:
    """
    Record that branch_id reached join_element_id (idempotent: duplicate branch_id ignored).
    Empty branch_id is a no-op for arrival recording.
    Returns True if all expected branches have now arrived.
    """
    pj = ensure_pending_joins(engine_state)
    raw = pj.get(join_element_id)
    if not raw or not isinstance(raw, dict):
        return False
    info = PendingJoinInfo.from_dict(raw)
    if branch_id and branch_id not in info.arrived_branch_ids:
        info.arrived_branch_ids.append(branch_id)
    pj[join_element_id] = info.to_dict()
    exp = set(info.expected_branch_ids)
    arr = set(info.arrived_branch_ids)
    return exp <= arr
