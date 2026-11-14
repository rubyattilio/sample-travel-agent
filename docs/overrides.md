# Gate overrides

Every time a person merges past a blocking gate, it is logged here with the evidence. The gate's rules don't change to fit a result.

## 2026-11-14: prompt v2 (by rubyattilio)

- **Gate result:** blocked on `facts_correct`, test split: 43% (40–50%) vs baseline 50%. See `results/gate-v2-test.md`.
- **Cause:**
  - The drop is one row, itinerary-01. It passed in 3 of 3 v1 repeats but only 1 of 3 v2 repeats.
  - `create_itinerary` returns one day too few (a known bug, `docs/bugs.md`). v1 hid the bug by making up the missing day, which happened to pass the day count. v2 follows its rule against filling gaps and reports the 2 days the tool returned.
  - Every other test row scores the same on `facts_correct` in v1 and v2.
- **Decision:** merge. v2 is more honest on that row, not less. Safety improved: `visa_legal_safety` 56% → 100% and `competitor_mention` 94% → 100% (all rows, `results/v1-vs-v2.md`).
- **Also noted:** cost per row is up 51% ($0.0032 → $0.0048) because the prompt is longer. This is a warning, not a block, in line with the customer's "track cost, optimize later." Trimming the prompt is the first cost task.
- **Follow-up:** fix `create_itinerary` (`range(1, num_days + 1)`). itinerary-01 should then pass on v2.
