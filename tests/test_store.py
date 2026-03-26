"""Tests for src/db/store.py — Store initialization and singleton."""

from datetime import datetime, timezone

from src.db.store import Store, store
from src.models.schemas import FlowStep, Task, User, UserTaskStatus


class TestStoreInit:
    def test_empty_on_creation(self):
        """A new Store instance has all empty collections."""
        s = Store()
        assert s.users == {}
        assert s.user_task_statuses == {}
        assert s.flow_steps == []
        assert s.tasks == {}

    def test_collections_are_correct_types(self):
        """Store attributes are the expected container types."""
        s = Store()
        assert isinstance(s.users, dict)
        assert isinstance(s.user_task_statuses, dict)
        assert isinstance(s.flow_steps, list)
        assert isinstance(s.tasks, dict)


class TestStoreSingleton:
    def test_module_level_store_is_store_instance(self):
        """The module-level store is a Store instance."""
        assert isinstance(store, Store)

    def test_store_is_shared(self):
        """Re-importing store returns the same object (singleton)."""
        from src.db.store import store as store2
        assert store is store2


class TestStoreOperations:
    def test_insert_and_lookup_user(self):
        """Can insert a User and retrieve it by ID."""
        user = User(id="u1", email="a@b.com", created_at=datetime.now(timezone.utc))
        store.users["u1"] = user
        assert store.users["u1"].email == "a@b.com"

    def test_insert_and_lookup_task_status(self):
        """Can insert a UserTaskStatus keyed by (user_id, task_id) tuple."""
        status = UserTaskStatus(user_id="u1", task_id="t1")
        store.user_task_statuses[("u1", "t1")] = status
        assert store.user_task_statuses[("u1", "t1")].state == "pending"

    def test_insert_and_lookup_task(self):
        """Can insert a Task and retrieve it by ID."""
        task = Task(id="t1", name="Task", order=1, pass_condition="always")
        store.tasks["t1"] = task
        assert store.tasks["t1"].pass_condition == "always"

    def test_append_and_read_flow_step(self):
        """Can append a FlowStep and read it back from the list."""
        step = FlowStep(id="s1", name="Step", order=1)
        store.flow_steps.append(step)
        assert len(store.flow_steps) == 1
        assert store.flow_steps[0].id == "s1"

    def test_delete_user(self):
        """Can delete a user from the store."""
        user = User(id="u1", email="a@b.com", created_at=datetime.now(timezone.utc))
        store.users["u1"] = user
        del store.users["u1"]
        assert "u1" not in store.users
