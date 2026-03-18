# BPMN workflow runs — operator guide

How to read run status, **run detail**, and **task detail** for BPMN-driven workflows (not legacy step-list workflows).

## Run statuses

| Status | Meaning |
|--------|---------|
| **Running** | Engine is executing service tasks; may show multiple active diagram nodes in parallel. |
| **Waiting for task** | Paused for human input (`TaskPendingException`); resume continues from the BPMN task id shown as “resume point”. |
| **Pending** | Run created; may be waiting to resume after a task (same progress shape as waiting in some paths). |
| **Completed** | All paths reached end events. |
| **Failed** | Engine stopped with an error (handler, gateway, join, timeout, retries exhausted, etc.). |
| **Cancelled** | Cooperative cancel (user/API); engine stopped between task attempts, not mid-handler. |

## Multi-node “current” state

Parallel forks create **several active tokens**. **Current node ids** list every BPMN element where a token sits (e.g. two branches = two task ids, or one branch at a **join** while another is still upstream). This is normal, not a bug.

## Pending joins (`pending_joins`)

When branches must meet at a **parallel join gateway**, the engine records **how many branches have arrived vs how many are expected** (e.g. `1/2`). Until all expected branches reach the join, the run may show nodes **parked at the join** on the diagram. After merge, a **single** token continues downstream (“merged path” in live UI).

## Retry vs pause vs failure

- **Retrying**: Handler raised a **retryable** error (`BpmnRetryableTaskError`). The same task is invoked again immediately (up to configured max). Live status may show **Retrying · taskId (attempt/total)**.
- **Paused for human**: Different from retry — workflow waits for a **human task**; no automatic re-invocation until the task is completed and the run is resumed.
- **Retry exhausted**: Retry budget used up; run **fails** with clear metadata (attempt count, branch id, last error).
- **Timeout / cancelled**: Checked **between** task attempts; they interrupt retry loops as well as normal progress.

## What to capture when debugging

1. **Run id** and **workflow id**.  
2. Screenshot or copy of the **BPMN run summary** / timeline on run detail (and **Raw progress snapshot** if support asks).  
3. For failures: **failure reason**, **failed node id**, **last successful node**, and any **parallel join** ids shown.  
4. For retry issues: **retry attempts** and **last error** text from the diagnostics panel.

## Where this is implemented

Run detail builds a **textual timeline** and **diagnostics panel** from persisted `progress_data` (no change to engine semantics). See [BPMN engine review](../architecture/BPMN_ENGINE_REVIEW.md) for architecture.
