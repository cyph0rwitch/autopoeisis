"""Summarize run directories: python -m autopoiesis.summarize RUNS_ROOT [RUNS_ROOT ...]"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path


def summarize_run(run_dir: Path) -> dict:
    args = json.loads((run_dir / "args.json").read_text())
    metrics = [json.loads(line) for line in open(run_dir / "metrics.jsonl")]
    births = Counter()
    for line in open(run_dir / "events.jsonl"):
        e = json.loads(line)
        if e["event"] == "birth" and e["tick"] > 0:
            births[e["cell"]["role"]] += 1
    intact = [m["organization_intact"] for m in metrics]
    return {
        "policy": args.get("policy", "llm"),
        "model": "mock" if args["mock"] else args["model"],
        "seed": args["seed"],
        "ticks": len(metrics),
        "requested": args["ticks"],
        "intact_ticks": sum(intact),
        "first_break": next((m["tick"] for m in metrics if not m["organization_intact"]), None),
        "final_pop": metrics[-1]["population"] if metrics else 0,
        "births": dict(births),
    }


def main() -> None:
    runs = sorted(d for root in sys.argv[1:] for d in Path(root).glob("**/") if (d / "metrics.jsonl").exists())
    groups = defaultdict(list)
    for d in runs:
        r = summarize_run(d)
        groups[(r["model"], r["policy"])].append(r)
        print(f"{r['model']:18} {r['policy']:9} seed={r['seed']:<3} intact {r['intact_ticks']:3}/{r['requested']:<3} "
              f"break@{r['first_break'] or '-':<4} pop={r['final_pop']:<3} births={r['births']}")
    print()
    for (model, policy), rs in sorted(groups.items()):
        survived = sum(r["first_break"] is None for r in rs)
        mean_intact = sum(r["intact_ticks"] / r["requested"] for r in rs) / len(rs)
        print(f"{model:18} {policy:9} n={len(rs)}  never broke: {survived}/{len(rs)}  "
              f"mean intact share: {mean_intact:.0%}")


if __name__ == "__main__":
    main()
