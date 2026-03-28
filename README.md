# Admissions System API

A FastAPI-based REST API that manages a multi-step student admissions flow. Users register, complete tasks in a defined sequence, and are ultimately accepted or rejected based on task outcomes.

## Quick Start

### With Docker

```bash
docker build -t admissions-api .
docker run -p 8000:8000 admissions-api
```

### Without Docker

```bash
pip install -r requirements.txt
uvicorn src.app:app --host 0.0.0.0 --port 8000
```

Visit `http://localhost:8000/docs` for the interactive Swagger UI.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/users` | Register a new user (requires `email`) |
| `GET` | `/users/{user_id}/progress` | Get the user's current position in the flow |
| `GET` | `/users/{user_id}/outcome` | Get admission outcome (`in_progress`, `accepted`, `rejected`) |
| `PUT` | `/users/{user_id}/tasks/{task_id}` | Complete a task with a payload |
| `GET` | `/flow` | Get the full admissions flow definition |

## Admissions Flow

The flow is defined in `config/flow.json` and consists of 6 sequential steps:

| Step | Task(s) | Pass Condition |
|------|---------|----------------|
| 1. Personal Details | `personal_details` | Always passes |
| 2. IQ Test | `iq_test` | Score > 75 |
| | `retake_iq` *(conditional)* | Score > 75 - unlocked if initial score is 60-75 |
| 3. Interview | `schedule_interview` | Always passes |
| | `perform_interview` | Decision = `"passed_interview"` |
| 4. Sign Contract | `upload_id` | Always passes |
| | `sign_contract` | Always passes |
| 5. Payment | `payment` | Always passes |
| 6. Join Slack | `join_slack` | Always passes |

- Failing a task **rejects** the user — unless a conditional task is unlocked as a second chance (see [Extending the Flow](#extending-the-flow)).
- Passing all tasks **accepts** the user.

## Architecture

```
src/
├── app.py                  # FastAPI app, lifespan hook, route mounting
├── routes/
│   ├── users.py            # User registration, progress, outcome
│   ├── tasks.py            # Task completion webhook
│   └── flow.py             # Flow definition endpoint
├── services/
│   ├── user_service.py     # User creation, progress computation
│   ├── task_service.py     # Task completion state machine
│   └── flow_service.py     # Flow config loading and queries
├── models/
│   └── schemas.py          # Pydantic models (config, runtime, request/response)
├── evaluators/
│   ├── pass_condition.py   # Pass/fail evaluation per task
│   └── unlock_condition.py # Conditional task unlock evaluation
└── db/
    └── store.py            # In-memory data store
```

## Running Tests

```bash
python -m pytest tests/ -v
```

## Extending the Flow

The system allows you to add new tasks and logic without modifying the core routing or service layers. Below is a guide on how to add new tasks, pass conditions, and conditional tasks.
(Note: For demonstration purposes, the current configuration includes an example conditional task to validate the end-to-end flow).

### Adding a new task

Add a task entry to the relevant step in `config/flow.json`:

```json
{ "id": "background_check", "name": "Background Check", "order": 2, "pass_condition": "always" }
```

That's it — the task will appear in the flow and users will need to complete it.

### Adding a new pass condition

1. Choose a condition key (e.g., `"score_gt_90"`).
2. Add a `case` to the `match` statement in `src/evaluators/pass_condition.py`:

```python
case "score_gt_90":
    return "passed" if payload.get("score", 0) > 90 else "failed"
```

3. Reference it in `flow.json`:

```json
{ "id": "advanced_test", "name": "Advanced Test", "order": 1, "pass_condition": "score_gt_90" }
```

### Adding a conditional task

Conditional tasks are hidden by default and only unlocked for specific users based on runtime data. For example, to add a "Retake IQ Test" task for users who score between 60 and 75:

**Step 1** — Add the conditional task to `config/flow.json` inside the relevant step:

```json
{
  "id": "iq_test",
  "name": "IQ Test",
  "order": 2,
  "tasks": [
    { "id": "iq_test", "name": "IQ Test", "order": 1, "pass_condition": "score_gt_75" },
    { "id": "retake_iq", "name": "Retake IQ Test", "order": 2, "pass_condition": "score_gt_75", "conditional": true, "unlock_when": "score_between_60_75" }
  ]
}
```

Key fields:
- `conditional: true` — hidden from the default flow, not seeded at user creation.
- `unlock_when` — the condition key evaluated against the payload to decide whether to unlock this task.

**Step 2** — Add the unlock condition to `src/evaluators/unlock_condition.py`:

```python
match unlock_when:
    case "score_between_60_75":
        score = payload.get("score", 0)
        return 60 <= score <= 75
    case _:
        raise ValueError(f"Unknown unlock condition: {unlock_when}")
```

**How it works at runtime:**

1. User submits IQ test with `{"score": 65}`.
2. `pass_condition.py` evaluates `score_gt_75` → `"failed"`.
3. `_try_unlock_conditional_tasks` runs and evaluates `score_between_60_75` against the payload → `True`.
4. A `UserTaskStatus` is created for `retake_iq` (in `"pending"` state).
5. Because a conditional task was unlocked, the user is **not rejected** — they stay `"in_progress"`.
6. The user can now complete `retake_iq` with a higher score to continue.

If no conditional task is unlocked on failure (e.g., score < 60), the user is rejected immediately.

## Assumptions

1. **Sequential flow**: The admissions flow is designed to be completed in order (step 1 before step 2, etc.). The system enforces this at the API level, returning an error with an informative message if a candidate attempts to skip a required task.
2. **In-memory storage is acceptable**: The system is designed such that all data lives in memory and is lost on restart. 
3. **Flow config is static at runtime**: The flow is loaded once from `config/flow.json` at startup and does not change while the server is running.

## Design Choices

1. **Config-driven flow (`flow.json`)**: The admissions flow is defined in a JSON file rather than hardcoded. This makes it easy to add, remove, or reorder steps and tasks without changing application code.
2. **Single generic webhook endpoint**: All task completions go through one `PUT /users/{id}/tasks/{task_id}` endpoint with a flexible `dict` body, rather than separate endpoints per task. This keeps the API surface small and allows new task types to be added via config alone.
3. **Evaluator pattern for pass/unlock conditions**: Pass conditions (`pass_condition.py`) and unlock conditions (`unlock_condition.py`) are isolated pure functions using pattern matching. Adding a new condition means adding a single `case` — no other code needs to change.
4. **Conditional tasks are lazily unlocked**: Conditional tasks are not seeded at user creation because they only apply to specific users based on runtime data. This avoids cluttering every user's task list with irrelevant tasks.
5. **Two-endpoint frontend pattern**: `GET /flow` returns the general flow definition (shared across all users) for displaying the overall structure and step names. `GET /users/{id}/progress` returns user-specific progress, including which step and task the user is currently on and any unlocked conditional tasks. A frontend combines both: `/flow` for the layout, `/progress` for highlighting the user's current position.

## Known Limitations

### 1. In-Memory Store — No Persistence
All data (users, task statuses, flow config) lives in memory. Restarting the server **wipes everything**. There is no database — the store is a plain Python object (`src/db/store.py`).

### 2. No Migration Strategy for Flow Updates
There is no mechanism to reconcile existing users' task statuses when the flow changes. In a production system with a persistent database, a migration job would be needed to seed missing task statuses for existing in-progress users whenever the flow is updated.

### 3. The "Conditional-Only Step" Edge Case
The schema enforces that every step must contain at least one task (`min_length=1`). However, if a step contains **only** conditional tasks, there is still a risk: if a user fails to unlock any of them, the step effectively becomes empty for that user and the system's logic defaults to `all_passed = True`, automatically marking the step as completed.

Our current `flow.json` safely prevents this by including at least one mandatory (non-conditional) task per step to act as an anchor. Future configurations must maintain this pattern to ensure users aren't skipped ahead unintentionally.

### 4. Untyped Task Payloads — Examples Only, No Validation
The `PUT /users/{user_id}/tasks/{task_id}` endpoint accepts a generic `dict` body. Swagger UI provides a dropdown with example payloads for each task type (select from the "Examples" dropdown to see the expected fields), but these are **documentation only**. The server does not enforce required fields or validate the payload structure — any JSON object is accepted.

Missing fields cause **silent failures**: a missing `score` defaults to `0` (which fails the `> 75` check), and a missing `decision` defaults to `None` (which fails the `== "passed_interview"` check). In both cases the user is **permanently rejected** with no validation error explaining what went wrong.

For simplicity, the webhook accepts data as a flexible `dict`. In a production environment, strict Pydantic models with `extra='forbid'` should be used for each task type to prevent payload pollution and enforce strict input validation.

## Future Improvements

1. **Persistent database** — Replace the in-memory store with a database (e.g., PostgreSQL with SQLAlchemy) so data survives restarts.
2. **Flow migration strategy** — A mechanism to reconcile existing users' task statuses when `flow.json` changes (seed missing statuses, clean up orphaned ones).
3. **Strict payload validation** — Typed Pydantic models per task type with `extra='forbid'` to enforce required fields and return clear 422 errors on invalid input.
4. **Generic pass conditions** — The current pass condition evaluator uses hardcoded `match/case` branches. A more extensible approach would define conditions in `flow.json` as generic expressions (e.g., `{"field": "score", "operator": ">", "value": 75}`), allowing new conditions to be added via config without writing Python code.

