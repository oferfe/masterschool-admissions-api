"""Task service — the core state machine driver for task completion.

Handles the PUT /users/{id}/tasks/{task_id} webhook: evaluates the
payload against the task's pass condition, updates user/task state,
unlocks conditional tasks when applicable, and determines whether the
user has been accepted or rejected.
"""

from datetime import datetime, timezone

from fastapi import HTTPException

from src.db.store import store
from src.models.schemas import UserTaskStatus
from src.evaluators.pass_condition import evaluate
from src.evaluators.unlock_condition import should_unlock
from src.services.user_service import get_user
from src.services.flow_service import get_steps_in_order, get_tasks_for_step


def complete_task(user_id: str, task_id: str, payload: dict) -> str:
    """Process a task completion webhook.

    Steps:
        1. Validate user exists and is not rejected.
        2. Validate task exists and is available for the user.
        3. If already passed, return passed.
        4. Evaluate pass condition against the payload.
        5. Try to unlock any conditional tasks whose conditions are met.
        6. On failure: reject the user only if no conditional task was
           unlocked (i.e., no second-chance path is available).
        7. On success: check if all tasks are passed (→ accepted).

    Args:
        user_id: The user completing the task.
        task_id: The task being completed.
        payload: The raw webhook payload (varies per task).

    Returns:
        The resulting task state: "passed" or "failed".

    Raises:
        HTTPException 404: User or task not found.
        HTTPException 400: User is rejected, or task not available.
    """
    user = get_user(user_id)

    if user.status == "rejected":
        raise HTTPException(status_code=400, detail="User has been rejected")

    task = store.tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

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

    unlocked = _try_unlock_conditional_tasks(user_id, payload)

    if result == "failed":
        if not unlocked:
            user.status = "rejected"
        return result

    if _all_required_tasks_passed(user_id):
        user.status = "accepted"

    return result


def _try_unlock_conditional_tasks(user_id: str, payload: dict) -> bool:
    """Scan all conditional tasks and unlock any whose condition is met.

    Skips tasks that are already unlocked or whose unlock_when condition
    is not recognised (future-proofing).

    Returns True if at least one conditional task was unlocked.
    """
    unlocked = False
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
                    unlocked = True
            except ValueError:
                continue
    return unlocked


def _all_required_tasks_passed(user_id: str) -> bool:
    """Check whether every task assigned to the user is in "passed" state.

    Conditional tasks that were never unlocked are skipped (they are
    not required). Unlocked conditional tasks must also be passed.
    """
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
