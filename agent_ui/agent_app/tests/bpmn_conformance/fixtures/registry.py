"""Registered BPMN conformance fixtures (validation + execution)."""

from __future__ import annotations

from agent_app.tests.bpmn_conformance.schema import (
    ExecutionExpect,
    ExecutionFixture,
    ValidationFixture,
)


def _state():
    return type("S", (), {"workflow_steps": []})()


def _state_x(x: int):
    s = type("S", (), {"workflow_steps": []})()
    s.__dict__["x"] = x
    return s


# --- BPMN dicts (aligned with test_bpmn_engine / test_workflow_context) ---

def _bpmn_linear():
    return {
        "elements": {
            "start": {
                "id": "start",
                "type": "startEvent",
                "outgoing": ["t1"],
                "outgoing_flow_ids": ["s0"],
            },
            "t1": {
                "id": "t1",
                "type": "serviceTask",
                "outgoing": ["t2"],
                "outgoing_flow_ids": ["f1"],
            },
            "t2": {
                "id": "t2",
                "type": "serviceTask",
                "outgoing": ["end"],
                "outgoing_flow_ids": ["f2"],
            },
            "end": {"id": "end", "type": "endEvent", "outgoing": []},
        },
        "sequence_flows": {k: {} for k in ["s0", "f1", "f2"]},
        "ordered_element_ids": ["start", "t1", "t2", "end"],
    }


def _bpmn_exclusive():
    return {
        "elements": {
            "start": {
                "id": "start",
                "type": "startEvent",
                "outgoing": ["task1"],
                "outgoing_flow_ids": ["f0"],
            },
            "task1": {
                "id": "task1",
                "type": "serviceTask",
                "outgoing": ["gw1"],
                "outgoing_flow_ids": ["f1"],
            },
            "gw1": {
                "id": "gw1",
                "type": "exclusiveGateway",
                "incoming": ["task1"],
                "outgoing": ["task_a", "task_b"],
                "outgoing_flow_ids": ["flow_a", "flow_b"],
            },
            "task_a": {
                "id": "task_a",
                "type": "serviceTask",
                "outgoing": ["end"],
                "outgoing_flow_ids": ["f2"],
            },
            "task_b": {
                "id": "task_b",
                "type": "serviceTask",
                "outgoing": ["end"],
                "outgoing_flow_ids": ["f3"],
            },
            "end": {"id": "end", "type": "endEvent", "outgoing": []},
        },
        "sequence_flows": {
            "f0": {},
            "f1": {},
            "flow_a": {"condition": "state.x == 1"},
            "flow_b": {"condition": "state.x == 2"},
            "f2": {},
            "f3": {},
        },
        "ordered_element_ids": ["start", "task1", "gw1", "task_a", "task_b", "end"],
    }


def _bpmn_parallel_fork_two_ends():
    return {
        "elements": {
            "start": {
                "id": "start",
                "type": "startEvent",
                "outgoing": ["task0"],
                "outgoing_flow_ids": ["s0"],
            },
            "task0": {
                "id": "task0",
                "type": "serviceTask",
                "outgoing": ["forkGW"],
                "outgoing_flow_ids": ["t0"],
            },
            "forkGW": {
                "id": "forkGW",
                "type": "parallelGateway",
                "incoming": ["task0"],
                "outgoing": ["taskA", "taskB"],
                "outgoing_flow_ids": ["ffa", "ffb"],
            },
            "taskA": {
                "id": "taskA",
                "type": "serviceTask",
                "outgoing": ["endA"],
                "outgoing_flow_ids": ["fa1"],
            },
            "taskB": {
                "id": "taskB",
                "type": "serviceTask",
                "outgoing": ["endB"],
                "outgoing_flow_ids": ["fb1"],
            },
            "endA": {"id": "endA", "type": "endEvent", "outgoing": []},
            "endB": {"id": "endB", "type": "endEvent", "outgoing": []},
        },
        "sequence_flows": {k: {} for k in ["s0", "t0", "ffa", "ffb", "fa1", "fb1"]},
        "ordered_element_ids": ["start", "task0", "forkGW", "taskA", "taskB", "endA", "endB"],
    }


def _bpmn_fork_join_downstream():
    return {
        "elements": {
            "start": {
                "id": "start",
                "type": "startEvent",
                "outgoing": ["task0"],
                "outgoing_flow_ids": ["s0"],
            },
            "task0": {
                "id": "task0",
                "type": "serviceTask",
                "outgoing": ["forkGW"],
                "outgoing_flow_ids": ["t0"],
            },
            "forkGW": {
                "id": "forkGW",
                "type": "parallelGateway",
                "incoming": ["task0"],
                "outgoing": ["taskA", "taskB"],
                "outgoing_flow_ids": ["ffa", "ffb"],
            },
            "taskA": {
                "id": "taskA",
                "type": "serviceTask",
                "outgoing": ["joinGW"],
                "outgoing_flow_ids": ["ja"],
            },
            "taskB": {
                "id": "taskB",
                "type": "serviceTask",
                "outgoing": ["joinGW"],
                "outgoing_flow_ids": ["jb"],
            },
            "joinGW": {
                "id": "joinGW",
                "type": "parallelGateway",
                "incoming": ["taskA", "taskB"],
                "outgoing": ["taskAfter"],
                "outgoing_flow_ids": ["jc"],
            },
            "taskAfter": {
                "id": "taskAfter",
                "type": "serviceTask",
                "outgoing": ["end"],
                "outgoing_flow_ids": ["jd"],
            },
            "end": {"id": "end", "type": "endEvent", "outgoing": []},
        },
        "sequence_flows": {k: {} for k in ["s0", "t0", "ffa", "ffb", "ja", "jb", "jc", "jd"]},
        "ordered_element_ids": [
            "start",
            "task0",
            "forkGW",
            "taskA",
            "taskB",
            "joinGW",
            "taskAfter",
            "end",
        ],
    }


def _bpmn_parallel_fork_pause_resume():
    return {
        "elements": {
            "start": {
                "id": "start",
                "type": "startEvent",
                "outgoing": ["task0"],
                "outgoing_flow_ids": ["s0"],
            },
            "task0": {
                "id": "task0",
                "type": "serviceTask",
                "outgoing": ["forkGW"],
                "outgoing_flow_ids": ["t0"],
            },
            "forkGW": {
                "id": "forkGW",
                "type": "parallelGateway",
                "incoming": ["task0"],
                "outgoing": ["taskA1", "taskB1"],
                "outgoing_flow_ids": ["ffa", "ffb"],
            },
            "taskA1": {
                "id": "taskA1",
                "type": "serviceTask",
                "outgoing": ["taskA2"],
                "outgoing_flow_ids": ["fa1"],
            },
            "taskA2": {
                "id": "taskA2",
                "type": "serviceTask",
                "outgoing": ["taskA3"],
                "outgoing_flow_ids": ["fa2"],
            },
            "taskA3": {
                "id": "taskA3",
                "type": "serviceTask",
                "outgoing": ["endA"],
                "outgoing_flow_ids": ["fa3"],
            },
            "taskB1": {
                "id": "taskB1",
                "type": "serviceTask",
                "outgoing": ["endB"],
                "outgoing_flow_ids": ["fb1"],
            },
            "endA": {"id": "endA", "type": "endEvent", "outgoing": []},
            "endB": {"id": "endB", "type": "endEvent", "outgoing": []},
        },
        "sequence_flows": {k: {} for k in ["s0", "t0", "ffa", "ffb", "fa1", "fa2", "fa3", "fb1"]},
        "ordered_element_ids": [
            "start",
            "task0",
            "forkGW",
            "taskA1",
            "taskA2",
            "taskA3",
            "taskB1",
            "endA",
            "endB",
        ],
    }


def _bpmn_linear_single_task():
    return {
        "elements": {
            "start": {
                "id": "start",
                "type": "startEvent",
                "outgoing": ["t1"],
                "outgoing_flow_ids": ["s0"],
            },
            "t1": {
                "id": "t1",
                "type": "serviceTask",
                "outgoing": ["end"],
                "outgoing_flow_ids": ["f1"],
            },
            "end": {"id": "end", "type": "endEvent", "outgoing": []},
        },
        "sequence_flows": {k: {} for k in ["s0", "f1"]},
        "ordered_element_ids": ["start", "t1", "end"],
    }


_BIND_LINEAR = {
    "workflow_id": "conf_lin",
    "executor": "conf.Ex",
    "serviceTasks": {
        "t1": {"handler": "h1"},
        "t2": {"handler": "h2"},
    },
}

_BIND_EXCLUSIVE = {
    "workflow_id": "conf_ex",
    "executor": "conf.Ex",
    "serviceTasks": {
        "task1": {"handler": "task1"},
        "task_a": {"handler": "task_a"},
        "task_b": {"handler": "task_b"},
    },
}

_BIND_PAR_TWO = {
    "workflow_id": "conf_p2",
    "executor": "conf.Ex",
    "serviceTasks": {
        "task0": {"handler": "task0"},
        "taskA": {"handler": "task_a"},
        "taskB": {"handler": "task_b"},
    },
}

_BIND_FJ = {
    "workflow_id": "conf_fj",
    "executor": "conf.Ex",
    "serviceTasks": {
        "task0": {"handler": "task0"},
        "taskA": {"handler": "task_a"},
        "taskB": {"handler": "task_b"},
        "taskAfter": {"handler": "task_after"},
    },
}

_BIND_PAUSE = {
    "workflow_id": "conf_pr",
    "executor": "conf.Ex",
    "serviceTasks": {
        "task0": {"handler": "task0"},
        "taskA1": {"handler": "task_a1"},
        "taskA2": {"handler": "task_a2"},
        "taskA3": {"handler": "task_a3"},
        "taskB1": {"handler": "task_b1"},
    },
}

_BIND_SINGLE = {
    "workflow_id": "conf_r",
    "executor": "conf.Ex",
    "serviceTasks": {"t1": {"handler": "h1"}},
}

_TAG_HAPPY = frozenset({"execution_happy"})
_TAG_PAUSE = frozenset({"pause_resume"})
_TAG_FAIL = frozenset({"failure_metadata"})

EXECUTION_FIXTURES: list[ExecutionFixture] = [
    ExecutionFixture(
        id="valid_linear_success",
        bpmn=_bpmn_linear(),
        bindings_raw=_BIND_LINEAR,
        behaviors={"t1": "ok", "t2": "ok"},
        state_factory=_state,
        expect=ExecutionExpect(
            outcome="complete",
            completed_contains=("t1", "t2"),
            completed_ordered_suffix=("t1", "t2"),
        ),
        tags=_TAG_HAPPY,
    ),
    ExecutionFixture(
        id="valid_exclusive_gateway_match",
        bpmn=_bpmn_exclusive(),
        bindings_raw=_BIND_EXCLUSIVE,
        behaviors={"task1": "ok", "task_a": "ok", "task_b": "ok"},
        state_factory=lambda: _state_x(1),
        expect=ExecutionExpect(
            outcome="complete",
            completed_contains=("task1", "task_a"),
            completed_ordered_suffix=("task1", "task_a"),
        ),
        tags=_TAG_HAPPY,
    ),
    ExecutionFixture(
        id="valid_parallel_fork_only",
        bpmn=_bpmn_parallel_fork_two_ends(),
        bindings_raw=_BIND_PAR_TWO,
        behaviors={"task0": "ok", "taskA": "ok", "taskB": "ok"},
        state_factory=_state,
        expect=ExecutionExpect(
            outcome="complete",
            completed_contains=("task0", "taskA", "taskB"),
        ),
        tags=_TAG_HAPPY,
    ),
    ExecutionFixture(
        id="valid_parallel_fork_join",
        bpmn=_bpmn_fork_join_downstream(),
        bindings_raw=_BIND_FJ,
        behaviors={
            "task0": "ok",
            "taskA": "ok",
            "taskB": "ok",
            "taskAfter": "ok",
        },
        state_factory=_state,
        expect=ExecutionExpect(
            outcome="complete",
            completed_contains=("task0", "taskA", "taskB", "taskAfter"),
        ),
        tags=_TAG_HAPPY,
    ),
    ExecutionFixture(
        id="valid_parallel_pause_resume",
        bpmn=_bpmn_parallel_fork_pause_resume(),
        bindings_raw=_BIND_PAUSE,
        behaviors={
            "task0": "ok",
            "taskA1": "ok",
            "taskA2": "pause_human",
            "taskA3": "ok",
            "taskB1": "ok",
        },
        state_factory=_state,
        expect=ExecutionExpect(
            outcome="task_pending",
            completed_contains=("taskA3", "taskB1"),
        ),
        pause_next_step="taskA3",
        pause_at_element_id="taskA2",
        tags=_TAG_PAUSE,
    ),
    ExecutionFixture(
        id="exec_exclusive_no_match",
        bpmn=_bpmn_exclusive(),
        bindings_raw=_BIND_EXCLUSIVE,
        behaviors={"task1": "ok", "task_a": "ok", "task_b": "ok"},
        state_factory=lambda: _state_x(3),
        expect=ExecutionExpect(
            outcome="bpmn_engine_error",
            failure_reason="invalid_gateway",
            failed_node_id="task1",
        ),
        tags=_TAG_FAIL,
    ),
    ExecutionFixture(
        id="exec_parallel_branch_failure",
        bpmn=_bpmn_fork_join_downstream(),
        bindings_raw=_BIND_FJ,
        behaviors={
            "task0": "ok",
            "taskA": "ok",
            "taskB": "fail_runtime",
            "taskAfter": "ok",
        },
        state_factory=_state,
        expect=ExecutionExpect(
            outcome="bpmn_engine_error",
            failure_reason="handler_error",
            failed_node_id="taskB",
            pending_join_ids=["joinGW"],
            min_active_tokens=2,
        ),
        tags=_TAG_FAIL,
    ),
    ExecutionFixture(
        id="exec_cancellation",
        bpmn=_bpmn_fork_join_downstream(),
        bindings_raw=_BIND_FJ,
        behaviors={"task0": "ok", "taskA": "ok", "taskB": "ok", "taskAfter": "ok"},
        state_factory=_state,
        expect=ExecutionExpect(
            outcome="bpmn_engine_error",
            failure_reason="cancelled",
            pending_join_ids=["joinGW"],
            min_active_tokens=2,
        ),
        execution_check_returns=[None, "cancelled"],
        tags=_TAG_FAIL,
    ),
    ExecutionFixture(
        id="exec_timeout",
        bpmn=_bpmn_fork_join_downstream(),
        bindings_raw=_BIND_FJ,
        behaviors={"task0": "ok", "taskA": "ok", "taskB": "ok", "taskAfter": "ok"},
        state_factory=_state,
        expect=ExecutionExpect(
            outcome="bpmn_engine_error",
            failure_reason="timeout",
            pending_join_ids=["joinGW"],
            min_active_tokens=2,
        ),
        execution_check_returns=[None, "timeout"],
        tags=_TAG_FAIL,
    ),
    ExecutionFixture(
        id="exec_retry_then_success",
        bpmn=_bpmn_linear_single_task(),
        bindings_raw=_BIND_SINGLE,
        behaviors={"t1": "retryable_once"},
        state_factory=_state,
        expect=ExecutionExpect(outcome="complete", completed_contains=("t1",)),
        max_task_retries=1,
        tags=_TAG_HAPPY,
    ),
    ExecutionFixture(
        id="exec_retry_exhausted",
        bpmn=_bpmn_linear_single_task(),
        bindings_raw=_BIND_SINGLE,
        behaviors={"t1": "retry_always"},
        state_factory=_state,
        expect=ExecutionExpect(
            outcome="bpmn_engine_error",
            failure_reason="retry_exhausted",
            failed_node_id="t1",
            retry_attempts=1,
        ),
        max_task_retries=0,
        tags=_TAG_FAIL,
    ),
]

VALIDATION_FIXTURES: list[ValidationFixture] = [
    ValidationFixture(
        id="invalid_parallel_mixed_fork_join",
        bpmn={
            "elements": {
                "start": {"type": "startEvent", "outgoing": ["forkGW"]},
                "forkGW": {
                    "type": "parallelGateway",
                    "incoming": ["start"],
                    "outgoing": ["t1", "t2"],
                },
                "t1": {"type": "serviceTask", "outgoing": ["endOnly"]},
                "t2": {"type": "serviceTask", "outgoing": ["joinGW"]},
                "endOnly": {"type": "endEvent", "outgoing": []},
                "joinGW": {
                    "type": "parallelGateway",
                    "incoming": ["t2", "u"],
                    "outgoing": ["e"],
                },
                "u": {"type": "serviceTask", "outgoing": ["joinGW"]},
                "e": {"type": "endEvent", "outgoing": []},
            },
            "sequence_flows": {k: {} for k in ["s", "a", "b", "c", "d"]},
        },
        expect_error_substrings=["mixed", "forkgw"],
    ),
    ValidationFixture(
        id="invalid_nested_parallel",
        bpmn={
            "elements": {
                "start": {"type": "startEvent", "outgoing": ["forkGW"]},
                "forkGW": {
                    "type": "parallelGateway",
                    "incoming": ["start"],
                    "outgoing": ["t1", "t2"],
                },
                "t1": {"type": "serviceTask", "outgoing": ["innerFork"]},
                "innerFork": {
                    "type": "parallelGateway",
                    "incoming": ["t1"],
                    "outgoing": ["a", "b"],
                },
                "a": {"type": "serviceTask", "outgoing": ["joinGW"]},
                "b": {"type": "serviceTask", "outgoing": ["joinGW"]},
                "t2": {"type": "serviceTask", "outgoing": ["joinGW"]},
                "joinGW": {
                    "type": "parallelGateway",
                    "incoming": ["a", "b", "t2"],
                    "outgoing": ["end"],
                },
                "end": {"type": "endEvent", "outgoing": []},
            },
            "sequence_flows": {k: {} for k in ["s", "x", "y", "z", "w", "v", "j"]},
        },
        expect_error_substrings=["nested", "forkgw"],
    ),
    ValidationFixture(
        id="invalid_parallel_pass_through",
        bpmn={
            "elements": {
                "start": {"type": "startEvent", "outgoing": ["gw"]},
                "gw": {
                    "type": "parallelGateway",
                    "incoming": ["start"],
                    "outgoing": ["end"],
                },
                "end": {"type": "endEvent", "outgoing": []},
            },
            "sequence_flows": {k: {} for k in ["s", "e"]},
        },
        expect_error_substrings=["pass_through", "gw"],
    ),
]

EXECUTION_FIXTURES_BY_ID = {f.id: f for f in EXECUTION_FIXTURES}
VALIDATION_FIXTURES_BY_ID = {f.id: f for f in VALIDATION_FIXTURES}

PAUSE_RESUME_FIXTURES = [f for f in EXECUTION_FIXTURES if "pause_resume" in f.tags]

FAILURE_METADATA_FIXTURE_IDS = frozenset(f.id for f in EXECUTION_FIXTURES if "failure_metadata" in f.tags)

EXECUTION_COMPLETE_FIXTURES = [
    f for f in EXECUTION_FIXTURES if f.expect.outcome == "complete" and "pause_resume" not in f.tags
]


def execution_fixture_by_id(fid: str) -> ExecutionFixture:
    return EXECUTION_FIXTURES_BY_ID[fid]


def validation_fixture_by_id(fid: str) -> ValidationFixture:
    return VALIDATION_FIXTURES_BY_ID[fid]
