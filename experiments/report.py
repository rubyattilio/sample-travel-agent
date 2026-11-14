"""Summaries of a results file: pass rates per eval and split, per category, cost and latency. No API calls."""

import statistics

from evals import ALL_EVALS

EVAL_NAMES = [e.NAME for e in ALL_EVALS]


def _rate(runs, eval_name):
    scored = [r["scores"][eval_name]["score"] for r in runs if eval_name in r["scores"]]
    return sum(scored) / len(scored) if scored else None


def _spread(per_rep):
    vals = [v for v in per_rep if v is not None]
    if not vals:
        return None
    return {"mean": round(statistics.mean(vals), 3), "min": round(min(vals), 3), "max": round(max(vals), 3)}


def _row_pass(r):
    return r["error"] is None and all(s["score"] == 1 for s in r["scores"].values())


def summarize(runs):
    """Pass rates per eval and split (mean and min-max across repeats), per category, cost and latency."""
    reps = sorted({r["rep"] for r in runs})
    out = {"reps": len(reps), "rows": len({r["example_key"] for r in runs}), "splits": {}, "categories": {}}
    for split in ("all", "train", "test"):
        split_runs = [r for r in runs if split == "all" or r["split"] == split]
        if not split_runs:
            continue
        by_rep = [[r for r in split_runs if r["rep"] == rep] for rep in reps]
        out["splits"][split] = {
            "row_pass": _spread([sum(map(_row_pass, rr)) / len(rr) for rr in by_rep]),
            "evals": {n: _spread([_rate(rr, n) for rr in by_rep]) for n in EVAL_NAMES},
        }
    for cat in sorted({r["category"] for r in runs}):
        cat_runs = [r for r in runs if r["category"] == cat]
        out["categories"][cat] = round(sum(map(_row_pass, cat_runs)) / len(cat_runs), 3)
    latencies = sorted(r["latency_s"] for r in runs)
    out["errors"] = sum(r["error"] is not None for r in runs)
    out["cost"] = {
        "agent": round(sum(r["agent_cost"] for r in runs), 4),
        "judge": round(sum(r["judge_cost"] for r in runs), 4),
        "agent_per_row": round(sum(r["agent_cost"] for r in runs) / len(runs), 5),
    }
    out["latency_s"] = {"p50": latencies[len(latencies) // 2], "p95": latencies[int(len(latencies) * 0.95)]}
    return out


def _fmt(s):
    if s is None:
        return "n/a"
    if s["min"] == s["max"]:
        return f"{s['mean']:.0%}"
    return f"{s['mean']:.0%} ({s['min']:.0%}–{s['max']:.0%})"


def to_markdown(name, summary):
    splits = list(summary["splits"])
    lines = [
        f"# {name}",
        "",
        f"Prompt {summary['prompt_version']}, {summary['rows']} rows × {summary['reps']} repeats, "
        f"{summary['errors']} errors. Pass rates are the mean across repeats (min–max).",
        "",
        "| Eval | " + " | ".join(splits) + " |",
        "|---|" + "---|" * len(splits),
        "| **every eval passes** | " + " | ".join(_fmt(summary["splits"][s]["row_pass"]) for s in splits) + " |",
    ]
    for n in EVAL_NAMES:
        lines.append(f"| {n} | " + " | ".join(_fmt(summary["splits"][s]["evals"][n]) for s in splits) + " |")
    lines += ["", "| Category | Rows where every eval passes |", "|---|---|"]
    lines += [f"| {c} | {v:.0%} |" for c, v in summary["categories"].items()]
    cost, lat = summary["cost"], summary["latency_s"]
    lines += [
        "",
        f"Cost: agent ${cost['agent']:.2f} (${cost['agent_per_row']:.4f} per row), judges ${cost['judge']:.2f}. "
        f"Latency per row: p50 {lat['p50']}s, p95 {lat['p95']}s.",
    ]
    return "\n".join(lines) + "\n"
