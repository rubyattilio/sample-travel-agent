"""The reply never names a competing travel site. Strict on purpose: even a refusal that names one fails."""

import re

NAME = "competitor_mention"

COMPETITORS = [
    "Expedia", "Booking.com", "Kayak", "Skyscanner", "Priceline", "Hotels.com", "Trivago",
    "Orbitz", "Travelocity", "Hopper", "Agoda", "Airbnb", "Vrbo", "Google Flights", "Google Hotels",
    "Trip.com", "Momondo", "Cheapflights",
]
_RE = re.compile(r"\b(" + "|".join(re.escape(c) for c in COMPETITORS) + r")\b", re.IGNORECASE)


def evaluate(run, example=None):
    named = sorted({m.lower() for m in _RE.findall(run["output"])})
    if named:
        return {"label": "fail", "score": 0, "explanation": f"Names competitors: {named}"}
    return {"label": "pass", "score": 1, "explanation": "No competitor named."}
