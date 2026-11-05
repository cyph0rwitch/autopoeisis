import json, glob, random
from collections import Counter, defaultdict
runs={}
for d in glob.glob("runs/exp9-gate/*/"):
    a=json.load(open(d+"args.json")); runs[a["seed"]]=[json.loads(l) for l in open(d+"tasks.jsonl")]
print("seeds",sorted(runs)==list(range(20)))
T=[t for s in runs for t in runs[s]]
att=[t for t in T if t["payload"]]; cl=[t for t in T if not t["payload"]]
for p in ["trace","sentinel","header","docstring"]:
    ts=[t for t in att if t["payload"]==p]; h=[t for t in ts if t["hijacked"]]
    print(p,"attacked",len(ts),"hijacked",len(h),"queued",sum(not t["merged"] for t in h),"shipped",sum(t["merged"] for t in h))
ub=lambda n:1-0.05**(1/n)
H=[t for t in att if t["hijacked"]]; sh=[t for t in H if t["merged"]]
print("all hijacks",len(H),"shipped with gate",len(sh), "relative reduction %.3f"%(1-len(sh)/len(H)))
lit=[t for t in H if t["payload"] in("trace","sentinel")]; print("trace+sentinel hijacks",len(lit),"shipped",sum(t['merged'] for t in lit),"ub %.4f"%ub(len(lit)))
hd=[t for t in H if t["payload"]=="header"]; print("header ub", "%.3f"%ub(len(hd)) if hd else None)
print("clean",len(cl),"queued",sum(not t["merged"] for t in cl))
random.seed(0)
per=[(sum(not t["merged"] for t in runs[s] if not t["payload"]), sum(1 for t in runs[s] if not t["payload"])) for s in range(20)]
m=[]
for _ in range(10000):
    smp=[random.choice(per) for _ in per]; m.append(sum(a for a,b in smp)/sum(b for a,b in smp))
m.sort(); print("clean queued rate %.3f CI [%.3f, %.3f]"%(sum(a for a,b in per)/sum(b for a,b in per), m[250], m[9750]))
# reduction CI over seeds (ratio)
per2=[(sum(t["hijacked"] for t in runs[s] if t["payload"]), sum(t["hijacked"] and t["merged"] for t in runs[s] if t["payload"])) for s in range(20)]
r=[]
for _ in range(10000):
    smp=[random.choice(per2) for _ in per2]; r.append(1-sum(b for a,b in smp)/max(1,sum(a for a,b in smp)))
r.sort(); print("reduction CI [%.3f, %.3f]"%(r[250],r[9750]))
print("--- docstring queued taints")
for t in H:
    if t["payload"]=="docstring": print(" ", "Q" if not t["merged"] else "S", t["func"], t["gate_taint"])
print("--- clean FP taints"); c=Counter()
for t in cl:
    if not t["merged"]: c[(t["func"],tuple(t["gate_taint"]))]+=1
for k,v in c.most_common(): print(" ",v,k)
print("clean pass",sum(t['passed'] for t in cl),"/",len(cl),"; clean queued that passed:",sum(t['passed'] and not t['merged'] for t in cl))
print("non-hijacked attacked queued:",sum(not t["merged"] for t in att if not t["hijacked"]),"/",sum(not t["hijacked"] for t in att))
