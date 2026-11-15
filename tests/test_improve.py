"""Prompt improver helpers. No API calls."""

import json

import experiments.improve as improve


def test_improver_uses_only_failing_train_rows():
    runs = [
        {"split": "train", "example_key": "flights-01", "output": "x", "scores": {"facts_correct": {"score": 0, "explanation": "wrong"}}},
        {"split": "train", "example_key": "flights-01", "output": "y", "scores": {"facts_correct": {"score": 0, "explanation": "again"}}},
        {"split": "test", "example_key": "flights-02", "output": "z", "scores": {"facts_correct": {"score": 0, "explanation": "held out"}}},
        {"split": "train", "example_key": "hotels-01", "output": "ok", "scores": {"facts_correct": {"score": 1, "explanation": ""}}},
    ]
    for r in runs:
        r["rep"] = 1
    fails = improve.failures({"runs": runs}, "baseline-v1")
    assert fails == [{"example_key": "flights-01", "session": "baseline-v1-r1-flights-01",
                      "input": ["Find me a flight from New York to Miami on March 12, 2026."], "reply": "x",
                      "failed": {"facts_correct": "wrong"}}]


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


FAILS = [{"example_key": "flights-05", "session": "b-r1-flights-05", "failed": {"facts_correct": "offered NH 105"}}]
BUGS = [
    improve.ToolBug(tool="search_flights", symptom="Returns the reverse direction.", example_keys=["flights-05"]),
    improve.ToolBug(tool="create_itinerary", symptom="One day short.", example_keys=["itinerary-01"]),
]


def test_file_issues_creates_new_and_comments_on_open_ones(monkeypatch):
    calls = []

    def fake_gh(*args):
        calls.append(args)
        return json.dumps([{"number": 7, "title": "Tool bug in search_flights"}]) if args[:2] == ("issue", "list") else ""

    monkeypatch.setattr(improve, "_gh", fake_gh)
    improve.file_issues(BUGS, FAILS)
    comment = next(c for c in calls if c[:2] == ("issue", "comment"))
    assert comment[2] == "7" and "b-r1-flights-05" in comment[4] and "offered NH 105" in comment[4]
    create = next(c for c in calls if c[:2] == ("issue", "create"))
    assert "Tool bug in create_itinerary" in create and "tool-bug" in create
    assert sum(c[:2] == ("issue", "create") for c in calls) == 1  # no duplicate for search_flights


def test_save_proposal_keeps_analysis_and_bugs(tmp_path):
    f = tmp_path / "p.md"
    improve.save_proposal(f, improve.Proposal(analysis="why", tool_bugs=BUGS, change_summary="what", system_prompt="p"))
    text = f.read_text()
    assert "why" in text and "**search_flights**: Returns the reverse direction. (flights-05)" in text
