"""Pull bookable entities out of reply text, for the code evals."""

import json
import re
from pathlib import Path

# The customer's catalog: the only hotels the agent may ever offer.
CATALOG_HOTELS = [h["name"] for h in json.loads((Path(__file__).resolve().parent.parent / "data" / "hotels.json").read_text())]

# shortcut: matches airline-code shapes like "DL 883" / "B6 1029"; widen if real flight numbers differ.
FLIGHT_RE = re.compile(r"\b(?:[A-Z]{2}|[A-Z][0-9]|[0-9][A-Z])\s?\d{1,4}\b")


def flight_numbers(text: str) -> set[str]:
    return {f"{m[:2]} {m[2:].strip()}" for m in FLIGHT_RE.findall(text)}  # "DL883" -> "DL 883"


def hotel_names(text: str) -> set[str]:
    # shortcut: only recognises catalog hotels; an invented hotel name is left to the task_completion judge.
    return {name for name in CATALOG_HOTELS if name.lower() in text.lower()}


def tool_text(run: dict) -> str:
    return json.dumps([c["result"] for c in run["tool_calls"]], ensure_ascii=False)
