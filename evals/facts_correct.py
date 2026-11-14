"""The reply's flights, hotels, temperatures, day count and cheapest pick match the golden row."""

import json
import re

from evals.extract import flight_numbers, hotel_names

NAME = "facts_correct"


def _options(kind, offered, expected):
    if not expected:
        return [f"offered {kind} {sorted(offered)} but none exist"] if offered else []
    wrong = sorted(offered - set(expected))
    if wrong:
        return [f"{kind} not expected: {wrong}"]
    return [] if offered else [f"none of the expected {kind} {expected} were offered"]


def evaluate(run, example=None):
    facts = (example or {}).get("expected_facts")
    if isinstance(facts, str):  # Arize stores dict fields as JSON strings
        facts = json.loads(facts)
    if not facts:
        return None
    out = run["output"]
    problems = []
    if "flight_numbers" in facts:
        problems += _options("flights", flight_numbers(out), facts["flight_numbers"])
    if "hotel_names" in facts:
        problems += _options("hotels", hotel_names(out), facts["hotel_names"])
    if "high_f" in facts:
        temps = [int(t) for t in re.findall(r"(-?\d+)\s*°?\s*F\b", out)]
        if not temps:
            problems.append("no °F temperatures given")
        else:
            (hi_lo, hi_hi), (lo_lo, lo_hi) = facts["high_f"], facts["low_f"]
            if not hi_lo <= max(temps) <= hi_hi:
                problems.append(f"high {max(temps)}°F outside {hi_lo}-{hi_hi}")
            if not lo_lo <= min(temps) <= lo_hi:
                problems.append(f"low {min(temps)}°F outside {lo_lo}-{lo_hi}")
    if "num_days" in facts:
        days = [int(d) for d in re.findall(r"\bDay\s+(\d+)", out, re.IGNORECASE)]
        if (max(days) if days else 0) != facts["num_days"]:
            problems.append(f"plan covers {max(days) if days else 0} days, expected {facts['num_days']}")
    if "cheapest_hotel" in facts and facts["cheapest_hotel"].lower() not in run["replies"][-1].lower():
        problems.append(f"final reply does not name the cheapest hotel, {facts['cheapest_hotel']}")
    if problems:
        return {"label": "fail", "score": 0, "explanation": "; ".join(problems)}
    return {"label": "pass", "score": 1, "explanation": "All expected facts match."}
