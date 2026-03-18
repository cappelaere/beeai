# BPMN engine – consolidation TODOs

**Decision: BPMN-only.** Execution is BPMN-only: workflows must provide `workflow.bpmn` and `bpmn-bindings.yaml` (and a state class) to run. The runner and consumers use only the BPMN engine; there is no legacy `executor.run()` path. Workflows that are not BPMN-ready fail with a clear error.

**Goal:** Keep **only one way** of executing flows (BPMN-driven) and simplify workflow code by removing the legacy Python step chain.

See **[BPMN_ENGINE_REVIEW.md](./BPMN_ENGINE_REVIEW.md)** §6 for current-state review and **[BPMN_V2_PLAN.md](./BPMN_V2_PLAN.md)** for the proposed v2 design.

---

## Phase 1: Validate engine

- [ ] Run BPMN-ready workflows (e.g. bi_weekly_report) in production/staging; confirm completion, pause/resume, run-detail UI
- [ ] Fix any engine or runner bugs found
- [ ] Document “BPMN-engine-ready workflow” contract in developer guide

## Phase 2: Migrate workflows to BPMN-only

- [x] **dap_report** – BPMN-ready; `DAPReportState`, handlers `retrieve_data`, `create_time_series`, `create_analysis`; `run()` removed
- [x] **bi_weekly_report** – BPMN-only; no `run()`, no step-order constant
- [x] **property_due_diligence** – BPMN-only; no `run()`
- [x] **bidder_onboarding** – BPMN-only; no `run()`

## Phase 3: Single execution path

- [x] **Single execution path** – Legacy branch removed; runner and consumers use BPMN engine only. Non–BPMN-ready workflows fail with a clear error.
- [ ] Simplify or remove `can_run_with_bpmn_engine` (optional; keep for "can this run?" check; execution always requires BPMN)
- [x] **Workflow modules** – No Flo `Workflow` / `add_step`; no legacy `run()` in dap_report, bi_weekly_report, property_due_diligence, bidder_onboarding
- [ ] Update tests and docs for “one execution model: BPMN-driven”
