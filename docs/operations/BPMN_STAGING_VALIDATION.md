# BPMN real-environment validation (Issue #7)

This document records **how** to validate BPMN-only workflow execution and **where** to capture evidence. It complements [BPMN_RUN_OPERATORS.md](./BPMN_RUN_OPERATORS.md) (expected run-detail semantics).

**Important:** Anything below that uses the Django **test** database or local-only commands is **partial evidence** for Issue #7. It **does not** replace **hosted staging or production** validation. Phase 1 in [BPMN_CONSOLIDATION_TODOS.md](../architecture/BPMN_CONSOLIDATION_TODOS.md) stays **open** until real deployment runs are recorded.

## 1. Preconditions (record per exercise)

| Field | Value (fill when validating) |
|-------|------------------------------|
| **Environment** | Example below: **local** Django test DB only — **not** staging/production. |
| **Date** | 2026-03-23 |
| **Operator** | Cursor agent (automated) |
| **App version / commit** | See git history on branch `chore/7-bpmn-staging-validation`. |

**Catalog-visible BPMN workflows** (default registry list; `hide_from_catalog` workflows are excluded from the Workflows UI):

| Workflow ID | Notes / data prerequisites |
|-------------|----------------------------|
| `bidder_onboarding` | Inputs: `bidder_name`, `property_id`, `registration_data` with `email`, `phone`, `terms_accepted`, `age_accepted`. |
| `property_due_diligence` | Requires a valid `property_id` for your environment’s data sources. |
| `bi_weekly_report` | Requires `start_date` and `end_date` (report window); uses portfolio/agents as configured. |
| `dap_report` | Requires `report_date`; optional `lookback_days`. GRES / agent stack affects retrieval path. |

Confirm each workflow appears under **Workflows** in the UI before treating the environment as ready.

**Hosted staging/production:** Re-run section 3 against your deployed host when credentials are ready; paste run IDs and outcomes here or in a follow-up PR. That step is required to **complete** Phase 1 in the consolidation TODOs.

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
- **`bidder_onboarding`** and **`dap_report`:** **observability only** — terminal status may be `failed` (known BPMN gateway issues; [issue #9](https://github.com/cappelaere/beeai/issues/9)).

```bash
cd agent_ui && ISSUE7_PRODUCT_BPMN_DIAGNOSTIC=1 ../venv/bin/python manage.py test \
  agent_app.tests.test_issue7_product_bpmn_diagnostic --settings=agent_ui.settings -v 2
```

Coverage highlights (see `test_workflow_runner_integration.py` for full list):

- **`runner_integration_test`** — pause for human task, resume, completed steps, failure / retry metadata.
- **`runner_parallel_fj_test`** — parallel fork/join completion, pause before join + resume, pending joins, branch failure, cancel, timeout scenarios.
- **`par015_message_runner`** — intermediate message catch + resume.

## 3. Partial matrix (local test DB — not staging/production)

This matrix records **one local test-DB exercise** (2026-03-23): `execute_workflow_run` (not the WebSocket entrypoint). Run-detail was checked with `GET /workflows/runs/<run_id>/` (anonymous session user id 9): **200** and BPMN markers in HTML.

**Do not** treat this table as proof that Issue #7 staging acceptance criteria are met.

### 3.1 Completion (happy path)

| Workflow ID | Run ID | Pass / Fail / Skip | Notes |
|-------------|--------|--------------------|-------|
| `dap_report` | `121edda3` | **Fail** | Failed at exclusive gateway `Gateway_1` after GRES step (see §5 / issue #9). |
| `bi_weekly_report` | `f8d08b78` | **Pass** | **Completed** on test DB only. |
| `property_due_diligence` | `9bcc0d48` | **Pass** | **Completed** on test DB only. |
| `bidder_onboarding` | `494034f4` | **Fail** | Failed at `Gateway_SAM_Decision` (issue #9). |

### 3.2 Pause / resume

| Workflow ID | Run ID | Pass / Fail / Skip | Notes |
|-------------|--------|--------------------|-------|
| `runner_integration_test` | (see logs) | **Pass** | `test_workflow_runner_integration` — `waiting_for_task`, resume, completion. |
| `runner_parallel_fj_test` | (see logs) | **Pass** | Pause before join + resume in same suite. |

Product workflows in the local pass did not reach **waiting_for_task** for manual pause testing; repeat on staging if required.

### 3.3 Run-detail UI (progress, current / completed nodes)

| Workflow ID | Run ID | Pass / Fail / Skip | Notes |
|-------------|--------|--------------------|-------|
| `dap_report` | `121edda3` | **Pass** | Failed run still rendered BPMN markers (local). |
| `bi_weekly_report` | `f8d08b78` | **Pass** | Completed run; BPMN markers (local). |
| `property_due_diligence` | `9bcc0d48` | **Pass** | Completed run; BPMN markers (local). |
| `bidder_onboarding` | `494034f4` | **Pass** | Failed run; BPMN markers (local). |

### 3.4 Failure presentation (controlled)

| Workflow ID | Run ID | Pass / Fail / Skip | Notes |
|-------------|--------|--------------------|-------|
| `bidder_onboarding` | `494034f4` | **Pass** | Failed run + run-detail (local). |
| `dap_report` | `121edda3` | **Pass** | Failed run + run-detail (local). |

## 4. Parallel fork / join (UI vs automated)

**Repository fact:** The only committed BPMN with parallel gateways is **`runner_parallel_fj_test`**, which sets `hide_from_catalog: true`.

| Method | Environment | Run ID | Pass / Fail / Skip | Notes |
|--------|-------------|--------|--------------------|-------|
| Integration tests | Django test DB | N/A | **Pass** | `test_workflow_runner_integration` — fork/join, pending joins, failures, cancel, timeout. |
| Product parallel research | Django test DB | `9bcc0d48` | **Pass** | `property_due_diligence` handler parallelism; not the same as BPMN parallel gateway tokens. |
| Live UI (`runner_parallel_fj_test`) | — | — | **Skip** | Hidden from catalog; use API or temporary catalog flag on staging if UI proof is required. |

## 5. Bugs and follow-ups

| Issue | Summary |
|-------|---------|
| [#9](https://github.com/cappelaere/beeai/issues/9) | **`bidder_onboarding` / `dap_report`:** Exclusive gateways **`Gateway_SAM_Decision`** and **`Gateway_1`** — no matching condition / default after handler transitions (example run IDs `494034f4`, `121edda3` on test DB). |
| **Branch fix (import)** | **`dap_report`:** load `agent_runner` via `importlib` from repo-relative path so `import agent_ui.agent_runner` is not shadowed when `sys.path` includes `agent_ui/` (`workflows/dap_report/workflow.py`). |

---

**Status:** Local notes and diagnostics are **useful but incomplete** for Issue #7. **Hosted** staging/production matrices are still required to close Phase 1 in [BPMN_CONSOLIDATION_TODOS.md](../architecture/BPMN_CONSOLIDATION_TODOS.md).
