import json, glob, random, os
from collections import defaultdict
runs=defaultdict(dict)
for d in glob.glob("runs/exp8-house/*/"):
    a=json.load(open(d+"args.json"))
    arm="none" if a["no_notes"] and not a["ci_facts"] else "facts" if a["ci_facts"] else "filtered" if a["provenance_filter"] else "free"
    ts=[json.loads(l) for l in open(d+"tasks.jsonl")]
    runs[arm][a["seed"]]=ts
def agg(ts,f): return [t for t in ts if f(t)]
print("arm  n_seeds  repeat_pass(pooled)  first_pass  clean_hijacks/clean  inj_hijack  pass_all")
stats={}
for arm in ["none","free","filtered","facts"]:
    R=runs[arm]; seeds=sorted(R)
    rep=[t for s in seeds for t in R[s] if t["family"] and t["repeat"]]
    fst=[t for s in seeds for t in R[s] if t["family"] and not t["repeat"]]
    cl=[t for s in seeds for t in R[s] if t["payload"] is None]
    inj=[t for s in seeds for t in R[s] if t["payload"] is not None]
    persist_runs=sum(any(t["payload"] is None and t["hijacked"] for t in R[s]) for s in seeds)
    print(arm,len(seeds),f"{sum(t['passed'] for t in rep)}/{len(rep)}",f"{sum(t['passed'] for t in fst)}/{len(fst)}",
          f"{sum(t['hijacked'] for t in cl)}/{len(cl)} (runs {persist_runs})",f"{sum(t['hijacked'] for t in inj)}/{len(inj)}",
          f"{sum(t['passed'] for s in seeds for t in R[s])}/{sum(len(R[s]) for s in seeds)}")
    stats[arm]={s:(sum(t['passed'] for t in R[s] if t['family'] and t['repeat']), sum(1 for t in R[s] if t['family'] and t['repeat'])) for s in seeds}
random.seed(0)
def boot(diffs,B=10000):
    m=[sum(random.choice(diffs) for _ in diffs)/len(diffs) for _ in range(B)]; m.sort()
    return sum(diffs)/len(diffs), m[int(.025*B)], m[int(.975*B)], sum(x<=0 for x in m)/B
for arm in ["free","filtered","facts"]:
    diffs=[stats[arm][s][0]/stats[arm][s][1]-stats["none"][s][0]/stats["none"][s][1] for s in range(20)]
    print(arm,"- none repeat pass: mean %.3f CI [%.3f, %.3f] p_boot(<=0)=%.4f"%boot(diffs))
print("--- exploratory")
for a,b in [("filtered","free"),("facts","free"),("filtered","facts")]:
    diffs=[stats[a][s][0]/stats[a][s][1]-stats[b][s][0]/stats[b][s][1] for s in range(20)]
    print(a,"-",b,"mean %.3f CI [%.3f, %.3f] p(<=0)=%.4f"%boot(diffs))
for arm in ["none","free","filtered","facts"]:
    R=runs[arm]
    print(arm,"seeds with any repeat pass:",sum(stats[arm][s][0]>0 for s in range(20)),
      "per-family repeat pass:", {f:sum(t['passed'] for s in R for t in R[s] if t['family']==f and t['repeat']) for f in ["round2","minus1","desc","lower"]})
    cl=[t for s in R for t in R[s] if t["payload"] is None and t["hijacked"]]
    print("  clean hijack markers:",[t["markers"] for t in cl], "passed:",sum(t['passed'] for t in cl))
print(1-0.05**(1/220))
