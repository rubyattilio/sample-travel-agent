# Bugs the loop found in code

A better prompt can't fix these. The improver is told to report them instead of working around them: with `--file-issues` (the weekly workflow) it opens or updates one `tool-bug` GitHub issue per tool, with the failing rows and their Arize session IDs. Fixing them stays with a person. Each one has a strict-xfail test in `tests/test_tool_bugs.py`, so the fix shows up when it lands. Trace links get filled in from the baseline-v1 run.

| Bug | Where | Caught by | Golden rows | Fix |
|---|---|---|---|---|
| Flight search ignores direction: Tokyo → LA returns the LA → Tokyo flight | `search_flights`: compares city sets | `facts_correct` | flights-05, flights-06 | match `origin` and `destination` separately |
| Hotel search ignores check-out: offers hotels that close mid-stay | `search_hotels`: checks only `check_in` | `facts_correct`, `task_completion` | hotels-04, hotels-05 | also require `check_out <= available_to` |
| Weather converts °F as if it were °C: Miami 86°F comes back about 80°F | `get_weather`: `* 5 / 9 + 32` | `facts_correct` | weather rows | drop the conversion |
| Itinerary is one day short | `create_itinerary`: `range(1, num_days)` | `facts_correct` | itinerary-01 to itinerary-03 | `range(1, num_days + 1)` |

## Release rule

A tool fix is a code change, so it goes through the normal PR gate with a person's review and is never auto-merged. Once it merges:

1. Re-run the baseline as `baseline-v1-fixed`.
2. Keep the prompt-only before/after numbers separate from the bug-fix numbers, so each improvement is credited to the right change.
