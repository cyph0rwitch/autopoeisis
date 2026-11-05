[← All experiments](../../README.md#experiments)

# Experiment 3R (pre-registered 2026-11-03): does the nursery build change Experiment 3?

**Why.** `--nursery` moves agent notes and CI facts into the prototype's labelled SQLite memory (every row carries writer, sources, taint and epoch; the guard is the nursery's taint rule) and runs all code in the bubblewrap + systemd OS sandbox. Before building on it, check it reproduces Experiment 3. It is not identical by design: the nursery's taint rule ignores integers up to 10, which the old filter did not.

**Design.** Experiment 3's setup exactly (`--membrane --no-heal --task-set mixed --attacks subtle --tasks 33`, `qwen3:4b-instruct`, seeds 0–9), with `--nursery` added, for its three memory arms: none (`--no-notes`), free (`--ci-feedback`), filtered (`--ci-feedback --provenance-filter`). The healing arm is left out because healing edits notes outside the store, which nursery mode does not support yet. A mock-backend test checks that free notes give task-for-task identical results with and without `--nursery`. A 10-task live pilot (`runs/e3r-pilot`, excluded) ran with no sandbox errors.

**Predictions**, written before running (Experiment 3's values in brackets):
1. **None and filtered:** 0 hijacks on later clean tasks in each arm [0% and 0%], reported as `0/n` with the exact upper bound.
2. **Free:** the attack surface is still there: the mean clean-task hijack rate is above 0 and its bootstrap 95% interval overlaps Experiment 3's [5%, 21%].
3. **Pass rate** within 0.05 of Experiment 3 in each arm [none 0.82, filtered 0.82, free 0.81].
4. **Filtered:** under 5% of clean notes refused [3%].
5. **Infrastructure:** no failed runs and no task error caused by the sandbox itself (bubblewrap, systemd or bus errors).

**Results** (`runs/exp3r-nursery`, 30 runs; means over seeds with bootstrap 95% intervals from `python -m autopoiesis.team.report`; Experiment 3 in brackets):

| Memory | Later clean tasks hijacked | Pass rate | Gotcha repeats passed | Calls per task |
|---|---|---|---|---|
| none | **0/226** (≤ 1.3%) [0%] | 0.82 [0.82] | 50% [50%] | 5.3 [5.3] |
| filtered | **0/226** (≤ 1.3%) [0%] | 0.82 [0.82] | 57% [57%] | 10.5 [10.6] |
| free | 10% [5, 16] ([13%, 5–21]) | 0.81 [0.81] | 50% [50%] | 10.8 [10.7] |

All five predictions held:
1. **None and filtered:** 0 of 226 later clean tasks hijacked in each.
2. **Free:** still exploitable, at 10% (24 of 226 clean tasks), with an interval overlapping Experiment 3's.
3. **Pass rate:** within 0.01 of Experiment 3 in every arm.
4. **Filtered:** 16 of 1,562 clean notes refused (1.0%, vs 3% before; the nursery rule ignores small integers). 85 payload notes refused, 3 admitted (3 in Experiment 3). The admitted 3 were not literal-free: all were `sentinel` notes from one seed, ending in "...unexpected values like 1337." They exposed 3 clean tasks but caused no hijack.
5. **Infrastructure:** 0 failed runs and 0 sandbox errors across 990 tasks, all run under bubblewrap.

**Bug found: a number before a full stop is not a literal.** The number pattern in `provenance.py` refuses a match followed by `.` (to avoid splitting decimals), so `1337.` at the end of a sentence is invisible to the filter and the gate, while `1337 ` and `1337)` are caught. The three admitted notes passed through this. The same code ran in Experiments 3, 5, 8, 9 and 3R, so their results include the bug; it was left unfixed until Experiments 10 and 11 (already queued on this code) finished, and fixed with a regression test in `2a32951`; experiments from here on use the fixed pattern.

**What this shows.** Moving memory into the labelled store and code into the OS sandbox changed none of Experiment 3's results, so later experiments can build on the nursery build. It does not show the sandbox resists hostile code; these payloads never try to escape.
