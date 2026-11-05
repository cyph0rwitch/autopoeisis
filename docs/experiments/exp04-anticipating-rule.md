[← All experiments](../../README.md#experiments)

# Experiment 4 (pre-registered 2026-10-29): a designed rule that anticipates

**Why.** `demand` lost a role at ticks 60–95 on 7 of 10 seeds in Experiment 2. In every case the lost role was a single cohort: 3–7 cells born within a few ticks of each other (usually after a burst of membrane overload), all due to die of old age on the same tick. Ten ticks earlier `demand` saw a healthy count and reported `no_need`, or production was blocked by the population cap or energy. Its floor counts cells now, not cells that will still be alive.

**Change.** New designed policy `forecast`: the same as `demand`, but the floor counts only cells still alive `forecast_lead` ticks from now. A role is rebuilt before its cohort ages out.

**Design.** Seeds 10–19 (the same seeds as Experiment 2, so `demand` serves as the paired baseline), 100 ticks, `forecast_lead` 10 and 15, `qwen3:4b-instruct`, everything else default.

**Predictions**, written before running:
- `forecast` with lead 15 survives on at least 8/10 seeds.
- `forecast` with lead 10 survives on more seeds than `demand` (3/10). It may still fail where the population is at its cap when a cohort is about to die, because no birth fits until something dies.
- Remaining collapses, if any, are energy or cap, not the cohort-ageing pattern above.

**Results** (`runs/exp4-forecast-lead10`, `runs/exp4-forecast-lead15`; `demand` from Experiment 2 on the same seeds):

| Policy | Survived 100 ticks | Collapses |
|---|---|---|
| `demand` | 3/10 | 7, at ticks 60–95 (cohort ageing) |
| `forecast`, lead 10 | **10/10** | none |
| `forecast`, lead 15 | 9/10 | 1, at tick 30 |

| Prediction | Result |
|---|---|
| Lead 15 survives ≥ 8/10 | **Met:** 9/10 |
| Lead 10 survives on more seeds than `demand` | **Met:** 10/10 vs 3/10 |
| Remaining collapses are energy or cap, not cohort ageing | **Met:** the one collapse (lead 15, seed 10, tick 30) lost the last seed-cohort metabolizer while the pool sat below the birth threshold for 6 of the 9 preceding ticks |

- **Counting cells that will still be alive, rather than cells alive now, removes the cohort-ageing failure.** It's the designed counterpart of Experiment 2's lesson: the regulating signal has to lead the system's response time.
- **Next for the town:** give the model this forward-looking information (cells alive in 10 ticks, per role) instead of a late alarm, and see whether an LLM producer can match `forecast`.
