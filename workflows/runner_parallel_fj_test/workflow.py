"""Fork/join BPMN workflow for runner integration tests (pause / failure flags)."""

from pydantic import BaseModel, Field

from agent_app.task_service import TaskPendingException


class RunnerParallelFjState(BaseModel):
    workflow_steps: list[str] = Field(default_factory=list)
    pause_on_task_b: bool = False
    fail_branch_b: bool = False


class RunnerParallelFjTestWorkflow:
    """Registry naming: runner_parallel_fj_test → RunnerParallelFjTestWorkflow."""

    def __init__(self, run_id: str | None = None):
        self.run_id = run_id

    async def task0(self, state: RunnerParallelFjState) -> None:
        state.workflow_steps.append("task0")

    async def task_a(self, state: RunnerParallelFjState) -> None:
        state.workflow_steps.append("taskA")

    async def task_b(self, state: RunnerParallelFjState) -> None:
        if state.fail_branch_b:
            raise RuntimeError("branch_b_failed")
        if state.pause_on_task_b:
            raise TaskPendingException("pause_b", "human_task", state, "taskB")
        state.workflow_steps.append("taskB")

    async def task_after(self, state: RunnerParallelFjState) -> None:
        state.workflow_steps.append("taskAfter")
