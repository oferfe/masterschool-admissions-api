"""Tests for src/services/task_service.py — task completion state machine.

Covers complete_task happy paths, rejection, acceptance, error cases,
conditional task unlocking, and the all-passed check.
"""

import pytest
from fastapi import HTTPException

from src.db.store import store
from src.models.schemas import UserTaskStatus
from src.services.user_service import create_user
from src.services.task_service import (
    complete_task,
    _try_unlock_conditional_tasks,
    _all_required_tasks_passed,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ALL_TASK_IDS = [
    "personal_details", "iq_test",
    "schedule_interview", "perform_interview",
    "upload_id", "sign_contract",
    "payment", "join_slack",
]

PASSING_PAYLOADS = {
    "personal_details": {},
    "iq_test": {"score": 80},
    "schedule_interview": {},
    "perform_interview": {"decision": "passed_interview"},
    "upload_id": {},
    "sign_contract": {},
    "payment": {},
    "join_slack": {},
}


# ---------------------------------------------------------------------------
# complete_task — happy paths
# ---------------------------------------------------------------------------

class TestCompleteTaskHappyPaths:
    def test_always_task_passes(self, loaded_flow):
        """Completing personal_details with empty payload returns 'passed'."""
        user_id = create_user("a@b.com")
        result = complete_task(user_id, "personal_details", {})
        assert result == "passed"

    def test_task_status_updated(self, loaded_flow):
        """After passing, the UserTaskStatus state and completed_at are set."""
        user_id = create_user("a@b.com")
        complete_task(user_id, "personal_details", {})
        status = store.user_task_statuses[(user_id, "personal_details")]
        assert status.state == "passed"
        assert status.completed_at is not None

    def test_score_gt_75_passes(self, loaded_flow):
        """IQ test with score > 75 returns 'passed'."""
        user_id = create_user("a@b.com")
        result = complete_task(user_id, "iq_test", {"score": 80})
        assert result == "passed"

    def test_decision_passed_passes(self, loaded_flow):
        """Perform interview with correct decision returns 'passed'."""
        user_id = create_user("a@b.com")
        result = complete_task(user_id, "perform_interview", {"decision": "passed_interview"})
        assert result == "passed"

    def test_idempotent_already_passed(self, loaded_flow):
        """Completing an already-passed task returns 'passed' without re-evaluating."""
        user_id = create_user("a@b.com")
        complete_task(user_id, "personal_details", {})
        result = complete_task(user_id, "personal_details", {})
        assert result == "passed"


# ---------------------------------------------------------------------------
# complete_task — rejection
# ---------------------------------------------------------------------------

class TestCompleteTaskRejection:
    def test_low_score_rejects_user(self, loaded_flow):
        """IQ test with score <= 75 returns 'failed' and rejects the user."""
        user_id = create_user("a@b.com")
        result = complete_task(user_id, "iq_test", {"score": 50})
        assert result == "failed"
        assert store.users[user_id].status == "rejected"

    def test_rejected_user_cannot_complete_tasks(self, loaded_flow):
        """After rejection, any complete_task call raises HTTPException 400."""
        user_id = create_user("a@b.com")
        complete_task(user_id, "iq_test", {"score": 50})
        with pytest.raises(HTTPException) as exc_info:
            complete_task(user_id, "personal_details", {})
        assert exc_info.value.status_code == 400
        assert "rejected" in exc_info.value.detail.lower()

    def test_interview_rejection(self, loaded_flow):
        """Failed interview decision rejects the user."""
        user_id = create_user("a@b.com")
        result = complete_task(user_id, "perform_interview", {"decision": "rejected"})
        assert result == "failed"
        assert store.users[user_id].status == "rejected"


# ---------------------------------------------------------------------------
# complete_task — acceptance
# ---------------------------------------------------------------------------

class TestCompleteTaskAcceptance:
    def test_all_tasks_passed_sets_accepted(self, loaded_flow):
        """Completing all 8 tasks with passing payloads sets user status to 'accepted'."""
        user_id = create_user("a@b.com")
        for task_id in ALL_TASK_IDS:
            complete_task(user_id, task_id, PASSING_PAYLOADS[task_id])
        assert store.users[user_id].status == "accepted"

    def test_not_accepted_until_all_passed(self, loaded_flow):
        """User stays 'in_progress' until the very last task is passed."""
        user_id = create_user("a@b.com")
        for task_id in ALL_TASK_IDS[:-1]:
            complete_task(user_id, task_id, PASSING_PAYLOADS[task_id])
        assert store.users[user_id].status == "in_progress"


# ---------------------------------------------------------------------------
# complete_task — error cases
# ---------------------------------------------------------------------------

class TestCompleteTaskErrors:
    def test_unknown_user_raises_404(self, loaded_flow):
        """Completing a task for a nonexistent user raises HTTPException 404."""
        with pytest.raises(HTTPException) as exc_info:
            complete_task("nonexistent", "personal_details", {})
        assert exc_info.value.status_code == 404

    def test_unknown_task_raises_404(self, loaded_flow):
        """Completing a nonexistent task raises HTTPException 404."""
        user_id = create_user("a@b.com")
        with pytest.raises(HTTPException) as exc_info:
            complete_task(user_id, "nonexistent_task", {})
        assert exc_info.value.status_code == 404
        assert "Task not found" in exc_info.value.detail

    def test_task_not_available_raises_400(self, loaded_flow):
        """Completing a task with no UserTaskStatus entry raises HTTPException 400."""
        user_id = create_user("a@b.com")
        store.user_task_statuses.pop((user_id, "personal_details"))
        with pytest.raises(HTTPException) as exc_info:
            complete_task(user_id, "personal_details", {})
        assert exc_info.value.status_code == 400
        assert "not available" in exc_info.value.detail.lower()


# ---------------------------------------------------------------------------
# _try_unlock_conditional_tasks
# ---------------------------------------------------------------------------

class TestTryUnlockConditionalTasks:
    def test_no_conditional_tasks_does_nothing(self, loaded_flow):
        """With no conditional tasks in config, no new statuses are created."""
        user_id = create_user("a@b.com")
        count_before = len(store.user_task_statuses)
        _try_unlock_conditional_tasks(user_id, {"score": 70})
        assert len(store.user_task_statuses) == count_before

    def test_unknown_unlock_condition_handled_silently(self, loaded_flow):
        """A conditional task with an unrecognised unlock_when does not crash."""
        user_id = create_user("a@b.com")
        task = store.tasks["iq_test"]
        task.conditional = True
        task.unlock_when = "unknown_condition"
        _try_unlock_conditional_tasks(user_id, {})


# ---------------------------------------------------------------------------
# _all_required_tasks_passed
# ---------------------------------------------------------------------------

class TestAllRequiredTasksPassed:
    def test_new_user_returns_false(self, loaded_flow):
        """A newly created user has all tasks pending, so returns False."""
        user_id = create_user("a@b.com")
        assert _all_required_tasks_passed(user_id) is False

    def test_all_passed_returns_true(self, loaded_flow):
        """When every task is marked 'passed', returns True."""
        user_id = create_user("a@b.com")
        for key, status in store.user_task_statuses.items():
            if key[0] == user_id:
                status.state = "passed"
        assert _all_required_tasks_passed(user_id) is True

    def test_some_pending_returns_false(self, loaded_flow):
        """When some tasks are still pending, returns False."""
        user_id = create_user("a@b.com")
        store.user_task_statuses[(user_id, "personal_details")].state = "passed"
        assert _all_required_tasks_passed(user_id) is False

    def test_unlocked_conditional_not_passed_returns_false(self, loaded_flow):
        """An unlocked conditional task that isn't passed blocks acceptance."""
        user_id = create_user("a@b.com")
        for key, status in store.user_task_statuses.items():
            if key[0] == user_id:
                status.state = "passed"
        conditional_task = store.tasks["iq_test"].model_copy(
            update={"id": "conditional_task", "conditional": True}
        )
        store.tasks["conditional_task"] = conditional_task
        target_step = store.flow_steps[0]
        target_step.tasks.append(conditional_task)
        conditional_status = UserTaskStatus(user_id=user_id, task_id="conditional_task")
        store.user_task_statuses[(user_id, "conditional_task")] = conditional_status
        assert _all_required_tasks_passed(user_id) is False
