## Eval gate: ❌ blocked

Held-out `test` split. Baseline prompt v1 vs candidate prompt v2, 3 repeats each. Mean pass rate (min–max across repeats).

| Eval | Baseline | Candidate |
|---|---|---|
| **every eval passes** | 36% (27%–40%) | 44% (40%–47%) |
| grounded_options 🔒 | 83% | 83% |
| facts_correct | 50% | 43% (40%–50%) |
| tool_selection | 80% | 87% (80%–90%) |
| competitor_mention 🔒 | 89% (87%–93%) | 100% |
| false_action_claim 🔒 | 100% | 100% |
| visa_legal_safety 🔒 | 67% (0%–100%) | 100% |
| scope_adherence | 98% (93%–100%) | 100% |
| task_completion | 62% (53%–67%) | 64% (60%–67%) |
| agent cost per row | $0.0032 | $0.0048 |
| p95 latency | 4.89s | 3.36s |

🔒 safety eval: may not get worse in any repeat.

**Blocking:**
- facts_correct: 43% vs baseline 50%

**Warnings (not blocking):**
- ⚠️ agent cost per row $0.0048 is 51% above baseline (budget 25%)
