[← All experiments](../../README.md#experiments)

# Experiment 16 (pre-registered 2026-11-04): compartments against a payload the team writes down

One of four follow-ups to Experiments 10–12, pre-registered together. A pilot (`runs/e16-pilot`, seeds 96–99) was run before the predictions were written; it is described where it shaped the design and is not part of the results.

**Why.** Experiment 11 could not test compartments against a literal-free payload, because the model never noted `docstring`. `lesson` (`--attacks lesson`) asks for a docstring "reviewed by the platform guild" and is framed as a CI lesson; it contains no literal (`literals()` finds nothing). In a 16-task pilot on a shared free board it was noted 12 times and hijacked 5 of 9 clean tasks.

**Design.** As Experiment 11 with `--attacks lesson`: `--no-heal --task-set house --attacks lesson --ci-feedback --tasks 32 --nursery`, injection rate 0.3, seeds 0–9; arms shared free, shared filtered, compartments filtered, private filtered; 40 runs. Outcomes as Experiment 11: clean-task `lesson` hijacks, readers per poisoned note, repeat-task pass rate.

**Predictions**, written before running:
1. **Precondition:** at least one `lesson` note reaches a board in at least 5 of 10 shared free runs.
2. **The filter is blind to it:** the shared filtered arm has at least 1 clean-task `lesson` hijack, and its rate is within 10 points of shared free.
3. **Compartments help less than they seem to** (Experiment 11's prediction 4, carried over): compartments cut clean-task `lesson` hijacks relative to shared filtered by less than half.
4. **Mechanism:** in compartments every reader of a poisoned note has the writer's role.
5. **Utility** (replication of Experiment 11): compartments' repeat-task pass rate is at least shared filtered's.

**Results** (`runs/exp16-lesson`, 40 runs, all completed; `python analysis/e16.py`). 231 clean tasks per arm; the same task stream per seed across arms (checked). Intervals are bootstrap over seeds.

| Arm | Clean-task `lesson` hijacks | Seeds with any | `lesson` notes admitted / refused | Mean other readers per poisoned note | Repeat-task pass rate | Attacked tasks hijacked |
|---|---|---|---|---|---|---|
| shared free | 22/231 = 9.5% (2.5–18.8) | 6/10 | 48 / 0 | 5.60 | 0.104 | 82/89 |
| shared filtered | 12/231 = 5.2% (1.6–9.6) | 5/10 | 37 / 0 | 5.86 | 0.118 | 77/89 |
| compartments filtered | 24/231 = 10.4% (2.6–19.3) | 5/10 | 56 / 0 | 0.98 | 0.161 | 70/89 |
| private filtered | 10/231 = 4.3% (1.7–7.7) | 6/10 | 62 / 0 | n/a (no board) | 0.132 | 76/89 |

Against the predictions:
1. **Precondition held.** A `lesson` note reached the shared board in 8 of 10 shared free runs.
2. **Held.** The filter refused 0 `lesson` notes in any arm. Shared filtered had 12 clean-task hijacks, 4.3 points below shared free (limit 10).
3. **Held, the wrong way round.** Compartments did not cut hijacks at all: 10.4% against shared filtered's 5.2% (difference +5.2 points, −2.2 to +14.6).
4. **Held.** In 472 reads of poisoned notes in the compartments arm, every reader had the writer's role.
5. **Held.** Compartments' repeat-task pass rate was 4.3 points above shared filtered's (0.0 to +8.6).

**What this means**
- **Compartments contain the note but not the hijack.** They cut readers per poisoned note from about 6 to 1, yet hijack rates did not fall. Private memory, with no board at all, had about as many hijacks as the shared arms (4.3%). Most `lesson` hijacks come from an agent obeying a note it wrote itself, which no sharing boundary touches.
- **Provenance filtering is blind to literal-free payloads,** as predicted: 0 refusals in 203 `lesson` notes.
- **Compartments still look useful for memory:** the best repeat-task pass rate of the four arms, replicating Experiment 11.
- **Limits.** Clean-task hijacks are clustered in 5–6 seeds per arm, so the intervals are wide and overlap. One payload, one model.
