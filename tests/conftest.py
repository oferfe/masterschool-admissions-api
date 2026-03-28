"""Shared test fixtures for the Admissions System test suite."""

import pytest

from src.db.store import store
from src.services.flow_service import load_flow_config


@pytest.fixture(autouse=True)
def reset_store():
    """Reset the in-memory store before each test to prevent state leakage."""
    store.users.clear()
    store.user_task_statuses.clear()
    store.flow_steps.clear()
    store.tasks.clear()
    yield


@pytest.fixture
def loaded_flow():
    """Load the flow config from flow.json into the store."""
    load_flow_config()
