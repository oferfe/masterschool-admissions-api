def should_unlock(unlock_when: str, payload: dict) -> bool:
    """Evaluate whether a conditional task should be unlocked.

    To add a new unlock condition, add a case to the match statement:

        case "your_condition_name":
            return <bool expression using payload>
    """
    match unlock_when:
        case _:
            raise ValueError(f"Unknown unlock condition: {unlock_when}")
