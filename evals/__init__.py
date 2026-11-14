"""Plug-in evals. Each module exposes NAME and evaluate(run, example) -> Result | None.

Result = {"label": str, "score": 0 | 1, "explanation": str}; None means not applicable.
`example` is a golden-dataset row (None in production); evals that need one return None without it.
Add an eval by writing a module with that interface and listing it in ALL_EVALS.
"""

from evals import (
    competitor_mention,
    facts_correct,
    false_action_claim,
    grounded_options,
    scope_adherence,
    task_completion,
    tool_selection,
    visa_legal_safety,
)

ALL_EVALS = [
    grounded_options,
    facts_correct,
    tool_selection,
    competitor_mention,
    false_action_claim,
    visa_legal_safety,
    scope_adherence,
    task_completion,
]


def run_all(run: dict, example: dict | None = None, evals=ALL_EVALS) -> dict:
    """Score one run with every applicable eval: {eval name: Result}."""
    results = {}
    for e in evals:
        result = e.evaluate(run, example)
        if result is not None:
            results[e.NAME] = result
    return results
