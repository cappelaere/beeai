# BPMN engine – consolidation TODOs

**Decision: BPMN-only.** Execution is BPMN-only: workflows must provide `workflow.bpmn` and `bpmn-bindings.yaml` (and a state class) to run. The runner and consumers use only the BPMN engine; there is no legacy `executor.run()` path. Workflows that are not BPMN-ready fail with a clear error.

**Goal:** Keep **only one way** of executing flows (BPMN-driven) and simplify workflow code by removing the legacy Python step chain.

See **[BPMN_ENGINE_REVIEW.md](./BPMN_ENGINE_REVIEW.md)** §6 for current-state review and **[BPMN_V2_PLAN.md](./BPMN_V2_PLAN.md)** for the proposed v2 design.

---

## Phase 1: Validate engine

- [ ] Run BPMN-ready workflows (e.g. bi_weekly_report) in **production/staging**; confirm completion, pause/resume, run-detail UI  
  - **Issue #7 — partial only:** [BPMN_STAGING_VALIDATION.md](../operations/BPMN_STAGING_VALIDATION.md) holds **local** notes (Django **test** DB, `execute_workflow_run`, optional diagnostic tests). That is **not** hosted staging/production validation and **does not** close this checkbox. Runner integration tests (`test_workflow_runner_integration`, 17 tests) cover engine mechanics, not deploy sign-off.
- [ ] Fix any engine or runner bugs found — **open:** [issue #9](https://github.com/cappelaere/beeai/issues/9) (product BPMN exclusive-gateway routing for `bidder_onboarding` / `dap_report`); `dap_report` agent import path hardening on branch
- [x] Document “BPMN-engine-ready workflow” contract in developer guide ([workflows/docs/DEVELOPER_GUIDE.md](../../workflows/docs/DEVELOPER_GUIDE.md) — BPMN-ready workflow contract)

## Phase 2: Migrate workflows to BPMN-only

- [x] **dap_report** – BPMN-ready; `DAPReportState`, handlers `retrieve_data`, `create_time_series`, `create_analysis`; `run()` removed
- [x] **bi_weekly_report** – BPMN-only; no `run()`, no step-order constant
- [x] **property_due_diligence** – BPMN-only; no `run()`
- [x] **bidder_onboarding** – BPMN-only; no `run()`

## Phase 3: Single execution path

- [x] **Single execution path** – Legacy branch removed; runner and consumers use BPMN engine only. Non–BPMN-ready workflows fail with a clear error.
- [x] **`can_run_with_bpmn_engine`** – **Kept** as a cheap readiness predicate (BPMN + bindings + state class + valid first executable). Used by the runner, consumers, and tools for fail-fast messaging; it does not enable a non-BPMN fallback. Documented on the function in `bpmn_engine.py`.
- [x] **Workflow modules** – No Flo `Workflow` / `add_step`; no legacy `run()` in dap_report, bi_weekly_report, property_due_diligence, bidder_onboarding
- [x] **Tests and docs** – Describe BPMN-only execution and supported subset; consolidation cleanup (issue #1). Ongoing: keep architecture docs aligned when engine behavior changes.
