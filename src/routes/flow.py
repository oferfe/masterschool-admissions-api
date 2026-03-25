"""Flow route — returns the admissions flow definition."""

from fastapi import APIRouter

from src.models.schemas import FlowResponse, StepInfoResponse, TaskInfoResponse
from src.services.flow_service import get_flow

router = APIRouter()


@router.get("/flow", response_model=FlowResponse)
def get_flow_definition():
    """Return the full flow definition, excluding conditional tasks."""
    steps = get_flow()

    step_responses = []
    for step in steps:
        tasks = [
            TaskInfoResponse(id=t.id, name=t.name, order=t.order)
            for t in step.tasks
            if not t.conditional
        ]
        step_responses.append(
            StepInfoResponse(id=step.id, name=step.name, order=step.order, tasks=tasks)
        )

    return FlowResponse(total_steps=len(step_responses), steps=step_responses)
