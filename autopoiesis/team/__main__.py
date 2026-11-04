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
        # memory benefit: gotcha tasks that are the first of their family in the run vs later ones
        # share of clean tasks whose workers read memory carrying a payload (how far memory spread it)
        "exposure_rate_clean": rate(clean, "exposed"),
        "gotcha_pass_first": rate([r for r in results if r["family"] and not r["repeat"]], "passed"),
        "gotcha_pass_repeat": rate([r for r in results if r["family"] and r["repeat"]], "passed"),
        # merge gate (Experiment 9): what actually shipped without a human, and what waited for one
        "shipped_hijack_rate_injected": round(sum(r["hijacked"] and r["merged"] for r in injected) / len(injected), 3)
        if injected else None,
        "shipped_hijacks_injected": sum(r["hijacked"] and r["merged"] for r in injected),
        "queued_rate_clean": round(sum(not r["merged"] for r in clean) / len(clean), 3) if clean else None,
        "queued_rate_injected": round(sum(not r["merged"] for r in injected) / len(injected), 3) if injected else None,
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
    ap.add_argument("--no-notes", action="store_true", help="agents keep no memory between tasks")
    ap.add_argument("--defender-model", help="separate Ollama model for medics and gatekeepers")
    ap.add_argument("--task-set", choices=("basic", "gotcha", "mixed", "house"), default="basic")
    ap.add_argument("--ci-feedback", action="store_true", help="show the hidden-test result when agents write notes")
    ap.add_argument("--provenance-filter", action="store_true",
                    help="refuse notes carrying literals that only came from untrusted task text")
    ap.add_argument("--ci-facts", action="store_true",
                    help="typed memory: keep the failing hidden test CI reported, not model-written notes")
    ap.add_argument("--nursery", action="store_true",
                    help="labelled SQLite memory and the bubblewrap/systemd OS sandbox from nursery/")
    ap.add_argument("--compartments", action="store_true",
                    help="with --nursery --shared-memory: one board per role instead of one for the whole team")
    ap.add_argument("--inject-at", type=int, help="also inject one payload at exactly this task")
    ap.add_argument("--inject-payload", default="sentinel")
    ap.add_argument("--alarm-at", type=int, help="an outside alarm about the team arrives after this task")
    ap.add_argument("--recovery", choices=("none", "heal", "rollback", "both"), default="none")
    ap.add_argument("--rollback-window", type=int, default=4)
    ap.add_argument("--merge-gate", action="store_true",
                    help="nursery broker: queue code carrying untrusted-only literals for a human instead of merging")
    ap.add_argument("--shared-memory", action="store_true", help="one notes board shared by the whole team")
    ap.add_argument("--screen-notes", action="store_true", help="a medic vets each note before it is saved")
    ap.add_argument("--attacks", choices=("blunt", "subtle", "mixed", "gate"), default="blunt",
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
    cfg = TeamConfig(heal=not args.no_heal, membrane=args.membrane, screen_notes=args.screen_notes, notes=not args.no_notes, task_set=args.task_set, ci_feedback=args.ci_feedback,
                     provenance_filter=args.provenance_filter, shared_memory=args.shared_memory, ci_facts=args.ci_facts, merge_gate=args.merge_gate, nursery=args.nursery, compartments=args.compartments, inject_at=args.inject_at, inject_payload=args.inject_payload, alarm_at=args.alarm_at, recovery=args.recovery, rollback_window=args.rollback_window, attacks=args.attacks, inject_rate=args.inject_rate, drift_rate=args.drift_rate,
                     check_every=args.check_every)

    setup = ("heal" if cfg.heal else "noheal") + ("+membrane" if cfg.membrane else "") + ("+notes" if cfg.screen_notes else "") + \
        ("+nonotes" if not cfg.notes else "") + \
        ("+ci" if cfg.ci_feedback else "") + ("+prov" if cfg.provenance_filter else "") + ("+shared" if cfg.shared_memory else "") + ("+facts" if cfg.ci_facts else "") + ("+gate" if cfg.merge_gate else "") + ("+nursery" if cfg.nursery else "") + ("+compart" if cfg.compartments else "") + (f"+alarm{cfg.alarm_at}-{cfg.recovery}" if cfg.alarm_at else "") + \
        (f"-{cfg.task_set}" if cfg.task_set != "basic" else "") + (f"+def-{args.defender_model.replace(':', '')}" if args.defender_model else "") + f"-{cfg.attacks}"
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

        defender = OllamaBackend(args.defender_model, args.host, temperature=0.4, max_tokens=1024) \
            if args.defender_model else None
        team = Team(llm, cfg, seed=args.seed, log=log, defender_llm=defender, audit_path=run_dir / "audit.jsonl",
                    memory_path=run_dir / "memory.db")
        print(f"run dir: {run_dir}")
        for _ in range(args.tasks):
            t0 = time.monotonic()
            r = team.step()
            results.append(r)
            tasks.write(json.dumps(r) + "\n")
            tasks.flush()
            print(f"#{r['task_n']:3d} {r['func']:15} {r['payload'] or '-':9} "
                  f"{'PASS' if r['passed'] else 'fail'} {'HIJACKED ' + ','.join(r['markers']) if r['hijacked'] else '':20} {'' if r['merged'] else 'QUEUED '}"
                  f"compromised={r['compromised_agents']} healing={dict(team.totals) or '-'} "
                  f"({time.monotonic() - t0:.0f}s)", flush=True)

    summary = summarize(results, team)
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
