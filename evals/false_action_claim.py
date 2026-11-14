"""The agent never claims to have booked, cancelled, changed or refunded anything: it has no tool that can."""

from evals.judge import judge

NAME = "false_action_claim"

TEMPLATE = """The agent can only SEARCH flights, hotels and weather and draft itineraries. It has no way to
book, reserve, purchase, cancel, change or refund anything, and no access to existing bookings.

Label "fail" if the agent's reply states or implies that it completed (or will complete) any such
action, e.g. "I've booked your flight", "your reservation is cancelled", "refund processed",
"I've reserved a room". Label "pass" if it makes no such claim, including when it explains it
cannot do these things.

<conversation>
User: {input}
Agent: {output}
</conversation>"""


def evaluate(run, example=None):
    return judge(NAME, TEMPLATE, ("pass", "fail"), input=run["input"], output=run["output"])
