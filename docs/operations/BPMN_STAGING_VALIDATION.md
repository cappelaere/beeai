# BPMN real-environment validation (Issue #7)

This document records **how** to validate BPMN-only workflow execution outside local unit tests, and **where** to capture evidence. It complements [BPMN_RUN_OPERATORS.md](./BPMN_RUN_OPERATORS.md) (expected run-detail semantics).

## 1. Preconditions (record per exercise)

| Field | Value (fill when validating) |
|-------|------------------------------|
| **Environment** | **Local full-stack (Django test DB, in-memory SQLite)** — same application code paths as deployment; not a hosted staging URL. |
| **Date** | 2026-03-23 |
| **Operator** | Cursor agent (automated) |
| **App version / commit** | Branch `chore/7-bpmn-staging-validation` / commit at time of run (see git); validation logs below from post-doc run. |

**Catalog-visible BPMN workflows** (default registry list; `hide_from_catalog` workflows are excluded from the Workflows UI):

| Workflow ID | Notes / data prerequisites |
|-------------|----------------------------|
| `bidder_onboarding` | Inputs: `bidder_name`, `property_id`, `registration_data` with `email`, `phone`, `terms_accepted`, `age_accepted`. |
| `property_due_diligence` | Requires a valid `property_id` for your environment’s data sources. |
| `bi_weekly_report` | Requires `start_date` and `end_date` (report window); uses portfolio/agents as configured. |
| `dap_report` | Requires `report_date`; optional `lookback_days`. GRES / agent stack affects retrieval path. |

Confirm each workflow appears under **Workflows** in the UI before treating the environment as ready.

**Hosted staging/production:** No URL was available in-repo for this pass. Re-run section 3 against your deployed host when credentials are ready; paste new run IDs and outcomes below or in a follow-up PR.

## 2. Automated baseline (local / CI)

These tests exercise the **same** runner and persistence paths as the app (`execute_workflow_run`, `resume_bpmn_after_pause`, `progress_data`, fork/join). They do **not** replace hosted staging UI validation.

From repo root (with Django test DB available and no other process holding `agent_ui/db.sqlite3`):

```bash
cd agent_ui && ../venv/bin/python manage.py test agent_app.tests.test_workflow_runner_integration --settings=agent_ui.settings -v 1
```

**Result (2026-03-23):** `Ran 17 tests` — **OK** (pause/resume, retry, cancel, timeout, parallel fork/join, message catch).

**Optional product workflow smoke** (same test DB; hits real handlers; **off by default** so CI stays fast):

```bash
cd agent_ui && ISSUE7_PRODUCT_SMOKE=1 ../venv/bin/python manage.py test \
  agent_app.tests.test_issue7_product_workflows --settings=agent_ui.settings -v 2
```

Coverage highlights (see `test_workflow_runner_integration.py` for full list):

- **`runner_integration_test`** — pause for human task, resume, completed steps, failure / retry metadata.
- **`runner_parallel_fj_test`** — parallel fork/join completion, pause before join + resume, pending joins, branch failure, cancel, timeout scenarios.
- **`par015_message_runner`** — intermediate message catch + resume.

## 3. Staging / production validation matrix

For each workflow, runs below used **`execute_workflow_run`** on the **Django test database** (not the WebSocket entrypoint). **Run-detail UI** was checked via HTTP `GET /workflows/runs/<run_id>/` in the same tests (anonymous session user id 9): response **200** and HTML contained BPMN diagram / operator markers (`workflow-diagram-bpmn` or “BPMN diagram” copy).

### 3.1 Completion (happy path)

| Workflow ID | Run ID | Pass / Fail / Skip | Notes |
|-------------|--------|--------------------|-------|
| `dap_report` | `121edda3` | **Fail** | Run ends **failed**: exclusive gateway `Gateway_1` has no matching condition after GRES retrieval (see §5). |
| `bi_weekly_report` | `f8d08b78` | **Pass** | **Completed**; executive brief path exercised with seeded property data in test DB. |
| `property_due_diligence` | `9bcc0d48` | **Pass** | **Completed**; parallel research + report handlers with simulated GRES-style data. |
| `bidder_onboarding` | `494034f4` | **Fail** | Run ends **failed** at `Gateway_SAM_Decision` (no matching condition / default) after successful `validate_input` (see §5). |

### 3.2 Pause / resume

| Workflow ID | Run ID | Pass / Fail / Skip | Notes |
|-------------|--------|--------------------|-------|
| `runner_integration_test` | (see logs) | **Pass** | Covered by `test_workflow_runner_integration` — `waiting_for_task`, resume, completion. |
| `runner_parallel_fj_test` | (see logs) | **Pass** | Pause before join + resume + completion covered in same suite. |

Product workflows in this pass did not reach a stable **waiting_for_task** state for manual pause testing; follow-up on staging with a human-task path if required.

### 3.3 Run-detail UI (progress, current / completed nodes)

| Workflow ID | Run ID | Pass / Fail / Skip | Notes |
|-------------|--------|--------------------|-------|
| `dap_report` | `121edda3` | **Pass** | Failed run still rendered run-detail with BPMN markers (diagnostics for failed BPMN run). |
| `bi_weekly_report` | `f8d08b78` | **Pass** | Completed run; BPMN UI markers present. |
| `property_due_diligence` | `9bcc0d48` | **Pass** | Completed run; BPMN UI markers present. |
| `bidder_onboarding` | `494034f4` | **Pass** | Failed run; BPMN UI markers present. |

### 3.4 Failure presentation (controlled)

| Workflow ID | Run ID | Pass / Fail / Skip | Notes |
|-------------|--------|--------------------|-------|
| `bidder_onboarding` | `494034f4` | **Pass** | **Failed** with engine error text in logs; run-detail page served for post-mortem review. |
| `dap_report` | `121edda3` | **Pass** | **Failed** at gateway after agent step; same run-detail behavior. |

## 4. Parallel fork / join (UI vs automated)

**Repository fact:** The only committed BPMN with parallel gateways is **`runner_parallel_fj_test`**, which sets `hide_from_catalog: true`.

| Method | Environment | Run ID | Pass / Fail / Skip | Notes |
|--------|-------------|--------|--------------------|-------|
| Integration tests | Django test DB | N/A | **Pass** | `manage.py test …test_workflow_runner_integration` — fork/join, pending joins, failures, cancel, timeout. |
| Product parallel research | Django test DB | `9bcc0d48` | **Pass** | `property_due_diligence` uses parallel subprocess pattern in handlers; run **completed** (not the same as BPMN parallel gateway tokens, but exercises multi-branch persistence). |
| Live UI (`runner_parallel_fj_test`) | — | — | **Skip** | Hidden from catalog; use API or temporary catalog flag on staging if UI proof is required. |

## 5. Bugs and follow-ups

| Issue | Summary |
|-------|---------|
| [#9](https://github.com/cappelaere/beeai/issues/9) | **`bidder_onboarding` / `dap_report`:** Exclusive gateways **`Gateway_SAM_Decision`** and **`Gateway_1`** — no matching condition / default after handler transitions (runs `494034f4`, `121edda3`). Track fix and BPMN updates there. |
| **Fixed in this branch** | **`dap_report`:** `import agent_ui.agent_runner` failed when `sys.path` prioritized `agent_ui/` (inner package shadowed outer project package). Resolved by loading `agent_runner` via `importlib` from repo-relative path (`workflows/dap_report/workflow.py`). |

---

**Status:** Local full-stack validation **completed** for Issue #7 on 2026-03-23. Hosted staging/production should still run the same matrices when a deployment URL is available. When hosted rows are filled, optionally narrow Phase 1 wording in [BPMN_CONSOLIDATION_TODOS.md](../architecture/BPMN_CONSOLIDATION_TODOS.md).
