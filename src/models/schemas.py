from datetime import datetime
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Config entities (loaded from flow.json, shared across all users)
# ---------------------------------------------------------------------------

class Task(BaseModel):
    id: str
    step_id: str = ""
    name: str
    order: int
    pass_condition: str
    conditional: bool = False
    unlock_when: str | None = None


class FlowStep(BaseModel):
    id: str
    name: str
    order: int
    tasks: list[Task] = []


# ---------------------------------------------------------------------------
# Runtime entities (per-user mutable state)
# ---------------------------------------------------------------------------

class User(BaseModel):
    id: str
    email: str
    status: str = "in_progress"
    created_at: datetime


class UserTaskStatus(BaseModel):
    user_id: str
    task_id: str
    state: str = "pending"
    completed_at: datetime | None = None


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class CreateUserRequest(BaseModel):
    email: str


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class CreateUserResponse(BaseModel):
    user_id: str


class TaskInfoResponse(BaseModel):
    id: str
    name: str
    order: int


class StepInfoResponse(BaseModel):
    id: str
    name: str
    order: int
    tasks: list[TaskInfoResponse] = []


class FlowResponse(BaseModel):
    total_steps: int
    steps: list[StepInfoResponse]


class StepSummary(BaseModel):
    id: str
    name: str
    order: int


class ProgressResponse(BaseModel):
    current_step: StepSummary | None
    current_task: TaskInfoResponse | None
    completed_steps: list[str]
    step_number: int
    total_steps: int


class OutcomeResponse(BaseModel):
    status: str


class TaskCompletionResponse(BaseModel):
    task_state: str
