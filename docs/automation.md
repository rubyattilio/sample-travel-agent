# The feedback loop

```
live traffic ──► Arize traces ──► live safety judges ──► monitors ──► alert engineers
      ▲                                  │
      │                         failing inputs ──► golden_candidates.json ──► human labels ──► golden v2
      │
  merge ◄── eval gate (held-out split) ◄── PR ◄── improve.py (weekly, train split)
```

| Piece | What runs | When | Cost |
|---|---|---|---|
| Eval gate | `.github/workflows/eval-gate.yml`: test split × 3 repeats vs `results/baseline-v1.json`, table posted on the PR | Every PR touching the agent, evals or data, once it is out of draft | about $0.35 |
| Live judges | `scripts/setup_live_evals.py`: `false_action_claim`, `visa_legal_safety`, `scope_adherence` as a continuous Arize task on every agent span | Continuously, in Arize | about $0.0005 per conversation |
| Improver | `.github/workflows/improve.yml`: train split × 1, `experiments.improve` proposes a prompt and opens an `auto-prompt` PR, then starts the gate | Mondays 14:00 UTC | about $0.30 plus the gate |
| Golden growth | `scripts/grow_golden.py`: failing live inputs → `data/golden_candidates.json` | By hand, weekly | free |

## Switches

Everything that spends money or merges code is off until switched on in **Settings → Secrets and variables → Actions**:

- Secrets `ANTHROPIC_API_KEY`, `ARIZE_API_KEY`, `ARIZE_SPACE_ID`: without them nothing can run.
- Variable `AUTO_IMPROVE_ENABLED=true`: turns on the weekly improver.
- Variable `AUTO_MERGE_ENABLED=true`: lets the gate merge PRs itself. Deleting it is the kill switch.

## Staged autonomy

Each stage starts only after the one before has a clean record:

- **A. Gate only.** People write PRs; the gate comments and blocks regressions.
- **B. Proposed PRs.** The improver opens `auto-prompt` PRs; a person reviews and merges.
- **C. Auto-merge.** The gate merges an `auto-prompt` PR only when all of these hold:
  - it changes only `agent/prompt.py`
  - it clears `experiments.gate --strict`: safety evals at 100% in every repeat, a clear improvement on the held-out split, and cost and latency within budget
  - no other auto-merge happened in the past day

  Code changes always need a person.

## Alerts

The Arize CLI has no monitor commands, so monitors are set up once in the Arize UI. On project `travel-agent`, go to **Monitors → New monitor** and create one per live judge:

- **Metric:** the share of spans labelled `fail` by `false_action_claim`, `visa_legal_safety` or `scope_adherence`.
- **Threshold:** above 0 for `false_action_claim` and `visa_legal_safety` (zero tolerance), above 5% for `scope_adherence`, over a 1-hour window.
- **Also monitor:** error rate above 2% and p95 latency above 15s on the `travel_agent` span.
- **Notify:** Slack or email (PagerDuty for the zero-tolerance ones).

A failed gate run also notifies the PR author through GitHub.

## Growing the golden set

- Failing live inputs are **added** as candidates. Expected answers are **never** written automatically.
- A person labels each candidate, checking it against the fixtures in `data/` and paying extra attention to visa, legal and booking rows. Labelled rows become `golden_v2` and a new version of the Arize dataset.
- The gate always compares the candidate and the baseline on the same dataset version.
- The headline before/after numbers stay pinned to v1.
