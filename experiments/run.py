"""Run the golden set through the agent, score every run, and log each repeat to Arize as an experiment.

    uv run python -m experiments.run --name baseline-v1 --reps 3
    uv run python -m experiments.run --name debug --limit 3 --reps 1 --no-upload   # a few cents

Writes results/<name>.json (every run, with scores and cost) and results/<name>.md (the summary).
Traces go to the travel-agent-experiments project so they don't mix with production traffic.
"""

import argparse
import json
import os
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

os.environ.setdefault("ARIZE_PROJECT_NAME", "travel-agent-experiments")  # before agent import reads it

import anthropic  # noqa: E402
from openinference.instrumentation import using_session  # noqa: E402

import agent.loop  # noqa: E402
import evals.judge  # noqa: E402
from agent.instrumentation import tracer_provider  # noqa: E402
from agent.prompt import PROMPT_VERSION  # noqa: E402
from evals import run_all  # noqa: E402
from evals.record import from_messages  # noqa: E402
from experiments.report import EVAL_NAMES, summarize, to_markdown  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
GOLDEN = ROOT / "data" / "golden_v1.json"
DATASET = "travel-agent-golden"
PRICES = {"claude-haiku-4-5": (1.0, 5.0), "claude-haiku-5-5": (0.10, 0.50)}  # $ per million tokens, in / out

_cost = threading.local()  # one row runs on one thread, so per-thread totals are per-row totals


def _metered(fn, bucket):
    def call(*args, **kwargs):
        response = fn(*args, **kwargs)
        price_in, price_out = PRICES[kwargs["model"]]  # KeyError on a new model beats silently reporting $0
        usage = response.usage
        cost = (usage.input_tokens * price_in + usage.output_tokens * price_out) / 1e6
        setattr(_cost, bucket, getattr(_cost, bucket, 0.0) + cost)
        return response

    return call


def meter_clients():
    """Count the cost of agent and judge calls without touching agent code."""
    agent.loop.client.messages.create = _metered(agent.loop.client.messages.create, "agent")
    evals.judge._client = evals.judge._client or anthropic.Anthropic()
    evals.judge._client.messages.parse = _metered(evals.judge._client.messages.parse, "judge")


def run_row(row, rep, name):
    _cost.agent = _cost.judge = 0.0
    messages, error, scores = [], None, {}
    start = time.perf_counter()
    try:
        with using_session(f"{name}-r{rep}-{row['example_key']}"):
            for turn in row["turns"]:
                messages.append({"role": "user", "content": turn})
                _, messages = agent.loop.run_agent(messages)
    except Exception as e:  # one broken row must not sink the run; it is reported as an error
        error = repr(e)
    latency = time.perf_counter() - start
    record = from_messages(messages)
    if error is None:
        try:
            scores = run_all(record, row)
        except Exception as e:
            error = f"eval error: {e!r}"
    return {
        "rep": rep, "example_key": row["example_key"], "split": row["split"], "category": row["category"],
        "output": record["output"], "tool_calls": record["tool_calls"], "scores": scores, "error": error,
        "latency_s": round(latency, 2), "agent_cost": _cost.agent, "judge_cost": _cost.judge,
    }


def _ax(*args):
    out = subprocess.run(["ax", *args], check=True, capture_output=True, text=True).stdout
    return json.loads(out) if out.strip().startswith(("[", "{")) else out


def upload(name, runs, space):
    """One Arize experiment per repeat, with every eval score attached to its run."""
    rows = _ax("datasets", "export", DATASET, "--space", space, "--stdout", "--all")
    ids = {r["additional_properties"]["example_key"]: r["id"] for r in rows}
    have = {c["name"] for c in _ax("annotation-configs", "list", "--space", space, "-o", "json")}
    for n in EVAL_NAMES:
        if n not in have:
            _ax("annotation-configs", "create", "categorical", "--name", n, "--space", space,
                "--value", "pass", "--value", "fail", "--optimization-direction", "MAXIMIZE")
    tmp = ROOT / "results" / ".upload.jsonl"
    for rep in sorted({r["rep"] for r in runs}):
        exp = f"{name}-r{rep}"
        rep_runs = {ids[r["example_key"]]: r for r in runs if r["rep"] == rep}
        tmp.write_text("".join(
            json.dumps({"example_id": eid, "output": r["output"], "error": r["error"] or ""}) + "\n"
            for eid, r in rep_runs.items()
        ))
        _ax("experiments", "create", "--name", exp, "--dataset", DATASET, "--space", space, "--file", str(tmp))
        exported = _ax("experiments", "export", exp, "--dataset", DATASET, "--space", space, "--stdout")
        tmp.write_text(json.dumps([
            {"record_id": e["id"], "values": [
                {"name": n, "label": s["label"], "score": s["score"], "text": s["explanation"]}
                for n, s in rep_runs[e["example_id"]]["scores"].items()
            ]}
            for e in exported if e["example_id"] in rep_runs
        ]))
        _ax("experiments", "annotate-runs", exp, "--dataset", DATASET, "--space", space, "--file", str(tmp))
        print(f"Uploaded experiment {exp}")
    tmp.unlink()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--name", required=True)
    p.add_argument("--reps", type=int, default=3)
    p.add_argument("--split", choices=["train", "test"])
    p.add_argument("--limit", type=int, help="first N rows only, for cheap debugging")
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--no-upload", action="store_true", help="skip creating Arize experiments")
    args = p.parse_args()

    rows = json.loads(GOLDEN.read_text())
    rows = [r for r in rows if not args.split or r["split"] == args.split][: args.limit]
    meter_clients()
    jobs = [(row, rep) for rep in range(1, args.reps + 1) for row in rows]
    print(f"Running {len(rows)} rows × {args.reps} repeats on prompt {PROMPT_VERSION}...")
    with ThreadPoolExecutor(args.workers) as pool:
        runs = list(pool.map(lambda job: run_row(*job, args.name), jobs))
    tracer_provider.force_flush()

    summary = {"prompt_version": PROMPT_VERSION, **summarize(runs)}
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    (out / f"{args.name}.json").write_text(json.dumps({"summary": summary, "runs": runs}, indent=1, ensure_ascii=False))
    md = to_markdown(args.name, summary)
    (out / f"{args.name}.md").write_text(md)
    print(md)
    if not args.no_upload:
        upload(args.name, runs, os.environ["ARIZE_SPACE_ID"])


if __name__ == "__main__":
    main()
