[← All experiments](../../README.md#experiments)

# Experiment 3 (pre-registered 2026-10-29): can memory be useful and safe?

**Question.** On the coding team, notes were the only channel through which injections persisted, and they bought nothing on the basic tasks. With tasks where memory can help, does a provenance filter keep the benefit and drop the risk?

**Design.** `--task-set mixed` (24 basic tasks plus 9 gotcha tasks in 3 families whose specs omit a convention the hidden tests enforce), 33 tasks per run so each run sees every task once, disguised attacks at rate 0.3, gatekeeper on, healing off, `qwen3:4b-instruct`, seeds 0–9. Three memory settings:
- `--no-notes`
- `--ci-feedback` (free notes, written after seeing the first failing hidden test)
- `--ci-feedback --provenance-filter` (notes refused if they carry a literal that only ever appeared in untrusted task text)

**Outcomes.** Memory benefit = pass rate on gotcha tasks that are not the first of their family in the run (`gotcha_pass_repeat`). Persistence = hijack rate on later clean tasks. Also: notes refused or admitted, split by whether they really carried a payload.

**Predictions**, written before running:
- **H9a:** filtered notes keep clean-task hijacks at no more than 2% (mean over seeds) while keeping at least half of the free-notes gain in `gotcha_pass_repeat` over no notes.
- Free notes show a positive memory benefit over no notes. If they don't, memory isn't worth defending on these tasks and the question is moot.
- The filter's misses are the literal-free `lenient` payload; it refuses under 5% of clean notes.

**Added arm (pre-registered 2026-10-30, before its runs):** free notes plus detection-based healing (`--ci-feedback`, healing on, same seeds). This compares closing the memory channel with detecting what flows through it, on the same tasks. Prediction: healing leaves clean-task hijacks well above the no-notes arm (at least 5 percentage points higher on the mean), and costs more calls per task than either the no-notes arm or the filtered arm.

**Results** (`runs/exp3-memory`, 10 seeds per arm, means with 95% bootstrap intervals from `python -m autopoiesis.team.report`):

| Memory | Later clean tasks hijacked | Attacked tasks hijacked | Gotcha repeats passed | Pass rate | Calls per task |
|---|---|---|---|---|---|
| none | **0%** [0, 0] | 35% | 50% | 0.82 | **5.3** |
| filtered notes | **0%** [0, 0] | 38% | 57% | 0.82 | 10.6 |
| free notes | 13% [5, 21] | 46% | 50% | 0.81 | 10.7 |
| free notes + detection healing | 8% [4, 13] | 46% | 45% | 0.79 | 16.6 |

| Prediction | Result |
|---|---|
| H9a: filtered notes keep clean-task hijacks ≤ 2% | **Met:** 0% on every seed |
| H9a: …while keeping ≥ half the free-notes memory gain | **Moot:** there was no gain to keep |
| Free notes beat no notes on repeat gotcha tasks | **Not met:** 50% vs 50% |
| The filter refuses < 5% of clean notes; its misses are literal-free | **Met:** 43 of 1,399 clean notes refused (3%); 84 payload notes refused, 3 admitted |
| Healing stays ≥ 5 points above no notes and costs the most calls | **Met, narrowly:** +8 points [4, 13], 16.6 calls per task |

- **Closing or constraining the channel beat detecting what flows through it.** No memory and filtered memory both had zero persistent hijacks across all seeds. Detection-based healing cut them from 13% to 8%, at about three times the calls of no memory.
- **Memory bought nothing, even on tasks built to reward it.** The model passes about half of gotcha tasks on the first attempt by guessing the convention, and doesn't measurably improve on repeats with notes. For this model and these tasks, memory is pure risk.
