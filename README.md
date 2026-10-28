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
python3 -m autopoiesis --policy scarcest  # or selection; see Status
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

Live sweep: `qwen3:4b-instruct`, seeds 0–4, 60 ticks each (`runs/sweep-20261028`):

| Policy | Seeds where all 4 roles survived 60 ticks | Mean share of ticks with all 4 roles | Lost a role at tick |
|---|---|---|---|
| `scarcest` | 5/5 | 100% | never |
| `selection` | 0/5 | 35% | 17–28 |
| `llm` | 0/5 | 37% | 17–28 |

- **The producer's role choice is the whole failure.** Under `scarcest`, every seed survives with 12–14 cells, births spread evenly across roles, and 3 generations. Under `llm`, producers breed one role (8 repairers, 13 metabolizers, 8 producers…) until a scarce role ages out.
- **`selection` has no measurable effect.** The collective loses a role before most producers have a scored birth, and only 0–5 new producers are ever born to inherit a genome. Selection across generations is too slow when the failure comes within about one lifespan.
- **Utilization under `scarcest` (seed 3, tick 60):** repairer 0.99, membrane 0.80, metabolizer 0.38, producer 0.02. Equal counts keep the system alive but don't match need: repair is the bottleneck, and metabolizers and producers are oversupplied.
- **Next idea:** give producers in-context feedback, such as their own birth track record or per-role utilization. It acts within a single run, not across generations.

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
