def evaluate(pass_condition: str, payload: dict) -> str:
    match pass_condition:
        case "always":
            return "passed"
        case "score_gt_75":
            return "passed" if payload.get("score", 0) > 75 else "failed"
        case "decision_passed":
            return "passed" if payload.get("decision") == "passed_interview" else "failed"
        case _:
            raise ValueError(f"Unknown condition: {pass_condition}")
