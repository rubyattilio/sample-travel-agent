"""Eval gate on hand-written summaries. No API calls."""

import copy

from experiments.gate import SAFETY, check
from experiments.report import EVAL_NAMES


def spread(mean, lo=None, hi=None):
    return {"mean": mean, "min": mean if lo is None else lo, "max": mean if hi is None else hi}


def summary(rate=0.8, safety=0.8, cost=0.01, p95=5.0):
    evals = {n: spread(safety if n in SAFETY else rate) for n in EVAL_NAMES}
    return {"prompt_version": "v1", "reps": 3, "errors": 0, "cost": {"agent_per_row": cost},
            "latency_s": {"p95": p95}, "splits": {"test": {"row_pass": spread(rate), "evals": evals}}}


def test_gate_allows_noise_but_not_safety_regressions():
    base = summary()
    assert check(base, summary(rate=0.78)) == []  # within MARGIN
    assert check(base, summary(rate=0.7))  # quality dropped past MARGIN
    worse = copy.deepcopy(base)
    worse["splits"]["test"]["evals"]["false_action_claim"]["min"] = 0.6
    assert any("safety" in p for p in check(base, worse))
    assert any("cost" in p for p in check(base, summary(cost=0.02)))


def test_strict_gate_needs_perfect_safety_and_an_improvement():
    base = summary()
    assert check(base, summary(rate=0.8), strict=True)  # no improvement, safety not 100%
    assert check(base, summary(rate=1.0, safety=1.0), strict=True) == []
