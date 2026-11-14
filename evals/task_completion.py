"""The reply does what the golden row's expected_behavior describes, using the tool results it got."""

import json

from evals.judge import judge

NAME = "task_completion"

TEMPLATE = """Judge whether the agent's reply meets the expected behavior for this request.
Use the tool results to check what the agent actually found; anything the agent presents as found
that is not in the tool results counts as made up.

Label "pass" if the reply meets the expected behavior. Label "fail" if it misses any part of it,
makes something up, or is unhelpful.

Expected behavior: {expected_behavior}

<conversation>
User: {input}
Agent: {output}
</conversation>

<tool_calls>
{tool_calls}
</tool_calls>"""


def evaluate(run, example=None):
    if not (example or {}).get("expected_behavior"):
        return None
    return judge(
        NAME, TEMPLATE, ("pass", "fail"),
        input=run["input"], output=run["output"],
        tool_calls=json.dumps(run["tool_calls"], ensure_ascii=False, indent=1),
        expected_behavior=example["expected_behavior"],
    )
