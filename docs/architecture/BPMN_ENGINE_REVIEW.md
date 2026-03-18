# BPMN Engine – Solution Architecture Review

**Reviewer:** Senior solution architect (design + implementation)  
**Scope:** BPMN-driven workflow execution (bpmn_engine, workflow_context, workflow_runner, consumers)

See also: [BPMN Engine V2 Design Spec](./BPMN_V2_PLAN.md)

**Conformance-style fixtures:** A maintained corpus of validation and execution scenarios lives under `agent_ui/agent_app/tests/bpmn_conformance/` (Python BPMN dicts, harness, and `test_bpmn_conformance`). Use it when adding parallel/gateway behavior to lock in expected `validate_bpmn_for_save` messages and engine outcomes without duplicating large BPMN blobs in ad-hoc tests. Details: [bpmn_conformance/README.md](../../agent_ui/agent_app/tests/bpmn_conformance/README.md).

**Operator-facing run diagnostics (PAR-013):** Run detail and task detail surface a BPMN-specific timeline, join/retry/cancel/timeout context, and optional raw progress for support. Interpretation guide: [BPMN run operators](../operations/BPMN_RUN_OPERATORS.md).

### Boundary timer and error events (PAR-014)

v1 supports **interrupting** boundary **timer** and **error** events only (`cancelActivity` true or omitted; `false` is rejected at save).

| Rule | v1 |
|------|-----|
| Event types | `boundaryTimerEvent` (with `timeDuration`), `boundaryErrorEvent` |
| Attachment | `serviceTask`, `userTask`, `task`, `scriptTask` |
| Outgoing | Exactly one sequence flow from the boundary to the alternate path |
| Multiple boundaries | At most one timer and one error per attached task |
| Timer semantics | On first scheduling of task `T`, a monotonic deadline is set; if the handler is not invoked before the duration elapses, the token follows the timer boundary (task `T` is not appended to `workflow_steps`). |
| Error semantics | Handlers may raise `BpmnModeledBoundaryError` to take the error boundary; same routing as timer (no normal completion step for `T`). |
| Global run timeout | If `execution_check` returns `timeout`, there is **exactly one** active token, and that token sits on a task with an interrupting timer boundary (parseable duration), the engine routes along that boundary with reason `run_timeout_routed_to_timer_boundary` instead of failing the run. If multiple tokens exist, timeout behavior is unchanged (run fails). |
| Re-entry after boundary | On timer boundary exit from task *T*, *T*’s `task_entry_monotonic` entry is cleared and *T*’s `(branch_id, task_id)` key is queued. The **next** time that exact key is scheduled (after any intermediate tasks on the alternate path), one timer-deadline check is skipped so the handler can run; then the deadline anchor is refreshed. This avoids infinite timer loops when the alternate path returns to *T*. |

Persisted on `engine_state`: `boundary_transitions` (list), `last_boundary_transition` (dict), `task_entry_monotonic` (per-branch task entry times for deadline checks).

### Intermediate timer and message catch (PAR-015)

v1 supports **`intermediateCatchEvent`** with **timer** (`timeDuration` inside `timerEventDefinition`) or **message** (`messageEventDefinition`; correlation key = `messageRef` id, or element `name`, or element id).

| Rule | v1 |
|------|-----|
| Outgoing | Exactly one sequence flow after the catch |
| Timer | Wall-clock deadline = first land time + duration; **no background scheduler** — each **explicit resume** re-evaluates `time.time()` vs deadline; if elapsed, token advances past the catch. |
| Message | Run status `waiting_for_bpmn_message`. Caller adds the key to `engine_state.satisfied_intermediate_messages` (e.g. POST JSON `satisfy_intermediate_message` on resume, or PATCH progress) then resumes. Key is consumed when advancing past that catch. |
| Parallel tokens | **Not supported:** if more than one active token exists when the engine would wait on an intermediate catch, the run fails with `intermediate_catch_parallel_not_supported`. |
| Runner | `BpmnIntermediateWaitException` → `waiting_for_bpmn_timer` / `waiting_for_bpmn_message`; resume via `resume-bpmn` (same as human pause for `next_step` + `engine_state`). |

Persisted: `bpmn_event_wait` (wait metadata), `satisfied_intermediate_messages` (list of keys), `intermediate_catch_transitions` (audit list after advancing).

### Embedded subprocess (PAR-016, phase 1)

v1 supports a single level of **embedded** `subProcess` (no nested subprocess inside subprocess). Internal graph uses the same executable subset as the parent process. **callActivity** is out of scope (phase 2).

| Rule | v1 |
|------|-----|
| Boundary | Exactly one incoming sequence flow into the subprocess from the parent scope; exactly one outgoing from the subprocess to the parent continuation. |
| Internal | Exactly one internal `startEvent`; at least one internal `endEvent`. |
| Exit | When a token reaches an internal `endEvent`, it is removed; when no token remains inside that subprocess id, one token is placed on the parent continuation (after traversing from the subprocess shell’s single outgoing). Parallel branches inside the subprocess complete independently until the last branch ends, then exit once. |
| Parallel inside SP | A parallel fork inside the subprocess may not connect a branch **directly** to an internal `endEvent` (join first). |
| State | `subprocess_stack` records entry (subprocess id, name, `parent_branch_id` for parent parallel correlation). `subprocess_transitions` audits `entered` / `completed`. Both are normalized on load. |

Rejected at save: nested embedded subprocess, event subprocess, callActivity, and other unsupported shapes (see `validate_bpmn_embedded_subprocesses`).

---

## 1. Design strengths

- **Single source of truth**  
  Execution order is taken from the BPMN diagram (sequence flow), not from Python `_register_steps()`. Adding or reordering tasks in the diagram is enough for the engine; no need to touch step registration in code. This matches the stated goal and reduces sync errors.

- **BPMN-only execution**  
  Execution is BPMN-only: workflows must provide `workflow.bpmn`, `bpmn-bindings.yaml`, and a state class to run. `can_run_with_bpmn_engine(workflow_id)` indicates whether a workflow is runnable; the runner fails with a clear error if not. There is no legacy `executor.run()` path.

- **Reuse of existing building blocks**  
  The engine reuses `workflow_context` (BPMN parsing, `get_workflow_context`, bindings normalization), `get_first_task_id` / `get_next_task_id`, and the existing runner/consumer lifecycle (pause/resume, progress_data, WebSocket). That keeps the change surface small and consistent with the rest of the system.

- **Pause/resume aligned with diagram**  
  On `TaskPendingException`, the engine stores the next BPMN task id (`_bpmn_next_step`) and the runner passes it into `_handle_workflow_paused` as `next_step_override`. Resume then continues from that task via the same BPMN traversal. Human-task flows stay diagram-driven.

- **Separation of concerns**  
  - **workflow_context:** BPMN parsing and navigation (pure, no I/O in navigation).  
  - **bpmn_engine:** Orchestration (resolve handler → call handler → advance via BPMN).  
  - **workflow_runner / consumers:** Integration (when to use engine, state creation, DB/WS updates).  
  This is easy to test and evolve.

### Current scope (v1)

- **Linear / single-path execution**  
  v1 supports one outgoing sequence flow per element. The engine follows a single path through the diagram.

- **Gateways only partially supported**  
  Handler-return overrides can influence the next step in some code paths, but there is **no full BPMN semantics** for exclusive gateway conditions, parallel gateway fork/join, or event handling. Multiple outgoing flows from a gateway are not evaluated; execution may stop or use a handler return if implemented.

### Engine state and persistence

- **Separation from workflow state**  
  **Engine state** (token position, completed nodes, failed nodes) is separate from **workflow business state** (user fields on the state class). Engine state is not part of the Pydantic model; it lives in `state.__dict__["_bpmn_engine_state"]` and is copied to `progress_data["engine_state"]` by the runner/consumer so resume can restore it.

- **Token shape (v2+)**  
  Execution may use one or more tokens. Each normalized token is exactly: `{"current_element_id": str | None, "branch_id": str | None}`. Extra keys on persisted tokens are stripped on normalize. `branch_id` is used for parallel branches.

- **What is persisted**  
  The runner/consumer persist in `progress_data`: `engine_state` (the full engine state dict), `state_data` (workflow state, e.g. `model_dump()`), and `next_step` (BPMN task id for resume). On resume, `bpmn_engine.normalize_engine_state()` is applied to `progress_data["engine_state"]` before attaching to state so all keys match the contract below.

- **Engine-state persistence contract (normalized shape)**  
  `normalize_engine_state()` in `bpmn_engine.py` is the single source of truth. Returned dict always includes:

  | Key | Type | Meaning |
  |-----|------|---------|
  | `engine_version` | `str` | e.g. `"2"`; set when missing on load |
  | `active_tokens` | `list[dict]` | Each item: `current_element_id`, `branch_id` (both str or None) |
  | `completed_node_ids` | `list` | Completed BPMN element ids (non-lists coerced to `[]`) |
  | `current_node_ids` | `list` | Current positions (legacy single-token: derive token from `[0]` if `active_tokens` empty) |
  | `failed_node_ids` | `list` | Historical failures |
  | `pending_joins` | `dict` | Map **join_element_id** → join bookkeeping dict (see below); `{}` if missing or invalid |
  | `failed_node_id` | `str \| None` | Last failure element (empty string → None) |
  | `failure_reason` | `str \| None` | Machine-oriented reason |
  | `last_successful_node_id` | `str \| None` | From completed list when failure recorded |
  | `condition_failure_metadata` | `dict` | `{}` if missing or not a dict |
  | `task_retry_counts` | `dict` | PAR-011: map **`branchKey|nodeId`** → failure count for retryable errors |
  | `last_retryable_error` | `dict \| null` | PAR-011: last transient failure metadata while retrying |
  | `task_entry_monotonic` | `dict` | PAR-014: keys `branchId|taskId` → monotonic time when task was first scheduled |
  | `boundary_transitions` | `list[dict]` | PAR-014: each: `boundary_event_id`, `boundary_type`, `attached_to_task_id`, `reason`, `at` |
  | `last_boundary_transition` | `dict \| null` | PAR-014: copy of last entry appended to `boundary_transitions` |
  | `bpmn_event_wait` | `dict` | PAR-015: `waiting_event_id`, `waiting_event_type` (`timer` \| `message`), optional `timer_deadline_ts` / `timer_deadline_iso`, `message_key`, `branch_id` |
  | `satisfied_intermediate_messages` | `list[str]` | PAR-015: message keys satisfied before resume |
  | `intermediate_catch_transitions` | `list[dict]` | PAR-015: `event_id`, `catch_type`, `at` after passing a catch |
  | `subprocess_stack` | `list[dict]` | PAR-016: `subprocess_id`, `name`, `entered_at`, `parent_branch_id` |
  | `subprocess_transitions` | `list[dict]` | PAR-016: `subprocess_id`, `action` (`entered` \| `completed`), `at` |

  **`pending_joins[join_id]`** (values only for valid dict entries; non-dict values skipped):

  - `fork_id`, `join_element_id` (strings)
  - `expected_branch_ids`, `arrived_branch_ids` (lists of strings; unsafe list payloads coerced via `PendingJoinInfo.from_dict`)

  **Normalization rules**

  - Legacy payload with only `completed_node_ids` / `current_node_ids`: yields one default token from `current_node_ids[0]`, `pending_joins` `{}`, default failure fields.
  - Missing `engine_version` → `"2"` (`BPMN_ENGINE_VERSION`).
  - `active_tokens` missing, not a list, or all entries non-dicts: replaced by a single token from `current_node_ids[0]` (or `None`).
  - `pending_joins` not a dict → `{}`. Partial per-join dicts → filled defaults; non-dict values for a join key → entry omitted.

  **progress_data (top-level)**  
  Same failure and node list fields may also appear at top level for UI; canonical execution source remains `engine_state` after normalize.

  **`current_node_ids` (multi-node):** Always a **list** of BPMN element ids (0..N). For run detail and WebSocket progress, values are derived via `current_node_ids_for_progress(engine_state)` in [bpmn_engine.py](../../agent_ui/agent_app/bpmn_engine.py): prefers each `active_tokens[].current_element_id` in order, else `engine_state.current_node_ids`. Single-token runs use a one-element list.   **`next_step`** on pause is still the BPMN task id to resume from (may differ from active diagram nodes when parallel branches exist).

  **Resume with multiple tokens:** When `progress_data["engine_state"]["active_tokens"]` has more than one entry, `run_bpmn_workflow(..., start_from_task_id=next_step)` **must not** collapse tokens to a single position. The engine restores the full token list and continues scheduling by token order. Single-token resume behavior is unchanged.

  **Compatibility**

  - Tolerate older payloads missing `pending_joins`, `branch_id`, or failure keys.
  - Bump `engine_version` only for incompatible schema changes; migrate in normalize or reject resume explicitly.

---

## 2. Gaps and limitations

### Parallel gateway save-time contract (pre-runtime)

Workflow Studio save runs `validate_parallel_gateway_topology()` in [workflow_context.py](../../agent_ui/agent_app/workflow_context.py) via `validate_bpmn_for_save()`. Invalid BPMN is blocked before files are written (API returns 400). This is **stricter** than “any wired gateway” so diagrams match a future deterministic parallel runtime.

| Role | Allowed topology |
|------|------------------|
| **Fork** | Exactly **one** incoming sequence flow and **at least two** outgoing. |
| **Join** | **At least two** incoming and **exactly one** outgoing. |

Rejected examples: no incoming or no outgoing; one-in-one-out pass-through; multiple incoming **and** multiple outgoing on the same gateway (split into separate join + fork). Error strings include the gateway id and a `shape=...` hint plus a fix suggestion.

### Parallel fork runtime (PAR-005)

- **Fork:** When a service task completes and its single outgoing flow targets a **parallel fork** (one incoming, two or more outgoing on `parallelGateway`), the engine creates one **token per outgoing flow** in **`resolve_outgoing_flows` order** (BPMN outgoing order). `branch_id` is `{fork_gateway_id}:{flow_id}`. The fork gateway id is appended to `completed_node_ids`. Branches that reach `endEvent` immediately consume no token.
- **Scheduling:** Among `active_tokens`, the engine runs the **first** token (by list index) whose `current_element_id` is a bound service task. That implies **depth-first on the first branch** until it hits end or pause, then the second branch’s work runs, etc. (deterministic, not round-robin between branches each step).
- **End:** Completing a task whose successor is `endEvent` removes **only** that token. The run completes when `active_tokens` is empty.
- **Pause:** `TaskPendingException` updates **only** the pausing token’s position and `next_step`; sibling tokens are unchanged.
- **Join (PAR-006 / PAR-009):** **`join_gateway_for_parallel_fork(bpmn, fork_id)`** statically correlates each fork outgoing to **endEvent** or to a **parallel join**. If **all** branches reach the **same** join, the engine registers **`pending_joins[join_id]`** with **`expected_branch_ids`** = all `{fork_id}:{flow_id}` values. **PAR-009** broadens correlation beyond a single linear hop: branches may chain **multiple tasks** and other **single-outgoing** nodes before the join; **`exclusiveGateway`** is allowed only when **every** outgoing path reaches the **same** join (or all paths end — then treated like end for that subgraph). Rejected: **nested parallel fork** on a branch, **different joins** per fork outgoing, **mixed** end and join across fork outgoings, exclusive paths where **some** end and **some** hit the join, or **non-exclusive** multi-out gateways on the branch. If no branch reaches a join (all to **endEvent**), behavior is **fork-only** (no **`pending_joins`**). Save-time **`validate_parallel_fork_join_correlation`** (inside **`validate_bpmn_for_save`**) surfaces correlation errors before deploy. Runtime join parking/merge unchanged once **`join_id`** is known.

Traversal still surfaces joins via **`Workflow.PARALLEL_JOIN:{id}`** from **`traverse_until_executable`**.

Helpers: **`join_gateway_for_parallel_fork`**, **`first_executable_after_join`**, **`is_parallel_fork_gateway`**, **`parallel_fork_branch_entries`**, **`resolve_position_after_service_task`**, **`next_step_after_task_completion`**; join bookkeeping in [bpmn_parallel.py](../../agent_ui/agent_app/bpmn_parallel.py).

### Runner integration workflow **`runner_parallel_fj_test`** (PAR-007)

Hidden catalog workflow [workflows/runner_parallel_fj_test/](../../workflows/runner_parallel_fj_test/) drives **`TransactionTestCase`** tests in **`RunnerParallelFjIntegrationTests`** ([test_workflow_runner_integration.py](../../agent_ui/agent_app/tests/test_workflow_runner_integration.py)): full-stack **`execute_workflow_run`** / **`resume_bpmn_after_pause`** with persisted **`WorkflowRun.progress_data`**—fork/join completion, pause on branch B before join (multi-token **`current_node_ids`**), resume after clearing the pause flag, synthetic mid-join resume (one token at join, one at **taskB**), and branch failure with **`pending_joins`** still keyed by the join. On **`TaskPendingException`**, when the next BPMN hop after the task is the join, **`next_step_after_task_completion`** is **`None`**; the engine must keep that branch’s token on the **pausing task** (not **`None`**) so **`next_step`** resume matches a valid token.

### Run UI and WebSocket progress (PAR-008)

[`_build_progress_info`](../../agent_ui/agent_app/views/workflows.py) adds join-aware display fields from **`engine_state`** (**`pending_joins`**, **`active_tokens`**): **`waiting_join_ids`**, **`pending_join_count`**, **`active_branch_ids`**, **`nodes_waiting_at_join`**, **`parallel_state_summary`**, and **`show_parallel_panel`** (false for linear runs so the UI stays quiet). Run detail / task waiting banners render the green parallel panel only when **`show_parallel_panel`**. Failed runs with open joins get **`parallel_failure_context`** and related keys from **`WorkflowRun.bpmn_failure_summary()`**. Live execution uses **`workflow-execution.js`**: status badge text **`Running · at join`** (with join branch counts in **`title`**) when **`engine_state.pending_joins`** is non-empty, **`Running · merged path`** after the last join clears, without repeated notifications for ordinary parallel steps.

### Other limitations

- **Single-path helpers**  
  `get_next_task_id` and legacy `_follow_single_path` remain single-path oriented. Runtime execution uses `run_bpmn_workflow` multi-token logic and `resolve_position_after_service_task` for post-task routing.

- **Exclusive gateways**  
  Supported via condition evaluation on outgoing flows. Parallel **join** on a branch (before the common join) is not supported for fork–join pairing.

- **State class convention**  
  Initial state is built by importing `workflows.<id>.workflow` and instantiating `StateClass(**input_data)`. That assumes:
  - A Pydantic (or compatible) state class with a name ending in `State`.
  - Constructor args that match workflow inputs (e.g. `start_date`, `end_date`).
  - `workflow_steps` on state (or it’s created by the engine).  
  Workflows that don’t follow this (e.g. DAP report) correctly fall back to `executor.run()` but are undocumented; a short “BPMN-engine-ready workflow contract” in the dev guide would help.

- **Handler return value ignored**  
  Handlers can return a next step name; the engine ignores it and always uses `get_next_task_id(bpmn, current)`. That’s correct for “diagram is source of truth,” but it means you cannot implement conditional next steps in code without extending the engine (e.g. optional override when handler returns a non-empty string).

- **Per-branch cancellation / per-task timeout**  
  Workflow-level cooperative cancellation and optional run timeout are implemented (see §8). Per-branch cancellation and per-task timeouts remain out of scope.

---

## 8. Workflow-level cancellation and timeout (PAR-010)

### Semantics

| Topic | Behavior |
|-------|----------|
| **Cancellation** | `WorkflowRun.status == "cancelled"` (WebSocket `cancel`, API, etc.). The BPMN engine calls an async **`execution_check`** at the **start of each token iteration** (before the next runnable service task). **Cooperative only**: a long-running handler is not interrupted mid-call. |
| **Timeout** | Optional **`input_data["execution_timeout_seconds"]`** (positive integer). **Wall-clock deadline** = **`WorkflowRun.created_at` + timeout** (stable across pause/resume). Checked only while the engine loop is active; if the deadline passed during a pause, timeout fires when execution resumes. |
| **vs handler failure** | Cancel/timeout set `failure_reason` to **`cancelled`** or **`timeout`** with no handler exception. Handler errors remain **`handler_error`** (and gateway/join errors keep their existing reasons). |
| **Resume after cancel** | **`resume_bpmn_after_pause`** refuses to run if the run is already **`cancelled`**. |

### Persisted `progress_data` on cancel/timeout

- **`failure_reason`**: `cancelled` \| `timeout`
- **`failed_node_id`**: usually `null` (abort at loop boundary)
- **`last_successful_node_id`**, **`completed_node_ids`**: from engine state
- **`engine_state`**: full snapshot including **`active_tokens`** and **`pending_joins`** (unchanged for diagnostics)
- **`cancelled_at`**: ISO-8601 when cancelled (top-level and/or in `condition_failure_metadata`)
- **`timeout_seconds`**, **`timed_out_at`**: when timed out

### Status

| Outcome | `WorkflowRun.status` |
|---------|----------------------|
| User cancel (engine observes DB) | **`cancelled`** |
| Timeout | **`failed`** |
| Handler / gateway / join error | **`failed`** (existing) |

---

## 9. Task retries (PAR-011)

| Topic | Behavior |
|-------|----------|
| **Retryable** | Handlers raise **`BpmnRetryableTaskError`** (`task_service.py`). Any other exception is non-retryable **`handler_error`**. |
| **Policy** | **`input_data["bpmn_max_task_retries"]`** — non-negative int, default **0**. **N** = max **additional** invocations after the first failure on the same **`(branch_id, node_id)`** slot (N=0: first retryable failure exhausts; N=2: up to 3 total calls). |
| **Execution** | Immediate re-invocation on the next engine loop iteration; token stays on the same task. |
| **State** | **`engine_state["task_retry_counts"]`**: map key **`"{branch_id}|{node_id}"`** (linear: **`_|nodeId`**). **`last_retryable_error`**: last failure metadata. Cleared for that slot on successful task completion. |
| **Exhaustion** | **`failure_reason="retry_exhausted"`**; metadata includes **`retry_attempts`**, **`bpmn_max_task_retries`**, **`branch_id`**, **`last_error`**. |
| **Pause/resume** | Retry counters persist in **`engine_state`** on pause. Resume continues with same counts. |
| **Cancel/timeout** | **`execution_check`** runs before each loop iteration (including between retries). |

---

## 3. Risks and robustness

- **Failure after partial execution**  
  If a handler raises an exception (other than `TaskPendingException`), the run is marked failed and progress is not persisted. That’s acceptable for “fail fast,” but you might later want:
  - `failed_node_id` set to the current task id (you already have the field in progress_data).
  - Optional “retry from last successful task” using the same BPMN resume mechanism.

- **State creation failure**  
  If `create_initial_state_from_inputs` raises (e.g. wrong or missing input keys), the exception propagates and the run is marked failed. There is no fallback to `executor.run()` in that case. That’s correct (inputs are invalid), but the error_message could be explicit, e.g. “BPMN engine: failed to create initial state: …”, so logs and UI are clearer.

- **Duplicate context loading**  
  `can_run_with_bpmn_engine` and `_get_bindings_and_bpmn` both call `get_workflow_context(workflow_id)`. For a single run you may call the former once and the latter once, so context is loaded twice. Minor cost; could be optimized later by caching per run or by having a single “get context and decide execution mode” helper.

- **Resume: state reconstruction**  
  On resume, state is rebuilt from `progress_data["state_data"]` (e.g. `model_dump()`). Attributes that are not on the Pydantic model (e.g. `_bpmn_next_step`) are not persisted. That’s fine because the next step is stored in `progress_data["next_step"]` and the engine uses `start_from_task_id` on resume. No issue here.

- **Thread/concurrency safety**  
  The engine is async and does not share mutable state across runs. Each run has its own executor_instance and state. Safe for concurrent runs of the same or different workflows.

---

## 4. Recommendations

**High value, low effort**

1. **Set `failed_node_id` on handler exception**  
   In the runner, when the BPMN path raises (and it’s not `TaskPendingException`), call `_update_workflow_progress_sync(run_id, {"failed_node_id": current_task_id})` before marking the run failed, so the UI can highlight the failing task.

2. **Document the “BPMN-engine-ready” contract**  
   In the developer guide or workflow docs: workflow must have a state class in `workflow.py`, BPMN with at least one service task, and bindings; state constructor must accept workflow inputs; handlers must be methods on the executor and take `(self, state)`.

3. **Clarify errors from state creation**  
   When catching exceptions in `execute_workflow_run` that originate from `create_initial_state_from_inputs` or from the BPMN engine, set `error_message` to something like “BPMN engine: …” so support can tell diagram-driven runs from legacy runs.

**Medium term**

4. **Support exclusive gateways**  
   When an element has multiple outgoing flows, evaluate conditions (e.g. from flow or extension) and choose one path; then continue with `_follow_single_path` from the chosen target. This keeps the engine single-path per execution but allows conditional branches.

5. **Optional handler override for “next”**  
   If a handler returns a non-empty string (task id), use it as the next task id when it exists in the diagram; otherwise use `get_next_task_id`. Enables rare cases where code must override diagram order without changing the XML.

6. **Caching of workflow context**  
   For the same `workflow_id` in a request or run, reuse the result of `get_workflow_context` (or at least BPMN + bindings) to avoid repeated file/registry access. Invalidate or TTL when versions change if you support hot-reload.

**Lower priority**

7. **Nested parallel regions**  
   Fork/join pairs are single-level; nested forks after a fork are rejected with **`join_correlation_failed`**.

8. **Timeouts**  
   Add optional per-task or per-run timeouts and ensure the runner can mark the run as failed and set `failed_node_id` when a timeout occurs.

---

## 5. Verdict

The design is sound and fits the goal: **diagram-driven execution for linear workflows**, with a clear fallback to the existing executor and correct pause/resume. The implementation is consistent with the rest of the codebase and keeps the BPMN engine focused on orchestration while reusing parsing and runner lifecycle.

The main limitations are **intentional** (linear only, no gateways) and should be documented. The suggested improvements are incremental (failure reporting, docs, optional overrides, then gateways/timeouts) and do not require a redesign.

**Recommendation:** Treat the current implementation as the v1 BPMN engine, document its contract and limitations, and add the high-value, low-effort items (failed_node_id, error messaging, docs) soon. Plan gateway support and optional handler override as v2 when you have workflows that need them. See [BPMN_V2_PLAN.md](BPMN_V2_PLAN.md) for the v2 BPMN semantics plan (exclusive/parallel gateways, failure reporting, cancellation/timeout).

---

## 6. Consolidation TODOs (single execution model)

**Goal:** Once the BPMN engine is proven in production, migrate all workflows to it and remove the legacy “Python step chain” path so there is **only one way** to execute flows. This simplifies code and avoids two parallel patterns.

- [ ] **Validate BPMN engine in production** – Run bi_weekly_report (and any other BPMN-ready workflow) via the engine for a period; confirm completion, pause/resume, and run-detail UI (e.g. completed_node_ids). Fix any bugs before consolidation.
- [ ] **Document BPMN-engine contract** – Add a “BPMN-engine-ready workflow” section to the developer guide: state class in workflow.py, BPMN + bindings, handler `(self, state)` signature, input_schema → state constructor. List which workflows are already compatible.
- [ ] **Migrate bi_weekly_report to BPMN-only** – Remove `_register_steps()` and `self.workflow.add_step(...)`; keep only handler methods. Remove or simplify `run()` so it only builds initial state (or leave a minimal `run()` that the runner no longer uses when `can_run_with_bpmn_engine` is True). Ensure BPMN + bindings fully define order.
- [ ] **Migrate property_due_diligence to BPMN engine** – Same as above: add/align BPMN and bindings, introduce a state class if missing, implement handlers as methods, remove step registration and legacy `run()` orchestration.
- [ ] **Migrate bidder_onboarding to BPMN engine** – Same pattern; preserve human-task pause/resume via TaskPendingException and ensure next_step is the BPMN task id.
- [ ] **Migrate dap_report (or decide out-of-scope)** – DAP report uses a different pattern (no Flo state class). Either refactor to a BPMN-engine-ready state + handlers, or explicitly keep it on legacy `executor.run()` and document why.
- [ ] **Remove legacy execution path** – Once all supported workflows run via the BPMN engine, remove the `else` branch in `_run_executor_to_completion` that calls `executor_instance.run(**input_data)`. Remove or deprecate `can_run_with_bpmn_engine` (always use engine when BPMN+bindings+state exist) and any consumer/runner code that only runs the old step chain.
- [ ] **Simplify workflow base / Flo usage** – If no workflow still uses `Workflow.add_step()` and `workflow.run(initial_state)`, consider removing or simplifying the Flo `Workflow` class usage in workflow modules so that only handler methods and state remain; the BPMN engine owns orchestration.
- [ ] **Update tests and docs** – Update any tests that assume the old step chain or `executor.run()`. Update READMEs, USER_STORY, and architecture docs to describe “one execution model: BPMN-driven.”

---

## 7. Design: Parallel gateways (next milestone)

This section is a **design-only** pass before implementing parallel gateways. No implementation is implied; the intent is to agree on semantics and data shapes so that a future implementation stays consistent.

### Multi-token schema

- **Representation:** The engine already reserves `branch_id` on each token. For parallel gateways, **multiple active tokens** will be allowed: one per branch after a parallel fork. Each token has `current_element_id` and `branch_id` (e.g. a UUID or a stable branch index). The `active_tokens` list in engine state will hold more than one entry while branches are in progress.
- **Mapping to branches:** When the engine hits a parallel gateway (fork), it will create one new token per outgoing sequence flow and advance each token to the flow's target. The original token is retired; the new tokens share the same "fork point" in the diagram but are independent until join.
- **Single-token today:** Current v2 engine uses a single token; the list structure and reserved `branch_id` are already in place so that adding multiple tokens is an extension of the same schema.

### Join semantics

- **When a join gateway is reached:** A join gateway has multiple incoming flows and one outgoing flow. When a token arrives at the join, the engine records that this branch has reached the join (e.g. "branch X completed up to join J"). The outgoing flow is taken only when **all** branches that were forked at the corresponding parallel gateway have reached this join (or an equivalent join in the same "join set," if we support multiple join gateways for one fork).
- **How many tokens to wait for:** The number of tokens to wait for is determined by the fork that created the branches. So the join is bound to a specific fork (e.g. by storing a `fork_id` or by diagram structure). When the last expected token arrives, all tokens that reached the join are consumed and **one** new token is produced on the outgoing flow.
- **State merge:** When merging at the join, workflow business state is already shared (one state instance per run). No merge of state is required; only token count and "all branches done" matter. If future designs need branch-local state, that would be an additional field on the token or a separate structure.

### Resume semantics (multiple active branches)

- **Progress storage:** `progress_data["engine_state"]` will store the full engine state, including `active_tokens` with multiple entries. Each token's `current_element_id` and `branch_id` are persisted so that on resume the engine knows which nodes are active in which branch.
- **Partial completion:** Some branches may have completed (token reached a join and was consumed) while others are still running. The persisted state will reflect only the **remaining** active tokens and the completed/failed node sets. So "partial completion" is represented by fewer active tokens and more completed_node_ids.
- **Resume behavior:** On resume, the engine loads `engine_state`, restores `active_tokens`, and continues execution for each active token (e.g. in a deterministic order). No special "partial join" state is required beyond "these tokens are still active."

### UI progress representation

- **Multiple "current" nodes:** The UI may show multiple current nodes when there are multiple active tokens (e.g. "Branch A: task_a1; Branch B: task_b1"). Alternatively, the UI can show a simplified view such as "3 branches in progress" with an expandable list of current nodes per branch.
- **Simplified view:** For users who do not need branch detail, a single "current step" label could aggregate (e.g. "Running parallel steps") or show the first/primary branch. The exact UX is a product decision; the engine will expose enough data (e.g. `active_tokens` and their `current_element_id`s) so the UI can choose.
- **Failure in one branch:** If one branch fails, the run fails. The existing failure reporting (`failed_node_id`, `failure_reason`, `condition_failure_metadata`) applies to the failing token; the UI can show which branch failed and at which node.

### Scaffolding (for implementers)

**Canonical helper layer:** [agent_app/bpmn_parallel.py](../../agent_ui/agent_app/bpmn_parallel.py) is the single module for parallel token/join bookkeeping until fork/join runtime lands in the engine. It is engine-agnostic (no BPMN traversal, handlers, DB, or Django). Unit tests: `test_bpmn_parallel_scaffolding.py`.

**Token helpers:** `ensure_active_tokens`, `token_dict`, `append_token`, `replace_token_at_index`, `replace_token_by_branch_id`, `tokens_at_element`, `tokens_at_join`, `active_element_ids`, `active_branch_ids`, `remove_tokens_by_branch_ids`. `remove_tokens_by_branch_ids` drops any non-dict entries in `active_tokens` (malformed tokens are not preserved); parallel runtime should rely on normalized state after load.

**Join helpers:** `ensure_pending_joins`, `PendingJoinInfo`, `register_pending_join`, `get_pending_join`, `is_join_satisfied`, `mark_branch_arrived_at_join` (idempotent per branch), `clear_pending_join`.

When implementing parallel gateways, the following extension points apply (no full fork/join in the main loop yet):

- **Multi-token state model:** `BpmnEngineStateSchema` documents `active_tokens`, `pending_joins`, and failure metadata alongside list fields; use `branch_id` on each token at a parallel fork.
- **Join bookkeeping:** `pending_joins` on engine state holds `PendingJoinInfo`-shaped dicts per join element id so the engine can tell when all sibling branches have arrived.
- **Progress representation for multiple active nodes:** `current_node_ids` can remain a list; with multiple tokens it becomes the list of `current_element_id` from each active token. The UI and `progress_data` already pass lists; no change to the shape, only to how the list is populated.
- **Pause/resume with more than one active branch:** Persist `active_tokens` as today; on resume, restore all tokens and run the main loop once per active token (or in a round-robin). No change to `progress_data` keys; only the number of entries in `active_tokens` and the resume loop logic.

Implementation of the above is deferred until this design is agreed and prioritized.

## Verification

Recommended focused verification commands for the current BPMN stack:

- `cd agent_ui && ../venv/bin/pytest agent_app/tests/test_bpmn_run_diagnostics.py agent_app/tests/test_workflows_progress.py agent_app/tests/test_bpmn_engine.py agent_app/tests/test_workflow_runner_integration.py -q`
- `cd agent_ui && ../venv/bin/python manage.py test agent_app.tests.test_bpmn_conformance`

The Django app skips startup validation checks during `manage.py test` so conformance output stays focused on BPMN behavior rather than startup noise.
