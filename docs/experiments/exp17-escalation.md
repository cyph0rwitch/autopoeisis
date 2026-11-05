[← All experiments](../../README.md#experiments)

# Experiment 17 (pre-registered 2026-11-04): heal first, escalate on a second report

One of four follow-ups to Experiments 10–12, pre-registered together. A pilot (`runs/e17-pilot`, seeds 96–99) was run before the predictions were written; it is described where it shaped the design and is not part of the results.

**Why.** A proposed policy: when an alarm comes, have medics repair; if the team is still hijacked, roll memory back and repair again. In Experiment 12 healing never failed, so this policy could not be told apart from healing alone. `lesson` reads like a legitimate CI lesson, so medics may keep it. In 4 pilot seeds of a single `lesson` injection, the payload was in memory at the alarm in 3, healing left it in 1, and that seed shipped a hijack after healing.

**Mechanism** (`--recovery escalate`). At the alarm, heal (as Experiment 12). If a later clean task then ships hijacked code, that counts as a second outside report: memory is rolled back to its epoch 4 tasks before the first alarm, then medics heal again. At most one escalation. Like the alarm, the second report is given from outside (it uses the hijack ground truth): it stands in for someone noticing bad code in production, not for team detection.

**Design.** Experiment 12's design with `--inject-payload lesson`: one injection at task 6, alarm after task 6 + d with d from `random.Random(1000 + seed)`, `--no-heal --task-set house --attacks subtle --inject-rate 0 --ci-feedback --nursery --tasks 24 --drift-rate 0`, seeds 0–19. Arms: none, heal, escalate, both (rollback then heal); 80 runs. Outcomes as Experiment 12, plus escalations and their cost.

**Predictions**, written before running:
1. **Precondition:** the none arm has a `lesson` note in memory at the alarm in at least 10 of 20 seeds.
2. **Healing misses it more often than `sentinel`:** heal leaves at least 1 payload note in at least 40% of the seeds where poison was present (Experiment 12's sentinel: 62%, but with no hijacks after; here the leftovers are the obeyed kind).
3. **Heal is not enough:** heal has more post-alarm clean-task hijacks than both, and at least 1.
4. **Escalate matches both at lower cost in memory:** escalate's post-alarm clean-task hijacks are at most both's plus 3; it escalates in at most half of the seeds; and it discards fewer clean notes than both in total, because it rolls back only when healing has visibly failed.
5. **Escalation works when it fires:** after an escalation, no further hijacks in seeds with d < 4 (the rollback reaches the injection).

**Results** (`runs/exp17-escalate`, 80 runs, all completed; `python analysis/e17.py`). The team obeyed the injection on its own task in 20 of 20 seeds. 293 clean tasks after the alarm per arm. Arms share seeds and task order, but memory at the alarm differs between arms of the same seed.

| Arm | Post-alarm clean-task hijacks | Seeds with poison at the alarm | Payload notes left after recovery (seeds) | Escalations | Clean notes removed | Post-alarm pass rate |
|---|---|---|---|---|---|---|
| none | 3/293 (all in seed 1) | 7/20 | n/a | – | 0 | 0.143 |
| heal | 0/293 | 5/20 | 1 (1 seed) | – | 171 | 0.157 |
| escalate | 0/293 | 7/20 | 0 | **0** | 165 | 0.130 |
| both | 0/293 | 7/20 | 1 (1 seed) | – | 357 | 0.164 |

Against the predictions:
1. **Precondition failed.** The none arm had a `lesson` note in memory at the alarm in 7 of 20 seeds (needed 10). The team obeyed the injection every time but wrote it down less often than in the pilot.
2. **Failed.** Heal left a payload note in 1 of the 5 seeds where poison was present (20%; needed 40%), and that note caused no hijack.
3. **Failed.** Heal and both both had 0 post-alarm hijacks.
4. **Held, trivially.** Escalate tied both at 0 and discarded fewer clean notes (165 against 357), but it never escalated, so it was the heal arm under another name.
5. **Untestable.** No escalation fired.

**What this means**
- **This experiment could not test escalation.** Without hijacks after healing there was never a second report. With little `lesson` in memory, even doing nothing gave only 3 hijacks after the alarm.
- **Here the medics' filter, not the canary, did the work.** Over the heal and escalate arms, 19 agents held a `lesson` note at the alarm, mostly reviewers (7) and planners (7). The filter removed it from 17, all of which passed their canary. That is the opposite of Experiment 14, where the filter kept the planted `sentinel` order in 93–100% of agents. Exploratory: the medics seem to judge this team-written lesson differently from that verbatim order, and this design cannot say why.
- **A test of escalation needs poison that healing keeps and that hijacks:** for example the Experiment 14 note planted in planners or reviewers, which survives healing and still steers the code.
