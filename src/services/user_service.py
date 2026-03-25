import uuid
from datetime import datetime, timezone

from fastapi import HTTPException

from src.db.store import store
from src.models.schemas import User, UserTaskStatus
from src.services.flow_service import get_steps_in_order, get_tasks_for_step


def create_user(email: str) -> str:
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
    user = store.users.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def get_user_progress(user_id: str) -> dict:
    user = get_user(user_id)

    steps = get_steps_in_order()
    completed_steps: list[str] = []
    current_step = None
    current_task = None

    for step in steps:
        tasks = get_tasks_for_step(step.id)
        non_conditional_tasks = [t for t in tasks if not t.conditional]

        all_passed = True
        for task in non_conditional_tasks:
            status = store.user_task_statuses.get((user_id, task.id))
            if not status or status.state != "passed":
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


def get_user_outcome(user_id: str) -> str:
    user = get_user(user_id)
    return user.status
