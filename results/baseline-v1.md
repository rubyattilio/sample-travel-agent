# baseline-v1

Prompt v1, 46 rows × 3 repeats, 0 errors. Pass rates are the mean across repeats (min–max).

| Eval | all | train | test |
|---|---|---|---|
| **every eval passes** | 31% (28%–33%) | 29% | 36% (27%–40%) |
| grounded_options | 91% (90%–94%) | 95% (92%–100%) | 83% |
| facts_correct | 39% (38%–41%) | 33% (32%–37%) | 50% |
| tool_selection | 76% | 75% | 80% |
| competitor_mention | 94% (91%–96%) | 96% (94%–97%) | 89% (87%–93%) |
| false_action_claim | 100% | 100% | 100% |
| visa_legal_safety | 56% (33%–67%) | 50% | 67% (0%–100%) |
| scope_adherence | 97% (96%–98%) | 97% | 98% (93%–100%) |
| task_completion | 64% (61%–67%) | 66% (64%–68%) | 62% (53%–67%) |

| Category | Rows where every eval passes |
|---|---|
| competitor | 33% |
| false_action | 33% |
| flights | 0% |
| hotels | 38% |
| itinerary | 44% |
| multi_turn | 33% |
| no_data | 40% |
| off_topic | 56% |
| prompt_injection | 100% |
| relative_date | 0% |
| visa_legal | 56% |
| weather | 0% |

Cost: agent $0.43 ($0.0032 per row), judges $0.08. Latency per row: p50 2.41s, p95 4.89s.
