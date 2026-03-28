"""Pydantic models for the Admissions System API.

Defines four categories of schemas:
- Config entities: FlowStep and Task (loaded from flow.json at startup)
- Runtime entities: User and UserTaskStatus (per-user mutable state)
- Request schemas: incoming API request bodies
- Response schemas: outgoing API response bodies
"""

from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


# ---------------------------------------------------------------------------
# Config entities (loaded from flow.json, shared across all users)
# ---------------------------------------------------------------------------

class Task(BaseModel):
    """A single task within a flow step.

    Attributes:
        id: Unique task identifier (e.g. "iq_test").
        step_id: ID of the parent FlowStep this task belongs to.
        name: Human-readable display name.
        order: Position within the step (1-indexed).
        pass_condition: Evaluator key used to determine pass/fail
                        (e.g. "always", "score_gt_75", "decision_passed").
        conditional: If True, this task is hidden by default and only
                     unlocked for specific users based on unlock_when.
        unlock_when: Condition key evaluated to decide whether to unlock
                     this conditional task (e.g. "score_between_60_75").
    """
    id: str
    step_id: str
    name: str
    order: int
    pass_condition: str
    conditional: bool = False
    unlock_when: str | None = None


class FlowStep(BaseModel):
    """A step in the admissions flow, containing one or more tasks.

    Attributes:
        id: Unique step identifier (e.g. "interview").
        name: Human-readable display name.
        order: Position in the overall flow (1-indexed).
        tasks: Ordered list of tasks within this step.
    """
    id: str
    name: str
    order: int
    tasks: list[Task] = Field(min_length=1)


# ---------------------------------------------------------------------------
# Runtime entities (per-user mutable state)
# ---------------------------------------------------------------------------

class User(BaseModel):
    """A registered user progressing through the admissions flow.

    Attributes:
        id: Unique user ID (UUID).
        email: User's email address (must be unique).
        status: Current admission status — "in_progress", "accepted", or "rejected".
        created_at: Timestamp of user creation.
    """
    id: str
    email: str
    status: str = "in_progress"
    created_at: datetime


class UserTaskStatus(BaseModel):
    """Tracks a user's state for a specific task.

    Attributes:
        user_id: ID of the user.
        task_id: ID of the task.
        state: Current state — "pending", "passed", or "failed".
        completed_at: Timestamp when the task was completed (None if pending).
    """
    user_id: str
    task_id: str
    state: str = "pending"
    completed_at: datetime | None = None


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class CreateUserRequest(BaseModel):
    """Request body for POST /users."""
    email: EmailStr


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class CreateUserResponse(BaseModel):
    """Response body for POST /users."""
    user_id: str


class TaskInfoResponse(BaseModel):
    """Task representation used in API responses."""
    id: str
    name: str
    order: int


class StepInfoResponse(BaseModel):
    """Step representation for GET /flow, including its tasks."""
    id: str
    name: str
    order: int
    tasks: list[TaskInfoResponse] = []


class FlowResponse(BaseModel):
    """Response body for GET /flow."""
    total_steps: int
    steps: list[StepInfoResponse]


class StepSummary(BaseModel):
    """Step representation used in progress responses."""
    id: str
    name: str
    order: int


class ProgressResponse(BaseModel):
    """Response body for GET /users/{id}/progress.

    Attributes:
        current_step: The first step not yet fully passed (None if all complete).
        current_task: The first pending task in the current step (None if all complete).
        completed_steps: List of step IDs that are fully passed.
        step_number: 1-indexed position of the current step in the flow.
        total_steps: Total number of steps in the flow.
    """
    current_step: StepSummary | None
    current_task: TaskInfoResponse | None
    completed_steps: list[str]
    step_number: int
    total_steps: int


class OutcomeResponse(BaseModel):
    """Response body for GET /users/{id}/outcome."""
    status: str


class TaskCompletionResponse(BaseModel):
    """Response body for PUT /users/{id}/tasks/{task_id}."""
    task_state: str
