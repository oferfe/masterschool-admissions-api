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
    payload: Optional[dict] = Body(
        default=None,
        openapi_examples={
            "personal_details": {
                "summary": "Personal Details Form",
                "description": "Step 1 — submit personal information.",
                "value": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john.doe@example.com",
                    "timestamp": "2026-03-27T12:00:00Z",
                },
            },
            "iq_test": {
                "summary": "IQ Test",
                "description": "Step 2a — submit test results. Passed when score > 75. if score between 60 and 75, the user can retake the test.",
                "value": {
                    "test_id": "t1",
                    "score": 80,
                    "timestamp": "2026-03-27T12:00:00Z",
                },
            },
            "schedule_interview": {
                "summary": "Schedule Interview",
                "description": "Step 3a — schedule an interview date.",
                "value": {
                    "interview_date": "2026-04-15",
                },
            },
            "perform_interview": {
                "summary": "Perform Interview (decision = 'passed_interview' to pass)",
                "description": "Step 3b — submit interview result. Passed when decision is 'passed_interview'.",
                "value": {
                    "interview_date": "2026-04-15",
                    "interviewer_id": "i1",
                    "decision": "passed_interview",
                },
            },
            "upload_id": {
                "summary": "Upload Identification Document",
                "description": "Step 4a — upload passport or ID.",
                "value": {
                    "passport_number": "AB1234567",
                    "timestamp": "2026-03-27T12:00:00Z",
                },
            },
            "sign_contract": {
                "summary": "Sign Contract",
                "description": "Step 4b — sign the admission contract.",
                "value": {
                    "timestamp": "2026-03-27T12:00:00Z",
                },
            },
            "payment": {
                "summary": "Payment",
                "description": "Step 5 — submit payment confirmation.",
                "value": {
                    "payment_id": "p1",
                    "timestamp": "2026-03-27T12:00:00Z",
                },
            },
            "join_slack": {
                "summary": "Join Slack",
                "description": "Step 6 — confirm Slack workspace membership.",
                "value": {
                    "email": "john.doe@example.com",
                    "timestamp": "2026-03-27T12:00:00Z",
                },
            },
        },
    ),
):
    """Mark a task as complete. Acts as the incoming webhook handler.

    The request body varies per task type — use the example dropdown
    in Swagger UI to see the expected payload for each task.
    """
    if payload is None:
        payload = {}
    task_state = complete_task(user_id, task_id, payload)
    return TaskCompletionResponse(task_state=task_state)
