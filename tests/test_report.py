"""Experiment report summaries on hand-written runs. No API calls."""

from experiments.report import summarize, to_markdown


def fake_run(rep, key, split, category, scores, error=None, latency=1.0):
    return {"rep": rep, "example_key": key, "split": split, "category": category, "output": "", "tool_calls": [],
            "scores": {n: {"label": "x", "score": s, "explanation": ""} for n, s in scores.items()},
            "error": error, "latency_s": latency, "agent_cost": 0.01, "judge_cost": 0.001}


def test_summarize_and_markdown():
    runs = [
        fake_run(1, "a", "train", "flights", {"facts_correct": 1, "tool_selection": 1}),
        fake_run(1, "b", "test", "hotels", {"facts_correct": 0}),
        fake_run(2, "a", "train", "flights", {"facts_correct": 0, "tool_selection": 1}),
        fake_run(2, "b", "test", "hotels", {}, error="boom", latency=9.0),
    ]
    s = summarize(runs)
    assert s["reps"] == 2 and s["rows"] == 2 and s["errors"] == 1
    assert s["splits"]["all"]["evals"]["facts_correct"] == {"mean": 0.25, "min": 0.0, "max": 0.5}
    assert s["splits"]["train"]["row_pass"] == {"mean": 0.5, "min": 0.0, "max": 1.0}
    assert s["splits"]["test"]["evals"]["tool_selection"] is None  # never applicable on test
    assert s["categories"] == {"flights": 0.5, "hotels": 0.0}
    assert s["cost"]["agent"] == 0.04 and s["latency_s"]["p95"] == 9.0
    md = to_markdown("x", {"prompt_version": "v1", **s})
    assert "| facts_correct | 25% (0%–50%) | 50% (0%–100%) | 0% |" in md
