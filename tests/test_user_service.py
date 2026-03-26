"""Tests for src/services/user_service.py — user creation, progress, and outcome."""

import pytest
from fastapi import HTTPException

from src.db.store import store
from src.services.user_service import (
    create_user,
    get_user,
    get_user_progress,
    get_user_outcome,
)


class TestCreateUser:
    def test_returns_uuid_string(self, loaded_flow):
        """create_user returns a non-empty UUID string."""
        user_id = create_user("test@example.com")
        assert isinstance(user_id, str)
        assert len(user_id) > 0

    def test_user_stored(self, loaded_flow):
        """Created user is stored in the store with the correct email."""
        user_id = create_user("test@example.com")
        assert user_id in store.users
        assert store.users[user_id].email == "test@example.com"

    def test_user_status_in_progress(self, loaded_flow):
        """Newly created user has status 'in_progress'."""
        user_id = create_user("test@example.com")
        assert store.users[user_id].status == "in_progress"

    def test_seeds_task_statuses_for_non_conditional_tasks(self, loaded_flow):
        """User creation seeds a UserTaskStatus for each of the 8 non-conditional tasks."""
        user_id = create_user("test@example.com")
        task_ids = {key[1] for key in store.user_task_statuses if key[0] == user_id}
        expected = {
            "personal_details", "iq_test",
            "schedule_interview", "perform_interview",
            "upload_id", "sign_contract",
            "payment", "join_slack",
        }
        assert task_ids == expected

    def test_all_task_statuses_pending(self, loaded_flow):
        """All seeded task statuses start in 'pending' state."""
        user_id = create_user("test@example.com")
        for key, status in store.user_task_statuses.items():
            if key[0] == user_id:
                assert status.state == "pending"

    def test_duplicate_email_raises_409(self, loaded_flow):
        """Creating a user with an already-registered email raises 409."""
        create_user("test@example.com")
        with pytest.raises(HTTPException) as exc_info:
            create_user("test@example.com")
        assert exc_info.value.status_code == 409


class TestGetUser:
    def test_returns_existing_user(self, loaded_flow):
        """get_user returns the correct User object for a valid ID."""
        user_id = create_user("test@example.com")
        user = get_user(user_id)
        assert user.id == user_id
        assert user.email == "test@example.com"

    def test_nonexistent_user_raises_404(self, loaded_flow):
        """get_user raises 404 for a nonexistent user ID."""
        with pytest.raises(HTTPException) as exc_info:
            get_user("nonexistent-id")
        assert exc_info.value.status_code == 404


class TestGetUserProgress:
    def test_new_user_at_step_1(self, loaded_flow):
        """A new user starts at step 1 (personal_details) with no completed steps."""
        user_id = create_user("test@example.com")
        progress = get_user_progress(user_id)
        assert progress["current_step"].id == "personal_details"
        assert progress["current_task"].id == "personal_details"
        assert progress["completed_steps"] == []
        assert progress["step_number"] == 1
        assert progress["total_steps"] == 6

    def test_all_tasks_passed(self, loaded_flow):
        """When all tasks are passed, current_step is None and all 6 steps are completed."""
        user_id = create_user("test@example.com")
        for key, status in store.user_task_statuses.items():
            if key[0] == user_id:
                status.state = "passed"

        progress = get_user_progress(user_id)
        assert progress["current_step"] is None
        assert progress["current_task"] is None
        assert len(progress["completed_steps"]) == 6
        assert progress["step_number"] == progress["total_steps"]

    def test_partial_progress(self, loaded_flow):
        """After completing steps 1-2, current step is interview (step 3)."""
        user_id = create_user("test@example.com")
        store.user_task_statuses[(user_id, "personal_details")].state = "passed"
        store.user_task_statuses[(user_id, "iq_test")].state = "passed"

        progress = get_user_progress(user_id)
        assert progress["completed_steps"] == ["personal_details", "iq_test"]
        assert progress["current_step"].id == "interview"
        assert progress["current_task"].id == "schedule_interview"
        assert progress["step_number"] == 3

    def test_nonexistent_user_raises_404(self, loaded_flow):
        """get_user_progress raises 404 for a nonexistent user ID."""
        with pytest.raises(HTTPException) as exc_info:
            get_user_progress("nonexistent-id")
        assert exc_info.value.status_code == 404


class TestGetUserOutcome:
    def test_new_user_in_progress(self, loaded_flow):
        """A new user's outcome is 'in_progress'."""
        user_id = create_user("test@example.com")
        assert get_user_outcome(user_id) == "in_progress"

    def test_returns_accepted(self, loaded_flow):
        """Returns 'accepted' after the user's status is set to accepted."""
        user_id = create_user("test@example.com")
        store.users[user_id].status = "accepted"
        assert get_user_outcome(user_id) == "accepted"

    def test_returns_rejected(self, loaded_flow):
        """Returns 'rejected' after the user's status is set to rejected."""
        user_id = create_user("test@example.com")
        store.users[user_id].status = "rejected"
        assert get_user_outcome(user_id) == "rejected"

    def test_nonexistent_user_raises_404(self, loaded_flow):
        """get_user_outcome raises 404 for a nonexistent user ID."""
        with pytest.raises(HTTPException) as exc_info:
            get_user_outcome("nonexistent-id")
        assert exc_info.value.status_code == 404
