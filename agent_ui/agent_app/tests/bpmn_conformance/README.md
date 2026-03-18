# BPMN conformance fixtures (PAR-012)

Small **corpus of Python-defined BPMN dicts** plus a harness that runs:

- `validate_bpmn_for_save` (save-time validation)
- `run_bpmn_workflow` (execution, cancel/timeout via `execution_check`, pause/resume via `TaskPendingException`)

This is **not** a BPMN 2.0 conformance suite: no XML round-trips, no exhaustive element coverage, and no claim of external standard compliance.

## What is covered

| Area | Examples |
|------|----------|
| Validation | Mixed fork/join paths, nested parallel fork, invalid parallel gateway topology (`pass_through`) |
| Happy execution | Linear chain, exclusive gateway with matching condition, parallel fork-only, fork→join→downstream |
| Pause/resume | Human pause on one parallel branch; second `run_bpmn_workflow` with `start_from_task_id` |
| Failure metadata | Exclusive no-match (`invalid_gateway`), parallel branch `handler_error`, cooperative `cancelled` / `timeout`, `retry_exhausted` |

## Run tests

From the Django project root (`agent_ui/`):

```bash
python manage.py test agent_app.tests.test_bpmn_conformance
```

## Add a fixture

1. Copy an existing BPMN `elements` / `sequence_flows` pattern from `fixtures/registry.py` or from `test_bpmn_engine.py` / `test_workflow_context.py`.
2. Register a `ValidationFixture` or `ExecutionFixture` in `fixtures/registry.py` (`VALIDATION_FIXTURES` / `EXECUTION_FIXTURES`). For execution, set `bindings_raw.serviceTasks` handler names and matching `behaviors` per task id (`ok`, `retryable_once`, `retry_always`, `fail_runtime`, `pause_human`).
3. For pause/resume, set `expect.outcome = "task_pending"`, `pause_next_step`, and `pause_at_element_id` (the task that raises `TaskPendingException`).
4. Tag execution fixtures: `execution_happy`, `pause_resume`, or `failure_metadata` so they route to the right test method.

## Out of scope (v1)

- Full BPMN 2.0 semantics, boundary events, subprocesses
- Replacing or deleting existing unit tests in `test_bpmn_engine.py` / `test_workflow_context.py`
- Browser / UI tests

See [BPMN engine review](../../../../docs/architecture/BPMN_ENGINE_REVIEW.md) for architecture context.
