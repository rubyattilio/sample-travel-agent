"""Prompt improver helpers. No API calls."""

import experiments.improve as improve


def test_improver_uses_only_failing_train_rows():
    runs = [
        {"split": "train", "example_key": "flights-01", "output": "x", "scores": {"facts_correct": {"score": 0, "explanation": "wrong"}}},
        {"split": "train", "example_key": "flights-01", "output": "y", "scores": {"facts_correct": {"score": 0, "explanation": "again"}}},
        {"split": "test", "example_key": "flights-02", "output": "z", "scores": {"facts_correct": {"score": 0, "explanation": "held out"}}},
        {"split": "train", "example_key": "hotels-01", "output": "ok", "scores": {"facts_correct": {"score": 1, "explanation": ""}}},
    ]
    fails = improve.failures({"runs": runs})
    assert fails == [{"input": ["Find me a flight from New York to Miami on March 12, 2026."], "reply": "x", "failed": {"facts_correct": "wrong"}}]


def test_improver_rejects_prompts_that_leak_catalog_answers():
    assert improve.leaks("Only offer options your tools return.") == []
    assert improve.leaks("For Miami suggest DL 412 or Hotel Lumière.") == ["DL 412", "Hotel Lumière"]


def test_write_prompt_bumps_version(tmp_path, monkeypatch):
    f = tmp_path / "prompt.py"
    f.write_text('# keep me\nPROMPT_VERSION = "v1"\n\nSYSTEM_PROMPT = """old"""\n')
    monkeypatch.setattr(improve, "PROMPT_FILE", f)
    assert improve.write_prompt("new prompt") == "v2"
    ns = {}
    exec(f.read_text(), ns)
    assert ns["PROMPT_VERSION"] == "v2" and ns["SYSTEM_PROMPT"] == "new prompt\n" and f.read_text().startswith("# keep me")
