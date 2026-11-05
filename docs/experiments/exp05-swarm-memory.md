[← All experiments](../../README.md#experiments)

# Experiment 5 (pre-registered 2026-10-30): swarm memory

**Question.** Real multi-agent systems often share one memory (a scratchpad, a knowledge base). With `--shared-memory`, every agent reads and writes one team board of 10 notes, so one poisoned note reaches every agent at once. Does closing or filtering the channel still beat detecting what flows through it?

**Design.** Same tasks, attacks, model and seeds as Experiment 3 (mixed tasks, 33 per run, disguised attacks, gatekeeper on, CI feedback, seeds 0–9). Arms: shared free notes; shared notes with the provenance filter; shared free notes with detection-based healing (the medic also filters the board at every health check). The Experiment 3 no-notes and private-notes arms serve as references. New measure: `exposure_rate_clean`, the share of clean tasks whose workers read memory that carried a payload.

**Predictions**, written before running:
- Shared free notes expose more clean tasks than private free notes, and hijack at least as many.
- The provenance filter brings shared-memory hijacks on clean tasks to no more than 2%, as for private memory, though exposure stays above zero because the literal-free `lenient` payload passes it.
- Healing on a shared board does worse than the filter on clean-task hijacks.

**Results** (`runs/exp5-swarm`, 10 seeds per arm; one crashed run was rerun after a fix, see `df31c3a`):

| Memory | Later clean tasks hijacked | Clean tasks exposed to payload text | Agents compromised at end | Pass rate | Calls per task |
|---|---|---|---|---|---|
| shared, free | **23%** [11, 37] | 34% | 7.2 | 0.71 | 10.7 |
| shared, healing | 10% [3, 17] | 17% | 1.6 | 0.66 | 17.1 |
| shared, filtered | **0%** [0, 0] | **0%** | 0 | 0.70 | 10.7 |
| private, free (Exp. 3) | 13% [5, 21] | – | 4.2 | 0.81 | 10.7 |
| none (Exp. 3) | 0% | – | 0 | 0.82 | 5.3 |

| Prediction | Result |
|---|---|
| Shared free notes spread more than private free notes | **Met in direction:** 23% vs 13% of clean tasks hijacked, 7.2 vs 4.2 agents compromised. The intervals overlap. |
| The filter keeps shared-memory clean-task hijacks ≤ 2% | **Met:** 0% on every seed |
| Exposure stays above zero because `lenient` passes the filter | **Not met:** 0% exposure. The model never wrote `lenient` to the board. |
| Healing on a shared board does worse than the filter | **Met:** 10% vs 0%, at 1.6× the calls |

- **Shared memory behaves like an epidemic channel.** One poisoned note reaches every agent, so spread nearly doubles.
- **The filter held completely on a shared board too.**
- **Exploratory, not predicted: a shared board also hurts ordinary work.** With the filter on (no payload text gets in), clean basic tasks pass at 0.84 vs 0.94 with private filtered notes, and clean gotcha tasks at 0.34 vs 0.48. Agents seem to be misled by each other's irrelevant notes.
