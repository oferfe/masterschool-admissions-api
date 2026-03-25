import json
from pathlib import Path

from src.db.store import store
from src.models.schemas import FlowStep, Task


CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "flow.json"


def load_flow_config() -> None:
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
    return get_steps_in_order()


def get_steps_in_order() -> list[FlowStep]:
    return sorted(store.flow_steps, key=lambda s: s.order)


def get_tasks_for_step(step_id: str) -> list[Task]:
    for step in store.flow_steps:
        if step.id == step_id:
            return sorted(step.tasks, key=lambda t: t.order)
    return []
