"""Tool bugs the evals traced back to code, not the prompt. Each is xfail(strict): fixing the bug makes
the test pass, which fails the suite until the marker is removed, so a fix can't go unnoticed.
No API calls. See docs/bugs.md.
"""

import pytest

from agent.tools import create_itinerary, get_weather, search_flights, search_hotels

bug = pytest.mark.xfail(strict=True)


@bug
def test_flights_respect_direction():
    # Only Los Angeles -> Tokyo exists; the search matches the city pair in either direction.
    assert search_flights("Tokyo", "Los Angeles", "2026-05-02") == []


@bug
def test_hotels_must_be_available_for_the_whole_stay():
    # Le Marais Boutique closes on April 5; only check-in is checked.
    names = {h["name"] for h in search_hotels("Paris", "2026-04-03", "2026-04-07")}
    assert "Le Marais Boutique" not in names


@bug
def test_weather_stays_in_fahrenheit():
    # Fixture highs are already °F, but the tool applies C->F to them (Miami 86 comes back about 80).
    assert 84 <= get_weather("Miami", "2026-07-15")["high_f"] <= 88


@bug
def test_itinerary_has_every_day():
    # range(1, num_days) drops the last day.
    assert len(create_itinerary("Chicago", 3)["days"]) == 3
