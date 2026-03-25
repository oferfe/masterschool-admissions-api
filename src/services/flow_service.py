"""Flow configuration service.

Responsible for loading the admissions flow from config/flow.json into
the in-memory store at startup, and providing query helpers to retrieve
steps and tasks in order.
"""

import json
from pathlib import Path

from src.db.store import store
from src.models.schemas import FlowStep, Task


CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "flow.json"


def load_flow_config() -> None:
    """Read config/flow.json and populate the store with FlowStep and Task instances.

    Called once during application startup (via the FastAPI lifespan hook).
    Each task is stored both inside its parent step and in the flat
    store.tasks dict for O(1) lookup by task ID.
    """
    with open(CONFIG_PATH) as f:
        raw_steps = json.load(f)

    for raw_step in raw_steps:
        tasks = []
        for raw_task in raw_step.get("tasks", []):
            task = Task(step_id=raw_step["id"], **raw_task)
            tasks.append(task)
            store.tasks[task.id] = task

        step = FlowStep(
            id=raw_step["id"],
            name=raw_step["name"],
            order=raw_step["order"],
            tasks=tasks,
        )
        store.flow_steps.append(step)

    store.flow_steps.sort(key=lambda s: s.order)


def get_flow() -> list[FlowStep]:
    """Return all flow steps in order. Used by the GET /flow endpoint."""
    return get_steps_in_order()


def get_steps_in_order() -> list[FlowStep]:
    """Return all flow steps sorted by their order field."""
    return sorted(store.flow_steps, key=lambda s: s.order)


def get_tasks_for_step(step_id: str) -> list[Task]:
    """Return all tasks for a given step, sorted by order.

    Returns an empty list if the step ID is not found.
    """
    for step in store.flow_steps:
        if step.id == step_id:
            return sorted(step.tasks, key=lambda t: t.order)
    return []
