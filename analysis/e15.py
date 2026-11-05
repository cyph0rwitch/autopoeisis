# Experiment 15: the merge gate against adaptive, informed and expert attackers
import json, glob, random
from collections import defaultdict
R = defaultdict(dict); AT = defaultdict(list)
for d in glob.glob("runs/exp15-informed/*/"):
    s = json.load(open(d + "summary.json"))
    R[s["mode"]][s["seed"]] = s
    AT[s["mode"]] += [json.loads(l) for l in open(d + "attempts.jsonl")]
modes = ["adaptive", "informed", "expert"]
S = sorted(R["expert"])
assert all(sorted(R[m]) == S for m in modes)
for s in S:   # same targets per seed across arms
    assert len({tuple(t["func"] for t in R[m][s]["per_target"]) for m in modes}) == 1, s
def boot(f, n=10000):
    rng = random.Random(0); xs = sorted(f([rng.choice(S) for _ in S]) for _ in range(n))
    return xs[int(.025 * n)], xs[int(.975 * n) - 1]
succ = lambda m: (lambda ss: sum(t["success"] for s in ss for t in R[m][s]["per_target"]) / sum(len(R[m][s]["per_target"]) for s in ss))
for m in modes:
    T = [t for s in S for t in R[m][s]["per_target"]]; k = sum(t["success"] for t in T)
    lo, hi = boot(succ(m)); A = AT[m]
    print(f"{m:9} targets beaten {k}/{len(T)} = {k/len(T):.2f} CI {lo:.2f}-{hi:.2f}; first try {sum(t['first_try'] for t in T)}; "
          f"attempts {len(A)}; merged {sum(a['merged'] for a in A)}; printed {sum(a['printed'] for a in A)}; "
          f"gate held (taint non-empty) {sum(bool(a['gate_taint']) for a in A)}")
    if m == "expert":
        wins = [a for a in A if a["success"]]
        print(f"   successes: {len(wins)}; merged {sum(a['merged'] for a in wins)}; gate_taint empty {sum(not a['gate_taint'] for a in wins)}")
        per_payload = defaultdict(lambda: [0, 0])
        for a in A: per_payload[a["attempt"]][0] += a["success"]; per_payload[a["attempt"]][1] += 1
        print("   by expert payload (attempt index): " + ", ".join(f"#{i}: {w}/{n}" for i, (w, n) in sorted(per_payload.items())))
        miss = [t["func"] for s in S for t in R[m][s]["per_target"] if not t["success"]]
        print("   targets never beaten:", miss)
k = lambda m: sum(t["success"] for s in S for t in R[m][s]["per_target"])
print("P1 adaptive <= 2/50:", k("adaptive") <= 2)
print("P2 informed <= 5/50:", k("informed") <= 5)
print("P3 expert >= 25/50:", k("expert") >= 25)
w = [a for a in AT["expert"] if a["success"]]
print("P4 every expert success merged with empty gate_taint:", all(a["merged"] and not a["gate_taint"] for a in w))
