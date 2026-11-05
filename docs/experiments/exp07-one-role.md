[← All experiments](../../README.md#experiments)

# Experiment 7 (pre-registered 2026-11-01): one role at a time

**Why.** In Experiment 6 the `outlook` alert listed every role with 2 or fewer cells alive 10 ticks ahead. It fired on all 380 decisions, usually naming 2–4 roles, and the model spread its births across them (5/10 survived). `forecast` acts on the same trigger but builds only the most endangered role.

**Change.** New policy `focus`: identical to `outlook` (plain census, may answer `none`), except the alert names only the single most endangered role: fewest cells still alive 10 ticks ahead, ties broken by which dies out soonest. One change versus Experiment 6.

**Design.** Seeds 10–19, 100 ticks, `forecast_lead` 10, `qwen3:4b-instruct`, everything else default.

**Predictions**, written before running:
- `focus` survives on more seeds than `outlook` (5/10).
- The model builds the named role on at least 75% of alerted decisions (vs 61% for `outlook`).
- The alert still fires on nearly every decision, so its effect comes from being specific, not rare.
- Skipping while a role is flagged (`none`) stays a cause of loss; collapses, if any, are mostly regulation.

**Results** (`runs/exp7-focus`, 10 runs, no failures; the GPU peaked at 84°C and the guard never paused):

| Policy (seeds 10–19) | Survived 100 ticks | Collapses |
|---|---|---|
| `critical` (Exp. 2) | 1/10 | |
| `outlook` (Exp. 6) | 5/10 | regulation 4, other 1, at ticks 26–81 |
| `focus` | **6/10** | energy 2 (ticks 95, 99), regulation 1 (tick 88), damage 1 (tick 39) |
| `forecast`, lead 10 (Exp. 4) | 10/10 | none |

| Prediction | Result |
|---|---|
| Survives on more seeds than `outlook` (5/10) | **Met, barely:** 6/10, well within seed noise |
| Builds the named role on ≥ 75% of alerted decisions | **Not met:** 299 of 439 (68%), up from 61% |
| The alert still fires on nearly every decision | **Met:** 439 of 460 (95%) |
| Collapses are mostly regulation; skipping stays a cause | **Not met:** 1 of 4 is regulation; skips fell from 74 (19%) to 26 (6%) |

- **Naming one role changed how the town fails, more than how often.** With `outlook`, 4 of 5 collapses were regulation, at ticks 26–81. With `focus`, 3 of 4 collapses came at ticks 88–99, and two of those were energy: the pool could not fund any birth in the 9 ticks before the loss.
- **The model skipped far less.** With one named role it answered `none` on 6% of decisions, against 19% with a list.
- **The model still diverged from the alert on about a third of decisions.** The designed rule, which never diverges, survived 10/10. Most of the remaining gap is that, not timing.
- **Conclusion for the town so far:** a local signal that is early and names one role gets a 4B model from 1/10 to 6/10 without any rule. Matching the designed rule needs the model to act on the signal more reliably, or the signal to be the decision.
