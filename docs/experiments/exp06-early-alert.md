[← All experiments](../../README.md#experiments)

# Experiment 6 (pre-registered 2026-11-01): an early alert for the model

**Why.** In Experiment 2 the model heeded the `critical` alert on 43 of 44 alerted decisions, but survived only 1/10: the alert came after the role was already too thin to rebuild. In Experiment 4 the designed `forecast` rule, which acts on cells still alive 10 ticks ahead and skips births when nothing is needed, survived 10/10. Is the missing ingredient for the model the timing of the signal, or the rule itself?

**Change.** New policy `outlook`: the model chooses from the plain census, plus an alert listing every role with 2 or fewer cells still alive 10 ticks from now (`forecast`'s trigger, given as information). Silent otherwise. The model may also answer `none` to skip a birth, which `forecast` does when no role is short. That changes two things versus `critical` (timing and skipping), chosen so the model has what the designed rule has.

**Design.** Seeds 10–19, 100 ticks, `forecast_lead` 10, `qwen3:4b-instruct`, everything else default. Baselines on the same seeds: `critical` 1/10, `demand` 3/10, `forecast` lead 10 10/10.

**Predictions**, written before running:
- `outlook` survives on more seeds than `critical` (1/10) and `demand` (3/10).
- `outlook` survives on at least 7/10 seeds: close to, but possibly below, `forecast`.
- The model follows the alert on at least 80% of alerted decisions, as it did with `critical`.
- Remaining collapses, if any, trace to energy (the model rarely answers `none` and spends the pool on unneeded births) rather than to ignored alerts.

**Results** (`runs/exp6-outlook`, 10 runs, no failures; collapses attributed with `python -m autopoiesis.collapse`):

| Policy (seeds 10–19) | Survived 100 ticks | Collapses |
|---|---|---|
| `critical` (Exp. 2) | 1/10 | |
| `demand` (Exp. 2) | 3/10 | |
| `warning` (Exp. 2) | 5/10 | |
| `outlook` | **5/10** | regulation 4 (ticks 26–81), other 1 (tick 47) |
| `forecast`, lead 10 (Exp. 4) | 10/10 | none |

| Prediction | Result |
|---|---|
| Survives on more seeds than `critical` and `demand` | **Met:** 5/10 vs 1/10 and 3/10 |
| Survives on at least 7/10 | **Not met:** 5/10 |
| Follows the alert on at least 80% of alerted decisions | **Not met:** 231 of 380 (61%); of the 306 births, 75% went to a flagged role |
| Remaining collapses trace to energy | **Not met:** 4 of 5 are regulation (births went to other roles while the lost role aged out) |

- **The alert was never silent.** Some role had 2 or fewer cells still alive 10 ticks ahead on all 380 decisions. Each role starts with 2 cells, and the population rarely grows far beyond the floor. An alert that is always on carries little information: this is the same failure as `warning` in Experiment 2, and `outlook` landed on the same 5/10.
- **The model used `none` where the rule would not.** It skipped 74 births (19%), every one while a role was flagged. `forecast` never skips while a role is short.
- **What the designed rule has that the model lacked is a ranking, not just timing.** `forecast` picks the most endangered role among several flagged ones; the model, shown 2–4 flagged roles at once, spread its births across them and across unflagged roles.
- **Next:** alert only on the single most endangered role (fewest cells still alive at the lead), so the signal is rare and specific again, or make the floor relative to the population.
