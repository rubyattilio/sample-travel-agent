"""Every flight and hotel the reply offers must come from this run's own tool results."""

from evals.extract import flight_numbers, hotel_names, tool_text

NAME = "grounded_options"


def evaluate(run, example=None):
    found = tool_text(run)
    offered = flight_numbers(run["output"]) | hotel_names(run["output"])
    if not offered:
        return None
    ungrounded = sorted(o for o in offered if o not in flight_numbers(found) | hotel_names(found))
    if ungrounded:
        return {"label": "fail", "score": 0, "explanation": f"Not in any tool result: {', '.join(ungrounded)}"}
    return {"label": "pass", "score": 1, "explanation": f"All {len(offered)} offered options came from tool results."}
