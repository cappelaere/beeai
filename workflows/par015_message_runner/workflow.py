"""PAR-015 message catch — runner integration test."""

from pydantic import BaseModel, Field


class Par015MessageRunnerState(BaseModel):
    workflow_steps: list[str] = Field(default_factory=list)


class Par015MessageRunnerWorkflow:
    def __init__(self, run_id: str | None = None):
        self.run_id = run_id

    async def task_msg_a(self, state: Par015MessageRunnerState) -> None:
        return None

    async def task_msg_b(self, state: Par015MessageRunnerState) -> None:
        return None
