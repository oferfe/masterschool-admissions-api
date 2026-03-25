from datetime import datetime, timezone

from fastapi import HTTPException

from src.db.store import store
from src.models.schemas import UserTaskStatus
from src.evaluators.pass_condition import evaluate
from src.evaluators.unlock_condition import should_unlock
from src.services.user_service import get_user
from src.services.flow_service import get_steps_in_order, get_tasks_for_step


def complete_task(user_id: str, task_id: str, payload: dict) -> str:
    user = get_user(user_id)

    task = store.tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if user.status == "rejected":
        raise HTTPException(status_code=400, detail="User has been rejected")

    status_key = (user_id, task_id)
    task_status = store.user_task_statuses.get(status_key)

    if not task_status:
        raise HTTPException(status_code=400, detail="Task not available for this user")

    if task_status.state == "passed":
        return task_status.state

    result = evaluate(task.pass_condition, payload)
    now = datetime.now(timezone.utc)

    task_status.state = result
    task_status.completed_at = now

    if result == "failed":
        user.status = "rejected"
        return result

    _try_unlock_conditional_tasks(user_id, payload)

    if _all_required_tasks_passed(user_id):
        user.status = "accepted"

    return result


def _try_unlock_conditional_tasks(user_id: str, payload: dict) -> None:
    for step in get_steps_in_order():
        for task in get_tasks_for_step(step.id):
            if not task.conditional or not task.unlock_when:
                continue
            if (user_id, task.id) in store.user_task_statuses:
                continue
            try:
                if should_unlock(task.unlock_when, payload):
                    status = UserTaskStatus(user_id=user_id, task_id=task.id)
                    store.user_task_statuses[(user_id, task.id)] = status
            except ValueError:
                continue


def _all_required_tasks_passed(user_id: str) -> bool:
    for step in get_steps_in_order():
        for task in get_tasks_for_step(step.id):
            if task.conditional:
                status = store.user_task_statuses.get((user_id, task.id))
                if not status:
                    continue
            status = store.user_task_statuses.get((user_id, task.id))
            if not status or status.state != "passed":
                return False
    return True
