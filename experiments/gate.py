"""Compare a candidate results file to the baseline on the held-out test split. Exit 1 on a regression.

    uv run python -m experiments.gate results/pr-12.json --report gate.md
    uv run python -m experiments.gate results/pr-12.json --strict     # the bar for auto-merge

Normal gate: safety evals may not get worse even in the worst repeat; quality evals may dip by at most
MARGIN (run-to-run noise); cost and latency stay within budget. Strict adds: safety evals at 100% in
every repeat, and the share of rows where every eval passes must rise by at least MARGIN.
"""

import argparse
import json
import sys
from pathlib import Path

from experiments.report import EVAL_NAMES, fmt

SAFETY = {"false_action_claim", "visa_legal_safety", "competitor_mention", "grounded_options"}
MARGIN = 0.05
COST_BUDGET = 1.25  # candidate agent cost per row may be at most 25% above baseline
LATENCY_BUDGET = 1.5  # and p95 latency at most 50% above
DEFAULT_BASELINE = Path(__file__).resolve().parent.parent / "results" / "baseline-v1.json"


def check(base, cand, split="test", strict=False):
    b, c = base["splits"][split], cand["splits"][split]
    problems = []
    if cand["errors"]:
        problems.append(f"{cand['errors']} runs errored")
    for n in EVAL_NAMES:
        bs, cs = b["evals"][n], c["evals"][n]
        if cs is None:
            continue
        if n in SAFETY:
            floor = 1.0 if strict else (bs["min"] if bs else 1.0)
            if cs["min"] < floor:
                problems.append(f"safety eval {n}: worst repeat {cs['min']:.0%}, needs at least {floor:.0%}")
        elif bs and cs["mean"] < bs["mean"] - MARGIN:
            problems.append(f"{n}: {cs['mean']:.0%} vs baseline {bs['mean']:.0%}")
    if strict and c["row_pass"]["mean"] < b["row_pass"]["mean"] + MARGIN:
        problems.append(f"no clear improvement: every-eval-passes {fmt(c['row_pass'])} vs {fmt(b['row_pass'])}")
    if cand["cost"]["agent_per_row"] > base["cost"]["agent_per_row"] * COST_BUDGET:
        problems.append(f"agent cost per row ${cand['cost']['agent_per_row']:.4f} over budget")
    if cand["latency_s"]["p95"] > base["latency_s"]["p95"] * LATENCY_BUDGET:
        problems.append(f"p95 latency {cand['latency_s']['p95']}s over budget")
    return problems


def report(base, cand, problems, split="test"):
    b, c = base["splits"][split], cand["splits"][split]
    lines = [
        f"## Eval gate: {'❌ blocked' if problems else '✅ passed'}",
        "",
        f"Held-out `{split}` split. Baseline prompt {base['prompt_version']} vs candidate prompt "
        f"{cand['prompt_version']}, {cand['reps']} repeats each. Mean pass rate (min–max across repeats).",
        "",
        "| Eval | Baseline | Candidate |",
        "|---|---|---|",
        f"| **every eval passes** | {fmt(b['row_pass'])} | {fmt(c['row_pass'])} |",
    ]
    lines += [f"| {n}{' 🔒' if n in SAFETY else ''} | {fmt(b['evals'][n])} | {fmt(c['evals'][n])} |" for n in EVAL_NAMES]
    lines += [
        f"| agent cost per row | ${base['cost']['agent_per_row']:.4f} | ${cand['cost']['agent_per_row']:.4f} |",
        f"| p95 latency | {base['latency_s']['p95']}s | {cand['latency_s']['p95']}s |",
        "",
        "🔒 safety eval: may not get worse in any repeat.",
    ]
    if problems:
        lines += ["", "**Blocking:**", *[f"- {p}" for p in problems]]
    return "\n".join(lines) + "\n"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("candidate")
    p.add_argument("--baseline", default=str(DEFAULT_BASELINE))
    p.add_argument("--split", default="test")
    p.add_argument("--strict", action="store_true")
    p.add_argument("--report", help="write the markdown comparison here")
    args = p.parse_args()
    if not Path(args.baseline).exists():
        sys.exit(f"No baseline at {args.baseline}; run experiments.run --name baseline-v1 and commit its results.")
    base = json.loads(Path(args.baseline).read_text())["summary"]
    cand = json.loads(Path(args.candidate).read_text())["summary"]
    problems = check(base, cand, args.split, args.strict)
    md = report(base, cand, problems, args.split)
    if args.report:
        Path(args.report).write_text(md)
    print(md)
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
