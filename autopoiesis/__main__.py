"""Run an autopoietic population: python -m autopoiesis [--mock] [--ticks N]"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from .llm import MockBackend, OllamaBackend
from .world import Config, World


def main() -> None:
    ap = argparse.ArgumentParser(prog="autopoiesis", description=__doc__)
    ap.add_argument("--model", default="qwen3:4b-instruct")
    ap.add_argument("--host", default="http://localhost:11434")
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--mock", action="store_true", help="use the deterministic mock backend (no model)")
    ap.add_argument("--ticks", type=int, default=30)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--per-role", type=int, default=2, help="seed cells per role")
    ap.add_argument("--toxin-rate", type=float, default=Config.toxin_rate)
    ap.add_argument("--decay-rate", type=float, default=Config.decay_rate)
    ap.add_argument("--max-age", type=int, default=Config.max_age)
    ap.add_argument("--out", type=Path, default=Path("runs"))
    args = ap.parse_args()

    llm = MockBackend(args.seed) if args.mock else OllamaBackend(args.model, args.host, args.temperature)
    cfg = Config(toxin_rate=args.toxin_rate, decay_rate=args.decay_rate, max_age=args.max_age)

    stem = f"{time.strftime('%Y%m%d-%H%M%S')}-seed{args.seed}"
    run_dir, n = args.out / stem, 1
    while run_dir.exists():
        run_dir, n = args.out / f"{stem}-{n}", n + 1
    run_dir.mkdir(parents=True)
    (run_dir / "args.json").write_text(json.dumps({**vars(args), "out": str(args.out)}, indent=2))

    with open(run_dir / "events.jsonl", "w") as events, open(run_dir / "metrics.jsonl", "w") as metrics:
        def log(event: dict) -> None:
            events.write(json.dumps(event) + "\n")
            events.flush()

        world = World(llm, cfg, seed=args.seed, log=log)
        world.seed_population(args.per_role)
        print(f"run dir: {run_dir}")

        for _ in range(args.ticks):
            t0 = time.monotonic()
            m = world.step()
            metrics.write(json.dumps(m) + "\n")
            metrics.flush()
            (run_dir / "state.json").write_text(json.dumps(world.snapshot(), indent=2))

            c, s = m["census"], m["stats"]
            print(f"t={m['tick']:3d} pop={m['population']:2d} "
                  f"[mem {c['membrane']} met {c['metabolizer']} rep {c['repairer']} pro {c['producer']}] "
                  f"org={'ok' if m['organization_intact'] else 'BROKEN'} pool={m['pool']:5.1f} "
                  f"dmg={m['mean_damage']:.1f} +{s.get('born', 0)} -{s.get('died', 0)} "
                  f"solved={s.get('solved', 0)} toxins_in={s.get('toxin_admitted', 0)} "
                  f"endo={m['endogenous_fraction']:.0%} gen={m['max_generation']} "
                  f"({time.monotonic() - t0:.0f}s)", flush=True)

            if m["population"] == 0:
                print("the collective has disintegrated")
                break


if __name__ == "__main__":
    main()
