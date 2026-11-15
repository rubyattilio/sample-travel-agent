# Proposal (prompt v2)

Recovered from the terminal output of the 2026-11-14 run, before the improver saved proposals or had a `tool_bugs` field.

## Analysis (tool-bug findings, condensed)

- **Flights:** search_flights returns rows that don't match the request (reversed direction, wrong route or date), and the agent lists them. "That the tool returns non-matching rows at all looks like a tool or filtering bug, and it should be reported to the tool owners."
- **Hotels:** one hotel's availability window didn't cover the full stay, but it was listed anyway.
- **Weather:** reported highs and lows fell outside the expected ranges. Possibly a tool bug: wrong units, or values for another date or city.
- **Itinerary:** create_itinerary returned fewer days than requested, "which is a tool bug and should be reported."

The rest of the analysis (embellishment, not calling tools, booking-request handling, legal rules, scope) drove the prompt changes now in `agent/prompt.py`.

## Tool bugs

- **search_flights**: returns flights in the reverse direction (flights-05, flights-06)
- **search_hotels**: ignores check-out, so it offers hotels that close mid-stay (hotels-04, hotels-05)
- **get_weather**: temperatures outside the forecast range (weather rows)
- **create_itinerary**: returns one day fewer than requested (itinerary-01 to itinerary-03)
