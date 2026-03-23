# BPMN real-environment validation (Issue #7)

This document records **how** to validate BPMN-only workflow execution outside local unit tests, and **where** to capture evidence. It complements [BPMN_RUN_OPERATORS.md](./BPMN_RUN_OPERATORS.md) (expected run-detail semantics).

## 1. Preconditions (record per exercise)

| Field | Value (fill when validating) |
|-------|------------------------------|
| **Environment** | e.g. staging URL or production (name only in git; no secrets) |
| **Date** | |
| **Operator** | |
| **App version / commit** | e.g. git SHA deployed |

**Catalog-visible BPMN workflows** (default registry list; `hide_from_catalog` workflows are excluded from the Workflows UI):

| Workflow ID | Notes / data prerequisites |
|-------------|----------------------------|
| `bidder_onboarding` | Inputs: `bidder_name`, `email`, `phone`, `property_id`, `age_accepted`, `terms_accepted`. External SAM/OFAC behavior depends on environment configuration. |
| `property_due_diligence` | Requires a valid `property_id` for your environment’s data sources. |
| `bi_weekly_report` | Requires `start_date` and `end_date` (report window); uses portfolio/agents as configured. |
| `dap_report` | Requires `report_date`; optional `lookback_days`. DAP agent availability affects outcome. |

Confirm each workflow appears under **Workflows** in the UI before treating the environment as ready.

## 2. Automated baseline (local / CI)

These tests exercise the **same** runner and persistence paths as the app (`execute_workflow_run`, `resume_bpmn_after_pause`, `progress_data`, fork/join). They do **not** replace staging UI validation.

From repo root (with Django test DB available and no other process holding `agent_ui/db.sqlite3`):

```bash
cd agent_ui && ../venv/bin/python -m pytest agent_app/tests/test_workflow_runner_integration.py -q
```

Coverage highlights (see file for full list):

- **`runner_integration_test`** — pause for human task, resume, completed steps, failure / retry metadata.
- **`runner_parallel_fj_test`** — parallel fork/join completion, pause before join + resume, pending joins, branch failure, cancel, timeout scenarios.
- **`par015_message_runner`** — intermediate message catch + resume.

Product workflows (`dap_report`, `bi_weekly_report`, etc.) are not the subject of this module; validate them in the matrix below in a real deployment.

## 3. Staging / production validation matrix

For each workflow, run from the **Workflows** UI (or equivalent API), then open **run detail**. Record **run id** from the UI or URL.

### 3.1 Completion (happy path)

| Workflow ID | Run ID | Pass / Fail / Skip | Notes |
|---------------|--------|--------------------|-------|
| `dap_report` | | | |
| `bi_weekly_report` | | | |
| `property_due_diligence` | | | |
| `bidder_onboarding` | | | |

### 3.2 Pause / resume

Use a workflow that reaches **Waiting for task** (human step). Confirm resume continues from the documented task / resume point.

| Workflow ID | Run ID | Pass / Fail / Skip | Notes |
|---------------|--------|--------------------|-------|
| | | | |

### 3.3 Run-detail UI (progress, current / completed nodes)

Compare timeline and diagnostics to [BPMN_RUN_OPERATORS.md](./BPMN_RUN_OPERATORS.md).

| Workflow ID | Run ID | Pass / Fail / Skip | Notes |
|---------------|--------|--------------------|-------|
| | | | |

### 3.4 Failure presentation (controlled)

Prefer invalid inputs, sandbox data, or a non-production environment. Capture **failed node** and message when applicable.

| Workflow ID | Run ID | Pass / Fail / Skip | Notes |
|---------------|--------|--------------------|-------|
| | | | |

## 4. Parallel fork / join (UI vs automated)

**Repository fact:** The only committed BPMN with parallel gateways is **`runner_parallel_fj_test`**, which sets `hide_from_catalog: true` and does not appear on the default Workflows list.

**Chosen validation method for fork/join engine + persistence:**

1. **Primary:** Automated tests in `agent_app/tests/test_workflow_runner_integration.py` (`RunnerParallelFjIntegrationTests`).
2. **Optional in a deployed environment:** Start `runner_parallel_fj_test` via internal API or temporarily expose it (e.g. staging-only branch with `hide_from_catalog: false`) strictly for validation—then restore.

Record here if a **live UI** parallel run was performed:

| Method | Environment | Run ID | Pass / Fail / Skip | Notes |
|--------|-------------|--------|--------------------|-------|
| Integration tests only | CI / local | N/A | | |
| Live UI or API | | | | |

## 5. Bugs and follow-ups

If a defect is found during real-environment runs, file a **new GitHub issue** with run id, workflow id, expected vs actual, and screenshots. Link it from this section when updating the doc after triage.

| Issue | Summary |
|-------|---------|
| | |

---

**Status:** Automated baseline is defined above. **Staging/production table rows are intentionally left for operators** to fill after exercises. When those rows are completed and any bugs are filed or fixed, update [BPMN_CONSOLIDATION_TODOS.md](../architecture/BPMN_CONSOLIDATION_TODOS.md) Phase 1 accordingly.
