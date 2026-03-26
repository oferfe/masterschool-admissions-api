"""Tests for src/models/schemas.py — Pydantic model validation and defaults."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from src.models.schemas import (
    Task,
    FlowStep,
    User,
    UserTaskStatus,
    CreateUserRequest,
    CreateUserResponse,
    FlowResponse,
    StepInfoResponse,
    TaskInfoResponse,
    ProgressResponse,
    StepSummary,
    OutcomeResponse,
    TaskCompletionResponse,
)


# ---------------------------------------------------------------------------
# Config entities
# ---------------------------------------------------------------------------

class TestTask:
    def test_required_fields(self):
        """Task accepts all required fields and stores them correctly."""
        task = Task(id="t1", name="Test Task", order=1, pass_condition="always")
        assert task.id == "t1"
        assert task.name == "Test Task"
        assert task.order == 1
        assert task.pass_condition == "always"

    def test_defaults(self):
        """Optional fields default to step_id='', conditional=False, unlock_when=None."""
        task = Task(id="t1", name="Test Task", order=1, pass_condition="always")
        assert task.step_id == ""
        assert task.conditional is False
        assert task.unlock_when is None

    def test_missing_required_field_raises(self):
        """Omitting pass_condition (required) raises ValidationError."""
        with pytest.raises(ValidationError):
            Task(id="t1", name="Test Task", order=1)


class TestFlowStep:
    def test_required_fields(self):
        """FlowStep accepts required fields and stores them correctly."""
        step = FlowStep(id="s1", name="Step One", order=1)
        assert step.id == "s1"
        assert step.name == "Step One"
        assert step.order == 1

    def test_default_tasks_empty(self):
        """Tasks list defaults to empty when not provided."""
        step = FlowStep(id="s1", name="Step One", order=1)
        assert step.tasks == []

    def test_with_tasks(self):
        """FlowStep can hold nested Task instances."""
        task = Task(id="t1", name="Task", order=1, pass_condition="always")
        step = FlowStep(id="s1", name="Step", order=1, tasks=[task])
        assert len(step.tasks) == 1
        assert step.tasks[0].id == "t1"


# ---------------------------------------------------------------------------
# Runtime entities
# ---------------------------------------------------------------------------

class TestUser:
    def test_required_fields(self):
        """User accepts required fields and stores them correctly."""
        now = datetime.now(timezone.utc)
        user = User(id="u1", email="a@b.com", created_at=now)
        assert user.id == "u1"
        assert user.email == "a@b.com"
        assert user.created_at == now

    def test_default_status(self):
        """User status defaults to 'in_progress'."""
        user = User(id="u1", email="a@b.com", created_at=datetime.now(timezone.utc))
        assert user.status == "in_progress"

    def test_missing_required_field_raises(self):
        """Omitting created_at (required) raises ValidationError."""
        with pytest.raises(ValidationError):
            User(id="u1", email="a@b.com")


class TestUserTaskStatus:
    def test_required_fields(self):
        """UserTaskStatus accepts required fields and stores them correctly."""
        status = UserTaskStatus(user_id="u1", task_id="t1")
        assert status.user_id == "u1"
        assert status.task_id == "t1"

    def test_defaults(self):
        """State defaults to 'pending' and completed_at defaults to None."""
        status = UserTaskStatus(user_id="u1", task_id="t1")
        assert status.state == "pending"
        assert status.completed_at is None

    def test_with_completed_at(self):
        """UserTaskStatus can be created with explicit state and timestamp."""
        now = datetime.now(timezone.utc)
        status = UserTaskStatus(user_id="u1", task_id="t1", state="passed", completed_at=now)
        assert status.state == "passed"
        assert status.completed_at == now


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class TestCreateUserRequest:
    def test_valid(self):
        """CreateUserRequest accepts a valid email."""
        req = CreateUserRequest(email="test@example.com")
        assert req.email == "test@example.com"

    def test_missing_email_raises(self):
        """Omitting email raises ValidationError."""
        with pytest.raises(ValidationError):
            CreateUserRequest()


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class TestCreateUserResponse:
    def test_valid(self):
        """CreateUserResponse stores the user_id."""
        resp = CreateUserResponse(user_id="abc123")
        assert resp.user_id == "abc123"


class TestFlowResponse:
    def test_valid(self):
        """FlowResponse holds total_steps and a list of step responses."""
        step = StepInfoResponse(id="s1", name="Step", order=1, tasks=[])
        resp = FlowResponse(total_steps=1, steps=[step])
        assert resp.total_steps == 1
        assert len(resp.steps) == 1


class TestProgressResponse:
    def test_with_current_step(self):
        """ProgressResponse with an active current step and task."""
        resp = ProgressResponse(
            current_step=StepSummary(id="s1", name="Step", order=1),
            current_task=TaskInfoResponse(id="t1", name="Task", order=1),
            completed_steps=[],
            step_number=1,
            total_steps=6,
        )
        assert resp.current_step.id == "s1"
        assert resp.current_task.id == "t1"

    def test_all_complete(self):
        """ProgressResponse when all steps are complete (nulls for current)."""
        resp = ProgressResponse(
            current_step=None,
            current_task=None,
            completed_steps=["s1", "s2"],
            step_number=2,
            total_steps=2,
        )
        assert resp.current_step is None
        assert resp.current_task is None


class TestOutcomeResponse:
    def test_valid(self):
        """OutcomeResponse stores the admission status string."""
        resp = OutcomeResponse(status="in_progress")
        assert resp.status == "in_progress"


class TestTaskCompletionResponse:
    def test_valid(self):
        """TaskCompletionResponse stores the task state string."""
        resp = TaskCompletionResponse(task_state="passed")
        assert resp.task_state == "passed"
