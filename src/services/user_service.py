"""User service — creation, progress resolution, and outcome retrieval.

Handles all user-scoped business logic: registering new users,
computing where a user stands in the admissions flow, and returning
their final admission status.
"""

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException

from src.db.store import store
from src.models.schemas import User, UserTaskStatus
from src.services.flow_service import get_steps_in_order, get_tasks_for_step


def create_user(email: str) -> str:
    """Register a new user and initialize their task statuses.

    Creates a User with status "in_progress" and a pending
    UserTaskStatus for every non-conditional task in the flow.

    Args:
        email: The user's email address (must be unique).

    Returns:
        The newly generated user ID (UUID string).

    Raises:
        HTTPException 409: If the email is already registered.
    """
    for user in store.users.values():
        if user.email == email:
            raise HTTPException(status_code=409, detail="Email already exists")

    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        email=email,
        status="in_progress",
        created_at=datetime.now(timezone.utc),
    )
    store.users[user_id] = user

    for step in get_steps_in_order():
        for task in get_tasks_for_step(step.id):
            if not task.conditional:
                status = UserTaskStatus(user_id=user_id, task_id=task.id)
                store.user_task_statuses[(user_id, task.id)] = status

    return user_id


def get_user(user_id: str) -> User:
    """Look up a user by ID.

    Raises:
        HTTPException 404: If the user does not exist.
    """
    user = store.users.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def get_user_progress(user_id: str) -> dict:
    """Compute the user's current position in the admissions flow.

    Walks steps in order. The current step is the first step that has
    at least one relevant pending task.
    A task is relevant if a UserTaskStatus entry exists for it.

    Returns a dict with keys: current_step, current_task,
    completed_steps, step_number, total_steps.

    Raises:
        HTTPException 404: If the user does not exist.
    """
    get_user(user_id)

    steps = get_steps_in_order()
    completed_steps: list[str] = []
    current_step = None
    current_task = None

    for step in steps:
        tasks = get_tasks_for_step(step.id)
        relevant_tasks = [
            t for t in tasks if (user_id, t.id) in store.user_task_statuses
        ]

        all_passed = True
        for task in relevant_tasks:
            status = store.user_task_statuses.get((user_id, task.id))
            if status.state != "passed":
                all_passed = False
                if current_step is None:
                    current_step = step
                    current_task = task
                break

        if all_passed:
            completed_steps.append(step.id)

    total_steps = len(steps)
    step_number = len(completed_steps) + 1 if current_step else total_steps

    return {
        "current_step": current_step,
        "current_task": current_task,
        "completed_steps": completed_steps,
        "step_number": step_number,
        "total_steps": total_steps,
    }


def get_user_flow(user_id: str) -> list[dict]:
    """Build a personalized flow for the user, including unlocked conditional tasks.

    Returns a list of step dicts, each containing the step info and a list
    of tasks relevant to this user with their current state.

    Raises:
        HTTPException 404: If the user does not exist.
    """
    get_user(user_id)

    result = []
    for step in get_steps_in_order():
        tasks = []
        for task in get_tasks_for_step(step.id):
            status = store.user_task_statuses.get((user_id, task.id))
            if not status:
                continue
            tasks.append({
                "id": task.id,
                "name": task.name,
                "order": task.order,
                "state": status.state,
            })
        result.append({
            "id": step.id,
            "name": step.name,
            "order": step.order,
            "tasks": tasks,
        })

    return result


def get_user_outcome(user_id: str) -> str:
    """Return the user's admission status ("in_progress", "accepted", or "rejected").

    Raises:
        HTTPException 404: If the user does not exist.
    """
    user = get_user(user_id)
    return user.status
