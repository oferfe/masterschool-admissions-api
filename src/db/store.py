"""In-memory data store for the Admissions System.

Provides a single global Store instance that holds all application state.
Flow config (steps/tasks) is populated once at startup; user data is
created and mutated at runtime through the service layer.
"""

from src.models.schemas import FlowStep, Task, User, UserTaskStatus


class Store:
    """Central in-memory store holding both config and runtime state.

    Attributes:
        users: All registered users, keyed by user ID.
        user_task_statuses: Per-user task state, keyed by (user_id, task_id)
                            for O(1) lookups.
        flow_steps: Ordered list of flow steps (loaded from flow.json).
        tasks: All tasks across all steps, keyed by task ID.
    """
    def __init__(self):
        self.users: dict[str, User] = {}
        self.user_task_statuses: dict[tuple[str, str], UserTaskStatus] = {}
        self.flow_steps: list[FlowStep] = []
        self.tasks: dict[str, Task] = {}


store = Store()
