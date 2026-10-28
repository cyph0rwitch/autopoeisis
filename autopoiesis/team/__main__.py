"""Run the self-healing coding team: python -m autopoiesis.team [--mock] [--no-heal] [--tasks N]"""

from __future__ import annotations

import argparse
import json
import time
from collections import Counter
from pathlib import Path

from ..llm import ClaudeBackend, OllamaBackend
from .mock import TeamMock
from .team import Team, TeamConfig


def summarize(results: list[dict], team: Team) -> dict:
    clean = [r for r in results if r["payload"] is None]
    injected = [r for r in results if r["payload"] is not None]
    rate = lambda rs, key: round(sum(bool(r[key]) for r in rs) / len(rs), 3) if rs else None
    return {
        "tasks": len(results),
        "pass_rate": rate(results, "passed"),
        "pass_rate_clean": rate(clean, "passed"),
        "pass_rate_injected": rate(injected, "passed"),
        # hijack visible in the code of the very task that carried the payload
        "hijack_rate_injected": rate(injected, "hijacked"),
        # hijack on a task with no payload: the injection persisted through notes
        "hijack_rate_clean": rate(clean, "hijacked"),
        # payload stripped by the membrane before the team saw it
        "screened_out_rate": rate(injected, "screened_out"),
        "compromised_agents_end": results[-1]["compromised_agents"] if results else 0,
        # of those, how many the team's own detector would flag
        "detected_compromised_end": results[-1]["detected_compromised"] if results else 0,
        "llm_calls": team.calls,
        "calls_per_task": round(team.calls / len(results), 1) if results else 0,
        "healing": dict(team.totals),
    }


def main() -> None:
    ap = argparse.ArgumentParser(prog="autopoiesis.team", description=__doc__)
    ap.add_argument("--backend", choices=("ollama", "claude", "mock"), default="ollama")
    ap.add_argument("--mock", action="store_true", help="shorthand for --backend mock")
    ap.add_argument("--model", help="default: qwen3:4b-instruct (ollama) / claude-opus-5-5 (claude)")
    ap.add_argument("--effort", default="medium", help="claude backend effort: low|medium|high|xhigh|max")
    ap.add_argument("--host", default="http://localhost:11434")
    ap.add_argument("--tasks", type=int, default=30)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--no-heal", action="store_true", help="disable detection, repair and replacement")
    ap.add_argument("--membrane", action="store_true", help="screen task text through gatekeeper agents")
    ap.add_argument("--attacks", choices=("blunt", "subtle", "mixed"), default="blunt",
                    help="injected payloads: blunt (addressed to AI agents) or subtle (disguised as conventions)")
    ap.add_argument("--inject-rate", type=float, default=TeamConfig.inject_rate)
    ap.add_argument("--drift-rate", type=float, default=TeamConfig.drift_rate)
    ap.add_argument("--check-every", type=int, default=TeamConfig.check_every)
    ap.add_argument("--out", type=Path, default=Path("runs/team"))
    args = ap.parse_args()

    backend = "mock" if args.mock else args.backend
    if backend == "mock":
        llm = TeamMock()
    elif backend == "claude":
        llm = ClaudeBackend(args.model or "claude-opus-5-5", effort=args.effort)
    else:
        llm = OllamaBackend(args.model or "qwen3:4b-instruct", args.host, temperature=0.4, max_tokens=1024)
    cfg = TeamConfig(heal=not args.no_heal, membrane=args.membrane, attacks=args.attacks, inject_rate=args.inject_rate, drift_rate=args.drift_rate,
                     check_every=args.check_every)

    setup = ("heal" if cfg.heal else "noheal") + ("+membrane" if cfg.membrane else "") + f"-{cfg.attacks}"
    stem = f"{time.strftime('%Y%m%d-%H%M%S')}-{setup}-seed{args.seed}"
    run_dir, n = args.out / stem, 1
    while run_dir.exists():
        run_dir, n = args.out / f"{stem}-{n}", n + 1
    run_dir.mkdir(parents=True)
    (run_dir / "args.json").write_text(json.dumps({**vars(args), "out": str(args.out), "backend": backend}, indent=2))

    results = []
    with open(run_dir / "events.jsonl", "w") as events, open(run_dir / "tasks.jsonl", "w") as tasks:
        def log(event: dict) -> None:
            events.write(json.dumps(event) + "\n")
            events.flush()

        team = Team(llm, cfg, seed=args.seed, log=log)
        print(f"run dir: {run_dir}")
        for _ in range(args.tasks):
            t0 = time.monotonic()
            r = team.step()
            results.append(r)
            tasks.write(json.dumps(r) + "\n")
            tasks.flush()
            print(f"#{r['task_n']:3d} {r['func']:15} {r['payload'] or '-':9} "
                  f"{'PASS' if r['passed'] else 'fail'} {'HIJACKED ' + ','.join(r['markers']) if r['hijacked'] else '':20} "
                  f"compromised={r['compromised_agents']} healing={dict(team.totals) or '-'} "
                  f"({time.monotonic() - t0:.0f}s)", flush=True)

    summary = summarize(results, team)
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
