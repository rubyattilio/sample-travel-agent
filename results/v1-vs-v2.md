## Eval gate: ✅ passed

Held-out `all` split. Baseline prompt v1 vs candidate prompt v2, 3 repeats each. Mean pass rate (min–max across repeats).

| Eval | Baseline | Candidate |
|---|---|---|
| **every eval passes** | 31% (28%–33%) | 43% (41%–44%) |
| grounded_options 🔒 | 91% (90%–94%) | 95% (94%–95%) |
| facts_correct | 39% (38%–41%) | 36% (34%–38%) |
| tool_selection | 76% | 85% (82%–88%) |
| competitor_mention 🔒 | 94% (91%–96%) | 100% |
| false_action_claim 🔒 | 100% | 100% |
| visa_legal_safety 🔒 | 56% (33%–67%) | 100% |
| scope_adherence | 97% (96%–98%) | 100% |
| task_completion | 64% (61%–67%) | 76% (74%–78%) |
| agent cost per row | $0.0032 | $0.0048 |
| p95 latency | 4.89s | 3.36s |

🔒 safety eval: may not get worse in any repeat.

**Warnings (not blocking):**
- ⚠️ agent cost per row $0.0048 is 51% above baseline (budget 25%)
