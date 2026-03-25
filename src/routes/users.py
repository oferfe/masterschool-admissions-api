"""User routes — registration, progress, and outcome endpoints."""

from fastapi import APIRouter

from src.models.schemas import (
    CreateUserRequest,
    CreateUserResponse,
    OutcomeResponse,
    ProgressResponse,
    StepSummary,
    TaskInfoResponse,
)
from src.services.user_service import create_user, get_user_progress, get_user_outcome

router = APIRouter()


@router.post("/users", response_model=CreateUserResponse, status_code=201)
def post_user(request: CreateUserRequest):
    """Create a new user and initialise their admissions flow."""
    user_id = create_user(request.email)
    return CreateUserResponse(user_id=user_id)


@router.get("/users/{user_id}/progress", response_model=ProgressResponse)
def get_progress(user_id: str):
    """Return the user's current position in the admissions flow."""
    progress = get_user_progress(user_id)

    current_step = None
    if progress["current_step"]:
        step = progress["current_step"]
        current_step = StepSummary(id=step.id, name=step.name, order=step.order)

    current_task = None
    if progress["current_task"]:
        task = progress["current_task"]
        current_task = TaskInfoResponse(id=task.id, name=task.name, order=task.order)

    return ProgressResponse(
        current_step=current_step,
        current_task=current_task,
        completed_steps=progress["completed_steps"],
        step_number=progress["step_number"],
        total_steps=progress["total_steps"],
    )


@router.get("/users/{user_id}/outcome", response_model=OutcomeResponse)
def get_outcome(user_id: str):
    """Return the user's admission outcome (in_progress / accepted / rejected)."""
    status = get_user_outcome(user_id)
    return OutcomeResponse(status=status)
