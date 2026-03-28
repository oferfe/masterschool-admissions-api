"""Pass condition evaluator.

Pure function that determines whether a task passes or fails based on
its configured pass_condition and the incoming webhook payload.

To add a new pass condition, add a case to the match statement in
evaluate(). Nothing else in the system needs to change.
"""


def evaluate(pass_condition: str, payload: dict) -> str:
    """Evaluate a task's pass condition against the webhook payload.

    Args:
        pass_condition: The condition key from the task config
                        (e.g. "always", "score_gt_75", "decision_passed").
        payload: The raw webhook payload dict.

    Returns:
        "passed" or "failed".

    Raises:
        ValueError: If the pass_condition is not recognised.
    """
    match pass_condition:
        case "always":
            return "passed"
        case "score_gt_75":
            return "passed" if payload.get("score", 0) > 75 else "failed"
        case "score_between_60_75":
            return "passed" if 60 <= payload.get("score", 0) <= 75 else "failed"
        case "decision_passed":
            return "passed" if payload.get("decision") == "passed_interview" else "failed"
        case _:
            raise ValueError(f"Unknown condition: {pass_condition}")
