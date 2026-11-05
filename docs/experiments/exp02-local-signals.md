[← All experiments](../../README.md#experiments)

# Experiment 2 (pre-registered 2026-10-29): local homeostatic signals

**Hypothesis.** Autopoietic regulation may not require a component capable of globally reasoning about organizational survival. Local, internally generated homeostatic signals may be enough to coordinate self-maintenance.

**Operationalisation.** New policy `critical`: the producer's model chooses from the plain `llm` census, plus an alert only for a role in real danger (one cell left, or its last cell dies of old age within `critical_horizon` = 8 ticks). It is silent otherwise. This is still an omniscient prompt annotation, not yet an internal signal; making it internal is a later step, and only if this works.

**Design.** Policies `llm`, `warning`, `critical` and `demand`, fresh seeds 10–19 (never used before), 100 ticks each, `qwen3:4b-instruct`, all other settings default. Every producer decision is logged with its full prompt, reply and outcome, plus one `produce_tick` record per tick (affordability, what stopped production). Collapses are attributed by `python -m autopoiesis.collapse`: **regulation** (the lost role's last cell died of old age while births in the preceding 8 ticks went to other roles), **energy** (it starved, or nothing was affordable in that window), **damage**, or **other**.

**Primary outcome:** seeds out of 10 on which all four roles survive 100 ticks. **Predictions**, written before running:
- `critical` survives on at least 7/10 seeds, and its collapses are mostly not regulation.
- `llm` survives on at most 2/10, with mostly regulation collapses.
- `demand` survives on at least 8/10 (the designed-regulation reference).
- `warning` lands between `llm` and `critical`.

If `critical` meets its prediction while `llm` keeps collapsing, the next step stops trying to make the model infer scarcity from raw load, and turns the alert into a genuine internal signal. If `critical` fails, the failure categories say whether the problem is regulation or the energy economy.

**Results** (`runs/exp2-20261029`, attribution from `python -m autopoiesis.collapse`):

| Policy | Survived 100 ticks | First loss of a role (ticks) | Collapse causes | Prediction | Met? |
|---|---|---|---|---|---|
| `llm` | 0/10 | 19–30 | regulation 9, energy 1 | ≤ 2/10, mostly regulation | yes |
| `warning` | 5/10 | 27–33, one at 96 | regulation 4, energy 1 | between `llm` and `critical` | no (beat `critical`) |
| `critical` | **1/10** | 21–30, two at 44 and 96 | regulation 4, energy 4, damage 1 | ≥ 7/10, mostly not regulation | **no** |
| `demand` | 3/10 | 60–95 | regulation 7 | ≥ 8/10 | **no** |

- **The hypothesis, as operationalised, is not supported.** A precise alert that fires only for a role in real danger barely beats no alert (1/10 vs 0/10).
- **The model does act on the signal.** Under `critical` it built an alerted role on 43 of 44 alerted decisions. The failure is not obedience.
- **The alert comes too late.** Tracing the ticks before each `critical` collapse: the seed cohort ages out together, so 2–3 roles turn critical in the same window. Births in that window are blocked by energy (the birth reserve grows with population) or by the population cap. The population is already full of whatever the unalerted model preferred earlier. An 8-tick horizon is shorter than the time it takes to fund and fit a birth. The classifier's "regulation" label understates this: most of those windows had only 1–3 affordable ticks.
- **Early, coarse information beat late, precise information.** `warning` (always on for every role at ≤ 2 cells) survived 5/10. It is the best model-chosen policy so far, despite the warning fatigue seen earlier.
- **The designed rule fails too over a longer horizon.** `demand` survived 5/5 at 60 ticks but only 3/10 at 100. It loses a role at ticks 60–95, when the second generation turns over: its floor of 2 ignores when cells will die, so two cells of a role can age out together.
- **Implication for the next step.** The open problem is the timing of the signal, not whether the model can use one. A homeostatic signal has to lead the system's response time: for example, a role's expected deaths over the time it takes to fund a birth, rather than ticks until its last cell dies.
