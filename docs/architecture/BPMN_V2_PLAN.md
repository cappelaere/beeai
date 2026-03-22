# BPMN Engine V2 Design Spec

**Status:** Proposed architecture and implementation design.  
**Audience:** Workflow engine maintainers, Workflow Studio maintainers, backend developers.  
**Scope:** Extend the **current** BPMN runtime (already token-based with parallel fork/join, exclusive gateways, boundaries, intermediate catch, embedded subprocess phase 1, cancel/timeout, retries—see [BPMN_ENGINE_REVIEW.md](./BPMN_ENGINE_REVIEW.md)) toward **fuller BPMN 2.0** semantics, stronger operational controls, and clearer evolution paths.

---

## 1. Summary

Today’s engine is **BPMN-only** and supports a **documented subset** of BPMN 2.0 (not merely linear diagrams). It remains **not** a complete BPMN 2.0 execution environment: unsupported constructs and edge cases are called out in the engine review and save-time validation.

V2 (this spec) targets **further** upgrades beyond the current baseline, for example:

- deeper coverage of BPMN constructs and stricter operational guarantees
- richer failure/retry policies and observability
- optional features still called out as future work in the review (e.g. some handler-override semantics, per-task timeouts, nested parallel regions)

Historical contrast (pre–parallel-gateway era)—the engine used to be conceptualized as:

- one current task
- one path through the graph

The **current** baseline already includes:

- a **token-based** execution model (multi-token after parallel fork)
- **exclusive gateway** condition evaluation
- **parallel gateway** fork/join (with save-time correlation rules)
- workflow-level **timeout**, **cancellation**, and **task retry** policies
- richer persisted engine state (see `normalize_engine_state`)

This spec defines additional intended behavior, architecture boundaries, persistence evolution, rollout plan, and the main files that should change as the runtime moves toward fuller BPMN 2.0 coverage.

---

## 2. Goals

**Note:** The **current** runtime already implements exclusive and parallel gateways (with constraints), token persistence, pause/resume across branches, workflow-level cancel/timeout, task retries, and BPMN run diagnostics. The goals below describe **V2 evolution**—tightening semantics, extending BPMN coverage, and operational hardening—not a from-scratch engine.

### Primary goals

1. Execute **exclusive gateways** using BPMN flow conditions, not only Python handler return values.
2. Execute **parallel gateways** using explicit fork/join semantics.
3. Persist enough runtime state to support **pause/resume**, **retry**, and **failure recovery** in branched flows.
4. Improve **operability** with failed-node reporting, timeouts, cancellation, and structured engine diagnostics.
5. Keep Workflow Studio and BPMN editing tools aligned with the runtime so generated workflows are valid by construction.

### Secondary goals

1. Keep linear workflows simple and backward-compatible within the BPMN-only model.
2. Preserve the current separation of concerns between parsing, orchestration, and Django integration.
3. Make the new execution semantics testable without requiring full end-to-end Django setup for every case.

---

## 3. Non-goals for V2

The following are intentionally out of scope unless required by a later phase:

1. Full BPMN 2.0 conformance across every event and artifact type.
2. Visual BPMN modeling parity with dedicated BPM suites.
3. Compensation transactions.
4. Multi-instance tasks.
5. Arbitrary script execution embedded directly in BPMN XML.
6. Distributed worker scheduling across multiple machines.

V2 focuses on the subset that materially advances RealtyIQ workflow execution:

- start/end events
- service tasks
- user tasks
- exclusive gateways
- parallel gateways
- timer/wait semantics where needed for workflow execution

---

## 4. Current v1 limitations

The current implementation is documented in:

- [BPMN_ENGINE_REVIEW.md](./BPMN_ENGINE_REVIEW.md)
- [BPMN_CONSOLIDATION_TODOS.md](./BPMN_CONSOLIDATION_TODOS.md)

The key limitations V2 addresses are:

1. Single-path traversal in `workflow_context`.
2. No explicit evaluation of BPMN conditions on sequence flows.
3. No parallel fork/join execution.
4. No token model for multiple active branches.
5. Limited timeout/cancellation behavior.
6. Failure reporting that is not yet branch-aware.
7. Workflow Studio generation that is still biased toward linear BPMN flows.

---

## 5. Supported BPMN semantics in V2

### Supported

1. **Start events**
2. **End events**
3. **Service tasks**
4. **User tasks**
5. **Exclusive gateways**
6. **Parallel gateways**
7. **Sequence flow conditions** for exclusive path selection
8. **Default flow** for exclusive gateways
9. **Per-task timeout** and **per-run timeout**
10. **Cancellation checks** between executable steps
11. **Retry policy hooks** for selected task failures

### Deferred / optional follow-on

1. Intermediate timer events as standalone BPMN nodes
2. Boundary timer/error events
3. Embedded subprocesses
4. Event-based gateways
5. Message/signal events

The runtime and persistence model should be designed so these can be added later without redesigning the core engine state.

---

## 6. Core architecture

V2 should split the engine into three clear layers.

### 6.1 Graph layer

Responsible for:

- parsing BPMN structure
- validating graph semantics
- identifying gateway kinds
- choosing next flow(s)
- tracking join dependencies

Likely homes:

- `agent_ui/agent_app/workflow_context.py`
- a new helper module such as `agent_ui/agent_app/bpmn_graph.py`

### 6.2 Execution runtime layer

Responsible for:

- managing execution tokens
- invoking handlers
- applying retry, timeout, cancellation rules
- moving tokens through the graph
- emitting engine progress events

Likely homes:

- `agent_ui/agent_app/bpmn_engine.py`
- optionally a new `agent_ui/agent_app/bpmn_runtime.py`

### 6.3 Integration layer

Responsible for:

- loading workflow context
- persisting workflow run state
- broadcasting WebSocket progress
- mapping engine failures to UI / DB state
- resume and restart behavior

Likely homes:

- `agent_ui/agent_app/workflow_runner.py`
- `agent_ui/agent_app/consumers.py`
- `tools/workflow_actions.py`

---

## 7. Runtime model: execution tokens

V2 replaces the implicit single-pointer model with **execution tokens**.

### 7.1 Token definition

Each active branch of execution is represented by a token with fields like:

- `token_id`
- `current_element_id`
- `status` (`active`, `waiting`, `completed`, `failed`, `cancelled`)
- `branch_key`
- `parent_token_id`
- `created_at`
- `updated_at`
- `retry_count`
- `waiting_reason`

### 7.2 Engine state definition

The BPMN runtime state persisted for a workflow run should include:

- `active_tokens`
- `completed_tokens`
- `waiting_tokens`
- `gateway_state`
- `completed_node_ids`
- `current_node_ids`
- `failed_node_ids`
- `cancel_requested`
- `deadline_at`
- `engine_version`

### 7.3 Business state vs engine state

Keep **workflow business state** separate from **engine runtime state**.

- Business state: workflow-specific Pydantic state object (`MyWorkflowState`)
- Engine state: BPMN traversal/persistence bookkeeping

This avoids overloading `state.workflow_steps` with all orchestration concerns and makes branch-aware resume possible.

---

## 8. Exclusive gateway semantics

### 8.1 Required behavior

When an exclusive gateway has multiple outgoing sequence flows:

1. Read all outgoing flows.
2. Evaluate any attached condition expressions in deterministic order.
3. Select the first matching flow.
4. If no condition matches, follow the default flow if one is defined.
5. If no default exists, fail the run with a structured gateway-selection error.

### 8.2 Condition source

V2 should support conditions from sequence flows first:

- `bpmn:conditionExpression`

Optional future extension:

- extension-element metadata
- editor-generated metadata blocks

### 8.3 Condition evaluation model

Conditions must be evaluated safely against workflow state, not via arbitrary `eval()`.

Recommended approach:

1. define a small supported expression language
2. parse into an AST or a constrained evaluator
3. expose read-only workflow state fields and helper predicates

Examples:

- `state.requires_manual_review == true`
- `state.bid_limit > 100000`
- `state.analysis_results.risk_level == "high"`

### 8.4 Validation rules

Validation should reject:

- exclusive gateways with multiple outgoing flows but no conditions and no default
- malformed condition expressions
- multiple defaults
- references to unavailable state variables when statically detectable

---

## 9. Parallel gateway semantics

### 9.1 Fork behavior

At a parallel fork gateway:

1. consume the incoming token
2. create one child token per outgoing branch
3. mark each child token active at its target element

### 9.2 Join behavior

At a parallel join gateway:

1. record arrival of each incoming branch
2. do not continue until all expected incoming branches have arrived
3. once complete, produce a single merged token
4. continue on the outgoing path

### 9.3 Join bookkeeping

Persist per-gateway join state:

- `gateway_id`
- `expected_incoming_count`
- `arrived_token_ids`
- `released`

### 9.4 Failure semantics in parallel branches

Initial V2 recommendation:

- if any required branch fails, the run fails
- failed branch should record `failed_node_id`
- sibling branches should be cancelled or marked abandoned explicitly

Optional future policy:

- allow workflow-defined branch failure tolerance

---

## 10. User task and wait semantics

Current pause/resume behavior should be preserved and generalized for branch-aware execution.

### Required behavior

1. A token may enter `waiting` state due to `TaskPendingException` or future timer wait.
2. Waiting tokens remain persisted in engine state.
3. Resume restarts only the waiting branch or the next eligible token set.
4. UI should be able to show waiting nodes and pending human tasks.

### Future-ready extension

Use the same waiting-token model for:

- human approvals
- timer waits
- external callbacks

---

## 11. Timeout, cancellation, and retry

### 11.1 Timeouts

Support:

- **per-task timeout**
- **per-run timeout**

On timeout:

- mark token or run failed
- record `failed_node_id`
- persist reason as structured engine metadata

### 11.2 Cancellation

The engine should check for cancellation:

- before starting each task
- after each task completes
- before releasing parallel joins

On cancellation:

- mark active tokens cancelled
- persist progress
- stop scheduling new work

### 11.3 Retries

V2 should add retry hooks, even if policies are conservative at first.

Suggested policy model:

- `max_attempts`
- `retryable_exceptions`
- `backoff_seconds`
- `scope` (`task`, later possibly `branch`)

Retry policy can initially live outside BPMN XML in bindings or workflow metadata.

---

## 12. Persistence and resume

### 12.1 Persistence requirements

The workflow run record must persist enough data to reconstruct:

- business state
- active/waiting tokens
- gateway join state
- completed/current/failed nodes
- retry counters
- timeout/cancellation metadata

### 12.2 Resume behavior

Resume should:

1. reconstruct business state
2. reconstruct engine runtime state
3. resume waiting or active tokens
4. avoid replaying already-completed branches

### 12.3 Backward compatibility

Linear v1 workflows should still serialize into the new engine state shape with one token.

---

## 13. Validation model

Validation should move beyond shape-only YAML checks and into BPMN semantic checks.

### Validate at least

1. workflow has a state class
2. bindings exist for executable tasks
3. handlers exist on executor
4. start event can reach executable nodes
5. no unreachable executable nodes
6. exclusive gateways are structurally valid
7. parallel fork/join pairs are structurally valid
8. unsupported BPMN element types are clearly flagged
9. default flows and conditions are valid

### Validation entry points

- save-time validation in Workflow Studio
- admin editor validation before persistence
- runtime startup validation as final guardrail

---

## 14. Workflow Studio and BPMN tooling impact

Workflow Studio and BPMN editing tools must align with V2 semantics.

### Required updates

1. Generate exclusive gateways when prompts imply branching.
2. Generate condition placeholders or guided condition definitions.
3. Generate parallel branches when prompts imply independent concurrent checks.
4. Validate BPMN/bindings before writing files.
5. Explain unsupported constructs to the user instead of silently flattening them.

### Tooling changes

Primary files:

- `agent_ui/agent_app/views/api_workflows.py`
- `tools/bpmn_tools.py`
- `agent_ui/agent_app/schema_validation.py`

---

## 15. Observability and UI implications

V2 should produce richer workflow execution telemetry.

### Engine events to expose

1. token created
2. token completed
3. token waiting
4. gateway branch selected
5. parallel fork created
6. join waiting / join released
7. task retry
8. timeout
9. cancellation

### UI expectations

The run-detail UI should eventually support:

- multiple current nodes
- failed node highlighting
- waiting nodes
- branch-aware progress

---

## 16. File-level implementation touchpoints

### Primary files

- `agent_ui/agent_app/workflow_context.py`
- `agent_ui/agent_app/bpmn_engine.py`
- `agent_ui/agent_app/workflow_runner.py`
- `agent_ui/agent_app/consumers.py`
- `tools/workflow_actions.py`
- `tools/bpmn_tools.py`
- `agent_ui/agent_app/schema_validation.py`
- `agent_ui/agent_app/views/api_workflows.py`

### Likely supporting additions

- `agent_ui/agent_app/bpmn_graph.py`
- `agent_ui/agent_app/bpmn_state.py`
- `agent_ui/agent_app/bpmn_conditions.py`

These new modules are recommended to avoid overloading `bpmn_engine.py`.

---

## 17. Rollout plan

### Phase 1: foundations

1. introduce engine runtime state schema
2. separate graph semantics from execution runtime
3. add richer semantic validation

### Phase 2: exclusive gateways

1. parse conditions
2. implement safe condition evaluator
3. execute exclusive gateways
4. add dedicated tests

### Phase 3: operational controls

1. failed-node reporting
2. timeouts
3. cancellation
4. retry hooks

### Phase 4: parallel gateways

1. token fan-out
2. join bookkeeping
3. branch-aware persistence
4. branch-aware UI updates

### Phase 5: Workflow Studio alignment

1. generation of branching BPMN
2. validation before write
3. clearer generated docs and metadata

---

## 18. Testing strategy

V2 needs dedicated tests beyond existing workflow command tests.

### Unit tests

1. BPMN parse and graph validation
2. exclusive gateway condition evaluation
3. parallel fork/join token handling
4. timeout and cancellation behavior
5. retry policy behavior

### Integration tests

1. full run with exclusive branching
2. full run with parallel fork/join
3. pause/resume during branched execution
4. failure reporting and failed-node UI metadata

### Studio generation tests

1. generated BPMN passes semantic validation
2. generated bindings match handlers
3. generated metadata/state contract is runnable

---

## 19. Open questions

1. Should conditions live only in BPMN XML, or also in bindings/metadata?
2. Should join failures cancel sibling branches immediately or wait for safe cleanup?
3. Do retries belong in bindings, metadata, or a future BPMN extension format?
4. Should subprocess support be included in V2 or deferred to V2.1?
5. How much branch state should be exposed in the UI versus kept internal?

These questions should be resolved before Phase 2 implementation begins.

---

## 20. Decision summary

V2 will treat the BPMN engine as a **true runtime**, not just a linear step sequencer over BPMN-shaped diagrams.

The key architectural decision is:

- keep **workflow business state** separate from **engine execution state**
- use **execution tokens** as the core runtime abstraction
- add semantics incrementally in this order:
  1. exclusive gateways
  2. operational controls
  3. parallel gateways
  4. Studio/tooling alignment

That path gives the highest value with the lowest redesign risk and keeps the current BPMN-first direction intact.
