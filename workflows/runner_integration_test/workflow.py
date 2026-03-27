"""Minimal workflow for BPMN runner integration tests (pause/resume/failure)."""

from pydantic import BaseModel, ConfigDict, Field

from agent_app.task_service import BpmnRetryableTaskError, TaskPendingError


class RunnerIntegrationTestState(BaseModel):
    model_config = ConfigDict(extra="ignore")

    workflow_steps: list[str] = Field(default_factory=list)
    human_review_result: dict | None = None
    retry_resume_test: bool = False
    task_b_rr_invocations: int = 0


class RunnerIntegrationTestWorkflow:
    def __init__(self, run_id: str | None = None):
        self.run_id = run_id

    async def task_a(self, state: RunnerIntegrationTestState) -> None:
        if state.retry_resume_test:
            return None
        raise TaskPendingError("hitask1", "human_task", state, "task_b")

    async def task_b(self, state: RunnerIntegrationTestState) -> None:
        if state.retry_resume_test:
            n = state.task_b_rr_invocations
            if n == 0:
                state.task_b_rr_invocations = 1
                raise BpmnRetryableTaskError("transient_b")
            if n == 1:
                state.task_b_rr_invocations = 2
                raise TaskPendingError("hitask_rr", "human_task", state, "task_b")
            return None
        return None
