"""Experiment runner, with the agent and judges stubbed out. No API calls."""

from types import SimpleNamespace

import experiments.run as runner

ROW = {"example_key": "flights-01", "split": "test", "category": "flights", "turns": ["a", "b"]}


def test_run_row_runs_every_turn_and_scores(monkeypatch):
    seen = []

    def fake_agent(messages):
        seen.append(messages[-1]["content"])
        return "ok", messages + [{"role": "assistant", "content": [{"type": "text", "text": "ok"}]}]

    monkeypatch.setattr(runner.agent.loop, "run_agent", fake_agent)
    monkeypatch.setattr(runner, "run_all", lambda record, row: {"e": {"label": "pass", "score": 1, "explanation": ""}})
    r = runner.run_row(ROW, 1, "t")
    assert seen == ["a", "b"] and r["output"] == "ok\n---\nok" and r["scores"]["e"]["score"] == 1 and r["error"] is None


def test_run_row_reports_agent_errors(monkeypatch):
    monkeypatch.setattr(runner.agent.loop, "run_agent", lambda m: 1 / 0)
    r = runner.run_row(ROW, 1, "t")
    assert "ZeroDivisionError" in r["error"] and r["scores"] == {}


def test_metered_prices_each_call():
    usage = SimpleNamespace(input_tokens=1_000_000, output_tokens=100_000)
    call = runner._metered(lambda **kw: SimpleNamespace(usage=usage), "agent")
    runner._cost.agent = 0.0
    call(model="claude-haiku-4-5")
    assert round(runner._cost.agent, 6) == 1.5
