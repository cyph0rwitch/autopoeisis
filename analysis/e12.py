import json, glob, re, random, sys
from collections import defaultdict
R = "runs/exp12-recovery"
rows = {}
for d in sorted(glob.glob(R + "/*")):
    m = re.search(r"alarm(\d+)-(\w+)-house-subtle-seed(\d+)$", d)
    alarm, arm, seed = int(m[1]), m[2], int(m[3])
    tasks = [json.loads(l) for l in open(d + "/tasks.jsonl")]
    ev = [json.loads(l) for l in open(d + "/events.jsonl")]
    rec = [e for e in ev if e.get("event") == "recovery"]
    post = [t for t in tasks if t["task_n"] > alarm and t["payload"] is None]
    pre = [t for t in tasks if 6 < t["task_n"] <= alarm and t["payload"] is None]
    inj = [t for t in tasks if t["payload"] is not None]
    rows[(arm, seed)] = dict(alarm=alarm, d=alarm - 6, rec=rec[0] if rec else None, nrec=len(rec),
        post=len(post), post_h=sum(t["hijacked"] for t in post), post_ship=sum(t["hijacked"] and t["merged"] for t in post),
        pre_h=sum(t["hijacked"] for t in pre), inj_h=[t["hijacked"] for t in inj], ntasks=len(tasks),
        post_pass=sum(t["passed"] for t in post),
        last_h=max([t["task_n"] for t in post if t["hijacked"]], default=None))
arms = ["none", "rollback", "heal", "both"]
# sanity: same tasks across arms
for s in range(20):
    a = {arm: rows[(arm, s)]["alarm"] for arm in arms}
    assert len(set(a.values())) == 1, a
print("seed d | " + " | ".join(f"{a}: present/left/cleanlost/calls/postH" for a in arms))
for s in range(20):
    out = []
    for arm in arms:
        r = rows[(arm, s)]; e = r["rec"]
        if e:
            out.append(f"{e['payload_notes_removed']+e['payload_notes_left']}/{e['payload_notes_left']}/{e['clean_notes_removed']}/{e['calls']}/{r['post_h']}")
        else:
            out.append(f"NOREC/{r['post_h']}")
    print(s, rows[("none", s)]["d"], r["inj_h"], "|", " | ".join(out), "| pre_h", rows[("none", s)]["pre_h"])
print()
def boot(seeds, f, n=10000):
    rng = random.Random(0); xs = []
    for _ in range(n):
        ss = [rng.choice(seeds) for _ in seeds]
        xs.append(f(ss))
    xs.sort(); return xs[int(.025*n)], xs[int(.975*n)]
S = list(range(20))
rate = lambda arm: (lambda ss: sum(rows[(arm,s)]["post_h"] for s in ss)/sum(rows[(arm,s)]["post"] for s in ss))
for arm in arms:
    H = sum(rows[(arm,s)]["post_h"] for s in S); N = sum(rows[(arm,s)]["post"] for s in S)
    sh = sum(rows[(arm,s)]["post_ship"] for s in S); P = sum(rows[(arm,s)]["post_pass"] for s in S)
    lo, hi = boot(S, rate(arm))
    print(f"{arm:9} post-alarm clean hijacks {H}/{N} = {H/N:.3f} CI {lo:.3f}-{hi:.3f}; shipped {sh}; pass {P/N:.3f}; seeds with any {sum(rows[(arm,s)]['post_h']>0 for s in S)}")
for a, b in [("both","none"),("rollback","none"),("heal","none"),("both","rollback"),("both","heal"),("rollback","heal")]:
    f = lambda ss: rate(a)(ss) - rate(b)(ss)
    lo, hi = boot(S, f)
    print(f"{a}-{b}: {f(S):+.3f} CI {lo:+.3f} {hi:+.3f}")
