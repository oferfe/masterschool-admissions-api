"""Task routes — webhook handler for task completion."""

from typing import Optional

from fastapi import APIRouter, Body
from src.models.schemas import TaskCompletionResponse
from src.services.task_service import complete_task

router = APIRouter()


@router.put("/users/{user_id}/tasks/{task_id}", response_model=TaskCompletionResponse)
async def put_complete_task(
    user_id: str,
    task_id: str,
    payload: Optional[dict] = Body(default=None),
):
    """Mark a task as complete. Acts as the incoming webhook handler.

    The request body is the raw task payload (varies per task type)
    and is passed directly to the pass condition evaluator.
    An empty body is accepted for tasks with an "always" pass condition.

    Example payloads:
        Personal details: {"first_name": "A", "last_name": "B", "email": "a@b.com", "timestamp": "..."}
        IQ test:          {"test_id": "t1", "score": 80, "timestamp": "..."}
        Interview:        {"interview_date": "...", "interviewer_id": "i1", "decision": "passed_interview"}
        Payment:          {"payment_id": "p1", "timestamp": "..."}
    """
    if payload is None:
        payload = {}
    task_state = complete_task(user_id, task_id, payload)
    return TaskCompletionResponse(task_state=task_state)
