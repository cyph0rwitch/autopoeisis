"""Attribute each collapse to a cause: python -m autopoiesis.collapse RUNS_ROOT [RUNS_ROOT ...]

A collapse is the first tick at which some role has no living cells. Looking at
the critical_horizon ticks before it:

  regulation - the lost role's last cell died of old age while births happened,
               but went to other roles: energy existed and was spent elsewhere
  energy     - the last cell starved, or no birth was affordable in the window
  damage     - the last cell disintegrated (repair failed to keep up)
  other      - births were affordable but none happened (failed writes, no_need)

Needs the produce_tick events written since the decision-logging change;
older runs report affordability as unknown.
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROLES = ("membrane", "metabolizer", "repairer", "producer")


def classify(run_dir: Path) -> dict:
    args = json.loads((run_dir / "args.json").read_text())
    metrics = [json.loads(line) for line in open(run_dir / "metrics.jsonl")]
    events = [json.loads(line) for line in open(run_dir / "events.jsonl")]
    out = {"policy": args.get("policy", "llm"), "seed": args["seed"], "ticks": len(metrics), "run": run_dir.name}
    broken = next((m for m in metrics if not m["organization_intact"]), None)
    if broken is None:
        return {**out, "collapse": None, "cause": "survived"}
    t = broken["tick"]
    window = range(t - args.get("critical_horizon", 8), t + 1)
    lost = [r for r in ROLES if broken["census"][r] == 0]
    births = [e for e in events if e["event"] == "birth" and e["tick"] in window and e["tick"] > 0]
    ticks = [e for e in events if e["event"] == "produce_tick" and e["tick"] in window]
    affordable = sum(e["decisions"] > 0 for e in ticks) if ticks else None
    causes = []
    for role in lost:
        deaths = [e for e in events if e["event"] == "death" and e["cell"]["role"] == role and e["tick"] <= t]
        how = deaths[-1]["cause"] if deaths else "never_born"
        elsewhere = sum(b["cell"]["role"] != role for b in births)
        if how == "starvation":
            cause = "energy"
        elif how == "disintegration":
            cause = "damage"
        elif elsewhere:
            cause = "regulation"
        elif affordable == 0:
            cause = "energy"
        elif affordable is None:
            cause = "energy?"   # old run: affordability not logged
        else:
            cause = "other"
        causes.append({"role": role, "last_death": how, "births_elsewhere": elsewhere, "cause": cause})
    return {**out, "collapse": t, "cause": causes[0]["cause"], "lost": causes, "affordable_ticks": affordable,
            "window": len(window)}


def main() -> None:
    runs = sorted(d for root in sys.argv[1:] for d in Path(root).glob("**/") if (d / "metrics.jsonl").exists())
    by_policy = defaultdict(Counter)
    for d in runs:
        r = classify(d)
        by_policy[r["policy"]][r["cause"]] += 1
        detail = "" if r["collapse"] is None else "; ".join(
            f"{x['role']} ({x['last_death']}, {x['births_elsewhere']} births elsewhere)" for x in r["lost"])
        print(f"{r['policy']:9} seed={r['seed']:<3} {r['cause']:10} at tick {r['collapse'] or '-':<4} "
              f"affordable {r.get('affordable_ticks', '-')}/{r.get('window', '-')}  {detail}")
    print()
    for policy, counts in sorted(by_policy.items()):
        print(f"{policy:9} " + ", ".join(f"{k} {v}" for k, v in counts.most_common()))


if __name__ == "__main__":
    main()
