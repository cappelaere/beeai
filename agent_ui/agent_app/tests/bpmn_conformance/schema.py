"""Fixture dataclasses for BPMN conformance suite."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ValidationFixture:
    """Save-time validation only (diagram must not run)."""

    id: str
    bpmn: dict[str, Any]
    expect_error_substrings: list[str]
    bindings: dict[str, Any] | None = None


@dataclass
class ExecutionExpect:
    outcome: str  # "complete" | "bpmn_engine_error" | "task_pending"
    failure_reason: str | None = None
    failed_node_id: str | None = None
    completed_contains: tuple[str, ...] = ()
    completed_ordered_suffix: tuple[str, ...] | None = None
    pending_join_ids: list[str] | None = None
    min_active_tokens: int | None = None
    retry_attempts: int | None = None
    bpmn_max_task_retries: int | None = None


@dataclass
class ExecutionFixture:
    """Runnable BPMN + bindings + dynamic handler behaviors."""

    id: str
    bpmn: dict[str, Any]
    bindings_raw: dict[str, Any]
    """
    task_element_id -> behavior key:
      ok, retryable_once, retry_always, fail_runtime, pause_human (needs next_step in extra)
    """
    behaviors: dict[str, str]
    state_factory: Callable[[], Any]
    expect: ExecutionExpect
    max_task_retries: int = 0
    execution_check_returns: list[str | None] = field(default_factory=list)
    """Per top-of-loop execution_check call: None continue, cancelled, timeout."""
    pause_next_step: str | None = None
    """When outcome task_pending, expected next_step for phase 2."""
    pause_at_element_id: str | None = None
    """Element id that raises TaskPendingException (must match pause_human branch)."""
    tags: frozenset[str] = field(default_factory=frozenset)
    """e.g. failure_metadata, pause_resume, execution_happy"""
