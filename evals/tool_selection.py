"""Every tool the golden row expects was called."""

import json

NAME = "tool_selection"


def evaluate(run, example=None):
    expected = (example or {}).get("expected_tools")
    if isinstance(expected, str):  # Arize stores list fields as JSON strings
        expected = json.loads(expected)
    if not expected:
        return None
    missing = sorted(set(expected) - {c["name"] for c in run["tool_calls"]})
    if missing:
        return {"label": "fail", "score": 0, "explanation": f"Expected tools not called: {missing}"}
    return {"label": "pass", "score": 1, "explanation": f"Called {sorted(set(expected))}."}
