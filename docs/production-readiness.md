# Production readiness

The goal: go from 500 conversations a day to thousands without repeating the customer's history of bad agents reaching production. Each section below says what's in place now and what's needed before launch.

## Where we stand

| | v1 (today's prod prompt) | v2 (merged) |
|---|---|---|
| Every eval passes (46 rows × 3) | 31% | 43% |
| Visa/legal safety | 56% | 100% |
| Competitor mentions | 94% | 100% |
| Made-up booking claims | 100% | 100% |
| Agent cost per conversation | $0.0032 | $0.0048 |
| p95 latency | 4.9s | 3.4s |

**Blocking for launch:** the four tool bugs in `docs/bugs.md`. Flight, weather and itinerary answers are wrong whatever the prompt says, because the tools are wrong.

## 1. Rollout: canary with automatic rollback

Today a merge changes the prompt for every user at once. For production:

- **Version routing.**
  - Serve the prompt by version, keeping v1 and v2 side by side.
  - Assign each session a version (10% canary at first). Every trace already carries `prompt_version` metadata, so Arize can split every metric by version.
- **Promotion.**
  - Canary for 3 days or 1,000 conversations, whichever is later.
  - Promote only if the live safety judges' fail rates are no worse than the current version's.
  - Raise the share in steps: 10% → 50% → 100%.
- **Rollback.**
  - A zero-tolerance monitor firing on the canary version (false booking claim, visa advice) sends all traffic back to the previous version automatically, then pages a person.
  - Rollback is a config flip, not a deploy.

## 2. How much runs without a person

The plan is staged autonomy, as in `docs/automation.md`. Each stage needs a clean record before the next:

| Stage | What's automatic | Who merges | Exit criteria |
|---|---|---|---|
| A (now) | The gate on every PR | A person | 4 weeks, with no regression that passed the gate and then showed up live |
| B | The improver opens prompt PRs weekly | A person | 4 proposals merged without later rollback |
| C | Auto-merge for prompt-only PRs that pass the strict gate, then the canary | Bot, at most 1 a day | Ongoing, with `AUTO_MERGE_ENABLED` as the kill switch |

Code changes, eval changes and golden-set labels always need a person.

## 3. Catching bad replies before users see them

Evals today **detect** problems after the fact. For the zero-tolerance risks, add a cheap check that runs before the reply is sent:

- **Inline, under 10 ms, with no model call:**
  - competitor-name check (`evals/competitor_mention.py`)
  - grounded-options check: every flight and hotel offered must appear in this turn's tool results (`evals/grounded_options.py`)
  - On a hit, regenerate once, then fall back to a safe reply.
- **Async (live judges in Arize):** false-action claims, visa/legal advice, scope. A blocking judge would add about 1s per reply. Revisit if a live monitor ever fires on a zero-tolerance judge.

The evals are already plain functions on a provider-neutral run record, so the same code runs in CI, live and inline.

## 4. Scaling to thousands of conversations a day

| Concern | Today | Needed |
|---|---|---|
| Conversation state | In-memory `dict` in `agent/api.py`: lost on restart, can't run more than one worker | Redis or Postgres, keyed by session ID, with expiry |
| Runaway tool loops | `while True` in `agent/loop.py` | Cap at ~8 tool rounds, then reply with what was found |
| Provider errors | SDK default: 2 retries | Timeouts, retries with backoff, a clear error message for the user, and a monitor on error rate |
| Rate limits | One API key, no plan | Check the Anthropic tier for peak load (~10× the daily average); queue or shed load past it |
| API access | No auth, per the README | Auth plus per-user rate limits |
| Tracing | 100% of spans, batched export | Fine at this scale; sample LLM spans if volume grows 10× |

**Cost** at v2's measured $0.0048 per conversation, plus about $0.0004 for the live judges:
- 500 a day ≈ $2.60 a day
- 5,000 a day ≈ $26 a day (about $800 a month)

Trimming the v2 prompt is the first cost task (see `docs/overrides.md`).

## 5. Monitoring and alerts

Arize monitors on project `travel-agent` (setup in `docs/automation.md`):

- **Page:** any `false_action_claim` or `visa_legal_safety` fail. Zero tolerance.
- **Slack:**
  - `scope_adherence` fail rate above 5% (1-hour window)
  - error rate above 2%
  - p95 latency above 15s
  - cost per day 50% over the trailing week
- **Stakeholder dashboard:**
  - pass rate per live judge over time, split by `prompt_version`
  - conversations per day, cost, latency
  - experiment history (v1 → v2 → ...)

## 6. Trusting the evals

- **Judges are checked on 16 hand-written cases only.**
  - Before launch: put 100 live conversations in an Arize annotation queue, have a person label them, and measure how often each judge agrees.
  - Target: at least 90% agreement on the safety judges; rewrite any judge below that.
  - Repeat monthly.
- **The test split is small** (15 rows), so one row is about 7 points. Visa safety on v1 swung from 0% to 100% between repeats.
  - Grow the golden set to 150+ rows with `scripts/grow_golden.py`.
  - Until then, the gate checks the worst repeat for safety evals.
- **Golden-set growth** only ever adds inputs. A person writes every expected answer. Each labelled batch becomes a new dataset version, and gate comparisons stay on one version.

## 7. Data and security

- **PII in traces.** Traces hold the user's messages. Set a retention policy in Arize, and redact names, emails and passport numbers before export if the customer's policy needs it.
- **Prompt injection.** It's covered by one golden category today. Add rows from live attempts as they're found.
- **Secrets.** These live in GitHub Actions secrets and `.env`, which git ignores. The Anthropic key the live judges use is stored as an Arize AI integration.

## 8. Known shortcuts

Marked `shortcut:` in code. `/ponytail-debt` lists them.

- The flight-number regex assumes airline-code shapes. Hotel checks only know catalog names; an invented hotel is left to the `task_completion` judge.
- Flight fixtures have no dates, so a date mismatch can't be caught.
- The gate in CI doesn't upload experiments to Arize, because the `ax` CLI isn't set up there. Traces still arrive.
- Arize monitors and the dashboard are set up by hand, because the CLI has no monitor commands.

## Launch checklist

- [ ] Fix the four tool bugs, re-run the baseline
- [ ] Persistent conversation store, tool-round cap, timeouts, API auth
- [ ] Inline competitor and grounded checks
- [ ] Version routing, canary and auto-rollback
- [ ] Live judges on, monitors and paging set up, dashboard shared
- [ ] Judge agreement ≥ 90% on 100 human-labelled conversations
- [ ] Golden set ≥ 150 rows
- [ ] PII and retention policy agreed with the customer
