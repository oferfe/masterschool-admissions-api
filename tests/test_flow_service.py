"""Tests for src/services/flow_service.py — flow config loading and queries."""

from src.db.store import store
from src.services.flow_service import (
    load_flow_config,
    get_flow,
    get_steps_in_order,
    get_tasks_for_step,
)


class TestLoadFlowConfig:
    def test_populates_flow_steps(self, loaded_flow):
        """Loading config creates 6 flow steps in the store."""
        assert len(store.flow_steps) == 6

    def test_populates_tasks(self, loaded_flow):
        """Loading config creates 8 tasks in the store."""
        assert len(store.tasks) == 8

    def test_steps_sorted_by_order(self, loaded_flow):
        """Steps in the store are sorted by their order field."""
        orders = [s.order for s in store.flow_steps]
        assert orders == sorted(orders)

    def test_task_ids_match_config(self, loaded_flow):
        """All 8 expected task IDs are present in the store."""
        expected_ids = {
            "personal_details", "iq_test",
            "schedule_interview", "perform_interview",
            "upload_id", "sign_contract",
            "payment", "join_slack",
        }
        assert set(store.tasks.keys()) == expected_ids

    def test_tasks_have_step_id_set(self, loaded_flow):
        """Each task's step_id matches its parent step."""
        assert store.tasks["iq_test"].step_id == "iq_test"
        assert store.tasks["schedule_interview"].step_id == "interview"
        assert store.tasks["upload_id"].step_id == "sign_contract"


class TestGetStepsInOrder:
    def test_returns_all_steps_sorted(self, loaded_flow):
        """Returns all 6 steps with orders 1 through 6."""
        steps = get_steps_in_order()
        assert len(steps) == 6
        assert [s.order for s in steps] == [1, 2, 3, 4, 5, 6]

    def test_step_ids(self, loaded_flow):
        """Steps are returned in the correct ID order."""
        steps = get_steps_in_order()
        ids = [s.id for s in steps]
        assert ids == [
            "personal_details", "iq_test", "interview",
            "sign_contract", "payment", "join_slack",
        ]


class TestGetFlow:
    def test_same_as_get_steps_in_order(self, loaded_flow):
        """get_flow() returns the same result as get_steps_in_order()."""
        assert get_flow() == get_steps_in_order()


class TestGetTasksForStep:
    def test_interview_has_two_tasks(self, loaded_flow):
        """Interview step contains schedule_interview and perform_interview."""
        tasks = get_tasks_for_step("interview")
        assert len(tasks) == 2
        assert tasks[0].id == "schedule_interview"
        assert tasks[1].id == "perform_interview"

    def test_personal_details_has_one_task(self, loaded_flow):
        """Personal details step has a single task."""
        tasks = get_tasks_for_step("personal_details")
        assert len(tasks) == 1
        assert tasks[0].id == "personal_details"

    def test_sign_contract_has_two_tasks(self, loaded_flow):
        """Sign contract step contains upload_id and sign_contract."""
        tasks = get_tasks_for_step("sign_contract")
        assert len(tasks) == 2
        assert tasks[0].id == "upload_id"
        assert tasks[1].id == "sign_contract"

    def test_nonexistent_step_returns_empty(self, loaded_flow):
        """Querying a nonexistent step returns an empty list."""
        assert get_tasks_for_step("nonexistent") == []

    def test_tasks_sorted_by_order(self, loaded_flow):
        """Tasks within a step are returned sorted by order."""
        tasks = get_tasks_for_step("interview")
        orders = [t.order for t in tasks]
        assert orders == sorted(orders)
