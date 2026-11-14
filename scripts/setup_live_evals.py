"""Score live production traffic in Arize with the same safety judges the experiments use.

Creates one Arize template evaluator per judge (same prompt text as evals/, so there is one source of truth)
and a continuous task that runs them on every new travel_agent span in the project. Prints the ax commands
and changes nothing unless --apply is passed.

    uv run python scripts/setup_live_evals.py --ai-integration-id INT_ID           # dry run
    uv run python scripts/setup_live_evals.py --ai-integration-id INT_ID --apply

INT_ID is an Arize AI integration holding an Anthropic key (`ax ai-integrations list --space SPACE`).
Only judges that need no golden row can run live: task_completion and the code evals need expected answers.
"""

import argparse
import json
import os
import shlex
import subprocess

import agent.config  # noqa: F401  loads ARIZE_SPACE_ID from .env
from evals import false_action_claim, scope_adherence, visa_legal_safety
from evals.judge import JUDGE_MODEL, PREAMBLE

LIVE_JUDGES = {
    false_action_claim: {"pass": 1, "fail": 0},
    visa_legal_safety: {"pass": 1, "fail": 0, "not_applicable": 1},  # Arize needs a score per label
    scope_adherence: {"pass": 1, "fail": 0},
}
# The agent span (our only AGENT span) holds this turn's user message and the reply the user saw.
COLUMNS = {"input": "attributes.input.value", "output": "attributes.output.value"}


def ax(args, apply):
    print("ax " + shlex.join(args))
    if not apply:
        return None
    out = subprocess.run(["ax", *args, "-o", "json"], check=True, capture_output=True, text=True).stdout
    return json.loads(out)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--ai-integration-id", required=True)
    p.add_argument("--project", default="travel-agent")
    p.add_argument("--sampling-rate", default="1.0", help="500 conversations a day is cheap enough to score all")
    p.add_argument("--apply", action="store_true")
    args = p.parse_args()
    space = os.environ["ARIZE_SPACE_ID"]

    evaluators = []
    for module, choices in LIVE_JUDGES.items():
        created = ax([
            "evaluators", "create-evaluator", "template", "--name", module.NAME, "--space", space,
            "--template-name", module.NAME, "--commit-message", "From evals/" + module.NAME + ".py",
            "--template", PREAMBLE + module.TEMPLATE, "--ai-integration-id", args.ai_integration_id,
            "--model-name", JUDGE_MODEL, "--include-explanations", "--use-function-calling",
            "--classification-choices", json.dumps(choices),
        ], args.apply)
        evaluator_id = created["id"] if created else f"<{module.NAME}-id>"
        evaluators.append({"evaluator_id": evaluator_id, "column_mappings": COLUMNS})

    ax([
        "tasks", "create-evaluation", "--name", "live-safety-judges", "--task-type", "TEMPLATE_EVALUATION",
        "--project", args.project, "--space", space, "--evaluators", json.dumps(evaluators),
        "--query-filter", "attributes.openinference.span.kind = 'AGENT'", "--is-continuous", "--sampling-rate", args.sampling_rate,
    ], args.apply)


if __name__ == "__main__":
    main()
