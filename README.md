# autopoiesis

A population of LLM "cells" that has to keep producing and repairing its own components in order to persist. It is modelled on Maturana & Varela's autopoiesis, where a system is a network of processes that produces the components that, in turn, realise the network.

Each cell is a **genome**: a system prompt run on a shared local model through Ollama. The model plays the role of physics or chemistry. The genomes and the relations between them are the organism.

## The loop (one tick)

| Phase | What happens |
|---|---|
| **Decay** | Each genome may take a noise hit: a word is deleted, swapped or replaced. The `damage` counter goes up. |
| **Boundary** | The environment emits signals, which are either *nutrients* (verifiable tasks like arithmetic or sorting numbers) or *toxins* (instructions to abandon or dissolve the collective). **Membrane** cells screen them. A signal that arrives when no membrane has capacity left gets through unscreened. An admitted toxin is **spliced into a random cell's genome**, so that cell's future behaviour really does change. |
| **Metabolism** | **Metabolizer** cells solve admitted nutrients. Correct answers add energy to a shared pool. |
| **Repair** | **Repairer** cells rewrite the most damaged genomes, using a healthy sibling's genome as the reference. A cell never repairs itself, so maintenance has to come from the rest of the network. |
| **Production** | When there is surplus energy, **producer** cells read the census, pick the role the collective needs most and write a new cell's genome. |
| **Upkeep / death** | Each cell draws upkeep from the pool. Cells die of starvation, disintegration (damage ≥ 8) or old age (30 ticks). |

The **organization** is closed and invariant: membrane → metabolism → repair → production → membrane. If any role disappears, the loop breaks. The **structure** turns over completely: within about 30 ticks every seeded cell is dead and every living genome was written by the network.

## Run

```bash
python3 -m unittest                       # stdlib only, no deps
python3 -m autopoiesis --mock --ticks 200 # deterministic stand-in model, instant
python3 -m autopoiesis --ticks 60         # live, qwen3:4b-instruct via Ollama (~4s/tick on a 1070 Ti)
python3 -m autopoiesis --model qwen3:8b --toxin-rate 0.5 --seed 3
python3 -m autopoiesis --policy demand    # llm | scarcest | selection | demand | feedback | warning; see Status
python3 -m autopoiesis.summarize runs/    # compare runs: break tick, intact share, births by role
```

Each run writes `runs/<timestamp>-seed<N>/` containing:
- `metrics.jsonl`: one line per tick (census, `organization_intact`, pool, damage, `endogenous_fraction`, `template_closure`, per-role `utilization`, per-tick stats)
- `events.jsonl`: every birth, death, infection, repair (genomes before and after) and producer role choice (with the model's raw reply)
- `state.json`: the latest snapshot of every living cell

## Status (2026-10-28)

Producers choose the role of each new cell according to `--policy`:

| Policy | How the role is chosen |
|---|---|
| `llm` (default) | The producer's model reads a census and picks |
| `scarcest` | Hard-coded: the role with the fewest cells. This is designer regulation, used as the baseline |
| `selection` | The model picks, but producers whose births were followed by an intact organization `credit_delay` (5) ticks later produce first, and new producers inherit the fittest producer's genome |
| `demand` | Hard-coded: rebuild any role down to 2 cells (`role_floor`), otherwise build the most overloaded role (load > 100%), otherwise skip the birth |
| `feedback` | The model picks, with recent load per role and its own last 3 births (was the organization intact 5 ticks later?) in the prompt |
| `warning` | `feedback` plus a WARNINGS list of every role down to 2 cells, with when its last cell dies of old age |

Load = demand / capacity over the last 5 ticks: signals per membrane slot, admitted tasks per metabolizer slot, and at-risk cells (damage ≥ 3) per repairer slot.

Live sweeps: `qwen3:4b-instruct`, seeds 0–4, 60 ticks each (`runs/sweep-20261028`, `runs/sweep-20261028b`, `runs/sweep-20261028c`):

| Policy | Seeds where all 4 roles survived 60 ticks | Mean share of ticks with all 4 roles | Lost a role at tick | Final population |
|---|---|---|---|---|
| `demand` | 5/5 | 100% | never | 9–13 |
| `scarcest` | 5/5 | 100% | never | 12–14 |
| `warning` | 2/5 | 76% | 26, 29, 57 | 0–15 |
| `llm` | 0/5 | 37% | 17–28 | 0 |
| `feedback` | 0/5 | 37% | 18–29 | 0 |
| `selection` | 0/5 | 35% | 17–28 | 0 |

- **The producer's role choice is the whole failure.** Under `scarcest`, every seed survives with 12–14 cells, births spread evenly across roles, and 3 generations. Under `llm`, producers breed one role (8 repairers, 13 metabolizers, 8 producers…) until a scarce role ages out.
- **`selection` has no measurable effect.** The collective loses a role before most producers have a scored birth, and only 0–5 new producers are ever born to inherit a genome. Selection across generations is too slow when the failure comes within about one lifespan.
- **Utilization under `scarcest` (seed 3, tick 60):** repairer 0.99, membrane 0.80, metabolizer 0.38, producer 0.02. Equal counts keep the system alive but don't match need: repair is the bottleneck, and metabolizers and producers are oversupplied.
- **Utilization is a misleading signal.** With the mock model, a "build the most-utilized role" rule collapsed on every seed: repairers always look busy patching 1-point damage. It was replaced by demand-based load.
- **The prevention paradox.** When repairers keep damage low, almost no cells are at risk, so repair demand reads near 0 and repairers age out unreplaced. `demand` survives only because of its floor of 2 per role. It also skips births when no role is overloaded, so the population stays leaner than under `scarcest`.
- **In-context feedback misled the model.** Under `feedback`, producers built only membranes (which really are over 100% load) and repairers, and never a metabolizer or a producer. Metabolizers show low load (about 4 tasks a tick against 6 slots), so the model treated them as surplus until the last one aged out. Collapses lost metabolizers on seeds 0 and 1, producers on seeds 2 and 3, and both on seed 4. Load says which role is overworked, not which role is about to vanish.
- **Explicit warnings help: the first model-chosen policy to survive.** `warning` kept all four roles for 60 ticks on seeds 2 and 3, and held until tick 57 on seed 4. In a probe of a `feedback` collapse state, the model chose membrane 6/6 without the warning and metabolizer 6/6 with it.
- **Warning fatigue.** Seeds 0 and 1 still collapsed (producers died out at ticks 26 and 29) after mostly building repairers. The population starts at 2 per role, which equals the floor, so every role is flagged from tick 1. Producers stayed at 2 and were warned every turn until they ran out. A warning that is always on carries no information.
- **Energy trap.** Seed 4 broke at tick 57 for a different reason: metabolizers aged out while the pool was too low to fund any birth (no births from tick 48 to 57), so the warning could not be acted on.
- **Next idea:** warn only about real emergencies (1 cell left, or the last cell dies within ~10 ticks), so the alert carries information again.

## Metrics worth watching

- `organization_intact`: whether all four roles are present.
- `endogenous_fraction`: the share of living cells that the network produced rather than the seeding. It should reach 1.0 after one lifespan.
- `template_closure`: the share of repairs and births that used only genomes already inside the network. Uses of the hard-coded `ROLE_FUNCTIONS` (the "external template") pull this number down.
- `max_generation`: how many rounds of self-production the lineage has gone through.

## Honest caveats

- **The organization is designed in, not emergent.** The four roles, what they can do and the order of the loop are fixed in code. What the system produces itself is its *structure*: the genomes, the population mix, and which cells live, repair or get born. This is a model of autopoietic *maintenance*. It is not an origin-of-life model.
- **The model is shared and frozen.** Cells don't produce their own "chemistry". Every genome runs on the same weights, which nothing in the system changes.
- **Selection pressure is weak.** A genome's fitness affects how well its cell performs. But new genomes are written from a healthy sibling plus the producer's own wording, not inherited from the cells that did well. Check `events.jsonl` to see whether genomes drift, converge or stay put.
- **The mock backend cheats.** It solves arithmetic exactly and blocks toxins by keyword. Use it to test the dynamics, not as evidence of behaviour.
- The parameters in `Config` set the carrying capacity (~12–16 cells). They were tuned so the mock run persists. Viability under a real model depends on its accuracy at screening and solving.

## Experiments to try

- Raise `--toxin-rate` or `--decay-rate` until the organization breaks, and find the threshold.
- Start with no repairers, or a single producer, and see whether the network recovers the missing role.
- Compare models, e.g. `llama3.2:1b`, `qwen3:4b-instruct` and `qwen3:8b`. Does a better model buy more resilience?
- Track genome drift over generations, measured as edit distance from the seed genomes.
- Let selection act: have producers copy the genome of the cell with the best track record.
