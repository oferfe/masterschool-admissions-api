"""End-to-end admission flow tests.

Integration scenarios that exercise the complete pipeline by composing
user_service and task_service together, validating state transitions
via get_user_progress and get_user_outcome.
"""

import pytest
from fastapi import HTTPException

from src.services.user_service import create_user, get_user_progress, get_user_outcome
from src.services.task_service import complete_task


class TestHappyPath:
    """Scenario 1: Full acceptance — user completes all tasks successfully."""

    def test_full_acceptance_flow(self, loaded_flow):
        """Walk through the entire flow and verify acceptance at the end."""
        user_id = create_user("student@example.com")
        assert get_user_outcome(user_id) == "in_progress"

        # Step 1: Personal Details
        progress = get_user_progress(user_id)
        assert progress["current_step"].id == "personal_details"
        assert progress["current_task"].id == "personal_details"
        assert progress["step_number"] == 1

        result = complete_task(user_id, "personal_details", {})
        assert result == "passed"

        # Step 2: IQ Test
        progress = get_user_progress(user_id)
        assert progress["current_step"].id == "iq_test"
        assert progress["step_number"] == 2

        result = complete_task(user_id, "iq_test", {"score": 90})
        assert result == "passed"

        # Step 3: Interview — schedule
        progress = get_user_progress(user_id)
        assert progress["current_step"].id == "interview"
        assert progress["current_task"].id == "schedule_interview"
        assert progress["step_number"] == 3

        result = complete_task(user_id, "schedule_interview", {})
        assert result == "passed"

        # Step 3: Interview — perform
        progress = get_user_progress(user_id)
        assert progress["current_step"].id == "interview"
        assert progress["current_task"].id == "perform_interview"

        result = complete_task(user_id, "perform_interview", {"decision": "passed_interview"})
        assert result == "passed"

        # Steps 4-6: Sign Contract, Payment, Join Slack
        complete_task(user_id, "upload_id", {})
        complete_task(user_id, "sign_contract", {})
        complete_task(user_id, "payment", {})
        complete_task(user_id, "join_slack", {})

        # Final outcome
        assert get_user_outcome(user_id) == "accepted"

        # Final progress
        progress = get_user_progress(user_id)
        assert progress["current_step"] is None
        assert progress["current_task"] is None
        assert len(progress["completed_steps"]) == 6
        assert progress["step_number"] == progress["total_steps"]


class TestEarlyRejectionIQ:
    """Scenario 2: User fails the IQ test and is rejected early."""

    def test_failed_iq_rejects_user(self, loaded_flow):
        """Low IQ score causes immediate rejection."""
        user_id = create_user("student@example.com")
        complete_task(user_id, "personal_details", {})

        result = complete_task(user_id, "iq_test", {"score": 50})
        assert result == "failed"
        assert get_user_outcome(user_id) == "rejected"

    def test_no_further_tasks_after_rejection(self, loaded_flow):
        """After IQ rejection, completing any other task raises 400."""
        user_id = create_user("student@example.com")
        complete_task(user_id, "personal_details", {})
        complete_task(user_id, "iq_test", {"score": 50})

        with pytest.raises(HTTPException) as exc_info:
            complete_task(user_id, "schedule_interview", {})
        assert exc_info.value.status_code == 400


class TestRejectionAtInterview:
    """Scenario 3: User passes IQ but fails the interview."""

    def test_failed_interview_rejects_user(self, loaded_flow):
        """Bad interview decision causes rejection."""
        user_id = create_user("student@example.com")
        complete_task(user_id, "personal_details", {})
        complete_task(user_id, "iq_test", {"score": 90})
        complete_task(user_id, "schedule_interview", {})

        result = complete_task(user_id, "perform_interview", {"decision": "failed"})
        assert result == "failed"
        assert get_user_outcome(user_id) == "rejected"


class TestProgressTrackingMidFlow:
    """Scenario 4: Verify progress is accurate after completing some steps."""

    def test_progress_after_two_steps(self, loaded_flow):
        """After completing steps 1-2, user is on step 3 (interview)."""
        user_id = create_user("student@example.com")
        complete_task(user_id, "personal_details", {})
        complete_task(user_id, "iq_test", {"score": 80})

        progress = get_user_progress(user_id)
        assert progress["step_number"] == 3
        assert progress["completed_steps"] == ["personal_details", "iq_test"]
        assert progress["current_step"].id == "interview"
        assert progress["current_task"].id == "schedule_interview"
        assert progress["total_steps"] == 6


class TestSecondChanceConditionalTask:
    """Scenario 5: User fails IQ with borderline score, gets a retake opportunity."""

    def test_borderline_score_unlocks_retake(self, loaded_flow):
        """Score 65 fails the IQ test but unlocks retake_iq; user stays in_progress."""
        user_id = create_user("student@example.com")
        complete_task(user_id, "personal_details", {})

        result = complete_task(user_id, "iq_test", {"score": 65})
        assert result == "failed"
        assert get_user_outcome(user_id) == "in_progress"

    def test_retake_passes_and_flow_continues(self, loaded_flow):
        """After failing IQ with 65, passing retake_iq allows full acceptance."""
        user_id = create_user("student@example.com")
        complete_task(user_id, "personal_details", {})
        complete_task(user_id, "iq_test", {"score": 65})

        result = complete_task(user_id, "retake_iq", {"score": 80})
        assert result == "passed"
        assert get_user_outcome(user_id) == "in_progress"

        complete_task(user_id, "schedule_interview", {})
        complete_task(user_id, "perform_interview", {"decision": "passed_interview"})
        complete_task(user_id, "upload_id", {})
        complete_task(user_id, "sign_contract", {})
        complete_task(user_id, "payment", {})
        complete_task(user_id, "join_slack", {})

        assert get_user_outcome(user_id) == "accepted"

    def test_retake_also_fails_rejects_user(self, loaded_flow):
        """Failing retake_iq (score still too low) rejects the user."""
        user_id = create_user("student@example.com")
        complete_task(user_id, "personal_details", {})
        complete_task(user_id, "iq_test", {"score": 65})

        result = complete_task(user_id, "retake_iq", {"score": 50})
        assert result == "failed"
        assert get_user_outcome(user_id) == "rejected"

    def test_low_score_no_retake_rejects_immediately(self, loaded_flow):
        """Score below 60 fails IQ and does NOT unlock retake — immediate rejection."""
        user_id = create_user("student@example.com")
        complete_task(user_id, "personal_details", {})

        result = complete_task(user_id, "iq_test", {"score": 50})
        assert result == "failed"
        assert get_user_outcome(user_id) == "rejected"

    def test_progress_shows_retake_after_borderline_failure(self, loaded_flow):
        """After borderline IQ failure, progress shows retake_iq as the current task."""
        user_id = create_user("student@example.com")
        complete_task(user_id, "personal_details", {})
        complete_task(user_id, "iq_test", {"score": 65})

        progress = get_user_progress(user_id)
        assert progress["current_step"].id == "iq_test"
        assert progress["current_task"].id == "retake_iq"
        assert progress["step_number"] == 2


class TestDuplicateUser:
    """Scenario 5: Attempting to register with an existing email."""

    def test_duplicate_email_raises_409(self, loaded_flow):
        """Creating two users with the same email raises 409."""
        create_user("a@b.com")
        with pytest.raises(HTTPException) as exc_info:
            create_user("a@b.com")
        assert exc_info.value.status_code == 409
