"""Unlock condition evaluator.

Pure function that determines whether a conditional task should be
unlocked for a user based on the current webhook payload.

To add a new unlock condition, add a case to the match statement in
should_unlock(). Then add a corresponding conditional task entry in
config/flow.json with the matching unlock_when key.
"""


def should_unlock(unlock_when: str, payload: dict) -> bool:
    """Evaluate whether a conditional task should be unlocked.

    Args:
        unlock_when: The condition key from the task config
                     (e.g. "score_between_60_75").
        payload: The raw webhook payload dict.

    Returns:
        True if the task should be unlocked, False otherwise.

    Raises:
        ValueError: If the unlock_when condition is not recognised.
    """
    match unlock_when:
        case _:
            raise ValueError(f"Unknown unlock condition: {unlock_when}")
