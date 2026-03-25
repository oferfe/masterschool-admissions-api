"""Task routes — webhook handler for task completion."""

from fastapi import APIRouter, Request

from src.models.schemas import TaskCompletionResponse
from src.services.task_service import complete_task

router = APIRouter()


@router.put("/users/{user_id}/tasks/{task_id}", response_model=TaskCompletionResponse)
async def put_complete_task(user_id: str, task_id: str, request: Request):
    """Mark a task as complete. Acts as the incoming webhook handler.

    The request body is the raw task payload (varies per task type)
    and is passed directly to the pass condition evaluator.
    """
    payload = await request.json()
    task_state = complete_task(user_id, task_id, payload)
    return TaskCompletionResponse(task_state=task_state)
