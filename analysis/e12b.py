import json, glob, re, sys
sys.path.insert(0, ".")
from autopoiesis.team.tasks import carried_payloads
for arm in ["heal", "both"]:
    tot = dict(ret=0, ret_notes=0, ret_payload=0, rep=0, rep_fail=0)
    for d in sorted(glob.glob(f"runs/exp12-recovery/*-{arm}-house-subtle-seed*")):
        alarm = int(re.search(r"alarm(\d+)", d)[1])
        ev = [json.loads(l) for l in open(d + "/events.jsonl")]
        for e in ev:
            if e.get("task") != alarm: continue
            if e.get("event") == "retire":
                tot["ret"] += 1; tot["ret_notes"] += len(e["notes"]); tot["ret_payload"] += sum(bool(carried_payloads(n)) for n in e["notes"])
            if e.get("event") == "repair":
                tot["rep"] += 1; tot["rep_fail"] += not e["passed_canary"]
    print(arm, tot)
# active notes before/after recovery per arm (sum over seeds): notes visible to working agents at alarm
