from src.models.schemas import FlowStep, Task, User, UserTaskStatus


class Store:
    def __init__(self):
        self.users: dict[str, User] = {}
        self.user_task_statuses: dict[tuple[str, str], UserTaskStatus] = {}
        self.flow_steps: list[FlowStep] = []
        self.tasks: dict[str, Task] = {}


store = Store()
