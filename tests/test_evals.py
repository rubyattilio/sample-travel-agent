"""Code evals and the message adapter, on hand-written runs. No API calls."""

from evals import competitor_mention, facts_correct, grounded_options, tool_selection
from evals.record import from_messages

NY_MIAMI = [{"airline": "Delta", "flight_number": "DL 883"}, {"airline": "JetBlue", "flight_number": "B6 1029"}]


def run(output, tool_calls=(), replies=None):
    return {"input": "q", "output": output, "replies": replies or [output], "tool_calls": list(tool_calls)}


def call(name, result):
    return {"name": name, "args": {}, "result": result}


def label(result):
    return result and result["label"]


def test_from_messages_builds_record():
    messages = [
        {"role": "user", "content": "flights NY to Miami"},
        {"role": "assistant", "content": [{"type": "tool_use", "id": "t1", "name": "search_flights", "input": {"origin": "New York"}}]},
        {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "t1", "content": '[{"flight_number": "DL 883"}]'}]},
        {"role": "assistant", "content": [{"type": "text", "text": "DL 883 at 9:40."}]},
        {"role": "user", "content": "thanks"},
        {"role": "assistant", "content": [{"type": "text", "text": "Anytime!"}]},
    ]
    r = from_messages(messages)
    assert r["input"] == "flights NY to Miami\n---\nthanks"
    assert r["replies"] == ["DL 883 at 9:40.", "Anytime!"]
    assert r["tool_calls"] == [{"name": "search_flights", "args": {"origin": "New York"}, "result": [{"flight_number": "DL 883"}]}]


def test_grounded_options():
    found = [call("search_flights", NY_MIAMI)]
    assert label(grounded_options.evaluate(run("Try DL 883 or B6 1029.", found))) == "pass"
    assert label(grounded_options.evaluate(run("Try DL 883 or AA 999.", found))) == "fail"  # invented flight
    assert label(grounded_options.evaluate(run("Ocean Drive Resort is lovely.", found))) == "fail"  # hotel never searched
    assert grounded_options.evaluate(run("Sorry, nothing found.")) is None  # nothing offered


def test_facts_correct_flights_including_reverse_direction_trap():
    expected = {"expected_facts": {"flight_numbers": ["DL 883", "B6 1029"]}}
    assert label(facts_correct.evaluate(run("DL 883 and B6 1029"), expected)) == "pass"
    assert label(facts_correct.evaluate(run("DL883 only"), expected)) == "pass"  # partial list is fine
    assert label(facts_correct.evaluate(run("No flights found."), expected)) == "fail"
    trap = {"expected_facts": {"flight_numbers": []}}  # Tokyo -> LA only exists reversed
    assert label(facts_correct.evaluate(run("Take NH 6 from Tokyo."), trap)) == "fail"
    assert label(facts_correct.evaluate(run("No direct flights on that route."), trap)) == "pass"


def test_facts_correct_hotels_past_availability():
    expected = {"expected_facts": '{"hotel_names": ["Hotel Lumière"]}'}  # JSON string, as Arize stores it
    assert label(facts_correct.evaluate(run("Hotel Lumière is available."), expected)) == "pass"
    assert label(facts_correct.evaluate(run("Hotel Lumière or Le Marais Boutique."), expected)) == "fail"


def test_facts_correct_weather_itinerary_and_cheapest():
    miami = {"expected_facts": {"high_f": [84, 88], "low_f": [72, 76]}}
    assert label(facts_correct.evaluate(run("High of 86°F, low of 74°F."), miami)) == "pass"
    assert label(facts_correct.evaluate(run("High of 80°F, low of 73°F."), miami)) == "fail"  # conversion bug
    three_days = {"expected_facts": {"num_days": 3}}
    assert label(facts_correct.evaluate(run("Day 1: x\nDay 2: y\nDay 3: z"), three_days)) == "pass"
    assert label(facts_correct.evaluate(run("Day 1: x\nDay 2: y"), three_days)) == "fail"  # off-by-one bug
    cheapest = {"expected_facts": {"hotel_names": ["A Hotel"], "cheapest_hotel": "The Loop Central"}}
    r = run("The Loop Central", replies=["...", "The Loop Central is cheapest."])
    assert "cheapest" not in facts_correct.evaluate(r, cheapest)["explanation"]
    assert facts_correct.evaluate(run("x"), None) is None


def test_tool_selection():
    example = {"expected_tools": '["search_flights", "search_hotels"]'}
    assert label(tool_selection.evaluate(run("x", [call("search_flights", []), call("search_hotels", [])]), example)) == "pass"
    assert label(tool_selection.evaluate(run("x", [call("search_flights", [])]), example)) == "fail"
    assert tool_selection.evaluate(run("x"), {"expected_tools": []}) is None


def test_competitor_mention():
    assert label(competitor_mention.evaluate(run("Here are my options for you."))) == "pass"
    assert label(competitor_mention.evaluate(run("You could also check expedia."))) == "fail"
    assert label(competitor_mention.evaluate(run("Try Booking.com"))) == "fail"
