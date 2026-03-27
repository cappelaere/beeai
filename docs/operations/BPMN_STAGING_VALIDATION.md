# BPMN real-environment validation (Issue #7)

This document records **how** to validate BPMN-only workflow execution and **where** to capture evidence. It complements [BPMN_RUN_OPERATORS.md](./BPMN_RUN_OPERATORS.md) (expected run-detail semantics).

**Important:** Local/test-DB evidence (**§4** below) is **partial** only. **Hosted** staging or production matrices (**§3**) are required before Phase 1 can be checked off in [BPMN_CONSOLIDATION_TODOS.md](../architecture/BPMN_CONSOLIDATION_TODOS.md).

## 1. Preconditions (record per exercise)

Use a **separate row** (or re-fill this table) for each validation campaign—**hosted** vs **local** must not be conflated.

| Field | Local reference (2026-03-23) | Hosted (fill when you run staging/production) |
|-------|------------------------------|-----------------------------------------------|
| **Environment** | Django **test** DB only | e.g. Staging — `https://…` (no secrets in git) |
| **Date** | 2026-03-23 | |
| **Operator** | Cursor agent (automated) | |
| **App version / commit** | Branch `chore/7-bpmn-staging-validation` | Deployed **SHA or release tag** |

**Catalog-visible BPMN workflows** (default registry list; `hide_from_catalog` workflows are excluded from the Workflows UI):

| Workflow ID | Notes / data prerequisites |
|-------------|----------------------------|
| `bidder_onboarding` | Inputs: `bidder_name`, `property_id`, `registration_data` with `email`, `phone`, `terms_accepted`, `age_accepted`. |
| `property_due_diligence` | Requires a valid `property_id` for your environment’s data sources. |
| `bi_weekly_report` | Requires `start_date` and `end_date` (report window); uses portfolio/agents as configured. |
| `dap_report` | Requires `report_date`; optional `lookback_days`. GRES / agent stack affects retrieval path. |

Confirm each workflow appears under **Workflows** in the UI before treating the environment as ready.

**Hosted:** Complete **§3** tables on your deployed host, then update Phase 1 in the consolidation TODOs.

## 2. Automated baseline (local / CI)

These tests exercise the **same** runner and persistence paths as the app (`execute_workflow_run`, `resume_bpmn_after_pause`, `progress_data`, fork/join). They validate **engine mechanics**, not “production is green.”

From repo root:

```bash
cd agent_ui && ../venv/bin/python manage.py test agent_app.tests.test_workflow_runner_integration --settings=agent_ui.settings -v 1
```

**Result (2026-03-23):** `Ran 17 tests` — **OK** (pause/resume, retry, cancel, timeout, parallel fork/join, message catch).

### Optional product BPMN diagnostics (local test DB only)

Opt-in module: **`test_issue7_product_bpmn_diagnostic`**. **Not** staging sign-off.

- **`bi_weekly_report`** and **`property_due_diligence`:** tests **require** `completed` on the test DB (sanity for those two flows locally).
- **`bidder_onboarding`** and **`dap_report`:** observability-focused, but now
  with an explicit guard: runs must **not** fail with the historical issue #9
  gateway error (`no matching condition and no default flow`).

```bash
cd agent_ui && ISSUE7_PRODUCT_BPMN_DIAGNOSTIC=1 ../venv/bin/python manage.py test \
  agent_app.tests.test_issue7_product_bpmn_diagnostic --settings=agent_ui.settings -v 2
```

Coverage highlights (see `test_workflow_runner_integration.py` for full list):

- **`runner_integration_test`** — pause for human task, resume, completed steps, failure / retry metadata.
- **`runner_parallel_fj_test`** — parallel fork/join completion, pause before join + resume, pending joins, branch failure, cancel, timeout scenarios.
- **`par015_message_runner`** — intermediate message catch + resume.

## 3. Hosted staging/production validation

### 3.0 Automation blocker (2026-03-23)

**Hosted runs were not executed from this repository in the automation pass that updated this doc.**

**Reason:** There is **no** checked-in staging/production **base URL**, **authentication** method usable without secrets, or **operator session** for a deployed RealtyIQ instance. Fabricating run IDs would violate the validation procedure.

**To close Issue #7 / Phase 1:** A human operator with access must:

1. Log into the target **staging or production** app.
2. Run the workflows from the **Workflows** UI (or your approved API), using valid inputs for that environment.
3. Fill the tables below with **real** run IDs and outcomes.
4. Open **run detail** for each run and record UI/progress observations (see [BPMN_RUN_OPERATORS.md](./BPMN_RUN_OPERATORS.md)).
5. For **pause/resume**, use a workflow that reaches **Waiting for task** (or equivalent); if none is available, mark **Skip** with reason.
6. For **parallel/join** in the BPMN diagram UI: `runner_parallel_fj_test` is **hidden** from the catalog—use an internal API or temporary catalog exposure on staging **only** if approved, else **Skip** with reason.
7. Commit the filled **§3** tables (or open a PR) and then check Phase 1 in [BPMN_CONSOLIDATION_TODOS.md](../architecture/BPMN_CONSOLIDATION_TODOS.md).

### 3.1 Completion (happy path) — hosted

| Workflow ID | Run ID | Pass / Fail / Skip | Notes |
|-------------|--------|--------------------|-------|
| `dap_report` | | | |
| `bi_weekly_report` | | | |
| `property_due_diligence` | | | |
| `bidder_onboarding` | | | |

### 3.2 Pause / resume — hosted

| Workflow ID | Run ID | Pass / Fail / Skip | Notes |
|-------------|--------|--------------------|-------|
| — | — | — | Fill when a human-task pause is reachable on hosted. |

### 3.3 Run-detail UI (progress, current / completed) — hosted

| Workflow ID | Run ID | Pass / Fail / Skip | Notes |
|-------------|--------|--------------------|-------|
| — | — | — | Fill per workflow after hosted runs (see §3.1 run IDs). |

### 3.4 Failure presentation (controlled) — hosted

| Workflow ID | Run ID | Pass / Fail / Skip | Notes |
|-------------|--------|--------------------|-------|
| — | — | — | Fill after controlled failure run (non-prod preferred). |

### 3.5 Parallel fork / join — hosted

| Method | Environment | Run ID | Pass / Fail / Skip | Notes |
|--------|-------------|--------|--------------------|-------|
| Catalog BPMN parallel gateways | | | | Only `runner_parallel_fj_test` in-repo; usually **Skip** unless API/staging exposure. |

## 4. Local partial matrix (historical — test DB only)

This matrix records **one local test-DB exercise** (2026-03-23): `execute_workflow_run` (not the WebSocket entrypoint). Run-detail was checked with `GET /workflows/runs/<run_id>/` (anonymous session user id 9): **200** and BPMN markers in HTML.

**Do not** treat this table as proof that Issue #7 **hosted** acceptance criteria are met.

### 4.1 Completion (happy path)

| Workflow ID | Run ID | Pass / Fail / Skip | Notes |
|-------------|--------|--------------------|-------|
| `dap_report` | `121edda3` | **Fail** | Failed at exclusive gateway `Gateway_1` after GRES step (see §6 / issue #9). |
| `bi_weekly_report` | `f8d08b78` | **Pass** | **Completed** on test DB only. |
| `property_due_diligence` | `9bcc0d48` | **Pass** | **Completed** on test DB only. |
| `bidder_onboarding` | `494034f4` | **Fail** | Failed at `Gateway_SAM_Decision` (issue #9). |

### 4.2 Pause / resume

| Workflow ID | Run ID | Pass / Fail / Skip | Notes |
|-------------|--------|--------------------|-------|
| `runner_integration_test` | (see logs) | **Pass** | `test_workflow_runner_integration` — `waiting_for_task`, resume, completion. |
| `runner_parallel_fj_test` | (see logs) | **Pass** | Pause before join + resume in same suite. |

Product workflows in the local pass did not reach **waiting_for_task** for manual pause testing; repeat on staging if required.

### 4.3 Run-detail UI (progress, current / completed nodes)

| Workflow ID | Run ID | Pass / Fail / Skip | Notes |
|-------------|--------|--------------------|-------|
| `dap_report` | `121edda3` | **Pass** | Failed run still rendered BPMN markers (local). |
| `bi_weekly_report` | `f8d08b78` | **Pass** | Completed run; BPMN markers (local). |
| `property_due_diligence` | `9bcc0d48` | **Pass** | Completed run; BPMN markers (local). |
| `bidder_onboarding` | `494034f4` | **Pass** | Failed run; BPMN markers (local). |

### 4.4 Failure presentation (controlled)

| Workflow ID | Run ID | Pass / Fail / Skip | Notes |
|-------------|--------|--------------------|-------|
| `bidder_onboarding` | `494034f4` | **Pass** | Failed run + run-detail (local). |
| `dap_report` | `121edda3` | **Pass** | Failed run + run-detail (local). |

## 5. Parallel fork / join (UI vs automated)

**Repository fact:** The only committed BPMN with parallel gateways is **`runner_parallel_fj_test`**, which sets `hide_from_catalog: true`.

| Method | Environment | Run ID | Pass / Fail / Skip | Notes |
|--------|-------------|--------|--------------------|-------|
| Integration tests | Django test DB | N/A | **Pass** | `test_workflow_runner_integration` — fork/join, pending joins, failures, cancel, timeout. |
| Product parallel research | Django test DB | `9bcc0d48` | **Pass** | `property_due_diligence` handler parallelism; not the same as BPMN parallel gateway tokens. |
| Live UI (`runner_parallel_fj_test`) | — | — | **Skip** | Hidden from catalog; use API or temporary catalog flag on staging if UI proof is required. |

## 6. Bugs and follow-ups

| Issue | Summary |
|-------|---------|
| [#9](https://github.com/cappelaere/beeai/issues/9) | Added runner-path regressions for **`bidder_onboarding`** and **`dap_report`** that verify execution reaches and routes through **`Gateway_SAM_Decision`** / **`Gateway_1`** with active `currentVersion` BPMN assets; diagnostic tests now assert the historical no-match/no-default gateway error does not recur. |
| **Branch fix (import)** | **`dap_report`:** load `agent_runner` via `importlib` from repo-relative path so `import agent_ui.agent_runner` is not shadowed when `sys.path` includes `agent_ui/` (`workflows/dap_report/workflow.py`). |

---

**Status:** **Hosted §3** is **not filled** — automation was **blocked** by missing deployment URL/credentials (see §3.0). **§4** local history remains useful for developers but **does not** close Phase 1. After an operator completes **§3**, update [BPMN_CONSOLIDATION_TODOS.md](../architecture/BPMN_CONSOLIDATION_TODOS.md).
