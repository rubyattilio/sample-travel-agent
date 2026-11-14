# candidate-v2

Prompt v2, 46 rows × 3 repeats, 0 errors. Pass rates are the mean across repeats (min–max).

| Eval | all | train | test |
|---|---|---|---|
| **every eval passes** | 43% (41%–44%) | 42% | 44% (40%–47%) |
| grounded_options | 95% (94%–95%) | 100% | 83% |
| facts_correct | 36% (34%–38%) | 32% | 43% (40%–50%) |
| tool_selection | 85% (82%–88%) | 85% (83%–88%) | 87% (80%–90%) |
| competitor_mention | 100% | 100% | 100% |
| false_action_claim | 100% | 100% | 100% |
| visa_legal_safety | 100% | 100% | 100% |
| scope_adherence | 100% | 100% | 100% |
| task_completion | 76% (74%–78%) | 82% (81%–84%) | 64% (60%–67%) |

| Category | Rows where every eval passes |
|---|---|
| competitor | 67% |
| false_action | 44% |
| flights | 0% |
| hotels | 43% |
| itinerary | 0% |
| multi_turn | 33% |
| no_data | 60% |
| off_topic | 100% |
| prompt_injection | 100% |
| relative_date | 67% |
| visa_legal | 100% |
| weather | 0% |

Cost: agent $0.66 ($0.0048 per row), judges $0.07. Latency per row: p50 2.04s, p95 3.36s.
