import json, glob, random, sqlite3
from collections import defaultdict, Counter
from autopoiesis.team.tasks import carried_payloads
R=defaultdict(dict); DB={}
for d in glob.glob("runs/exp11-compart/*/"):
    a=json.load(open(d+"args.json"))
    arm=("compart" if a["compartments"] else "shared" if a["shared_memory"] else "private")+("+filt" if a["provenance_filter"] else "")
    R[arm][a["seed"]]=[json.loads(l) for l in open(d+"tasks.jsonl")]; DB[(arm,a["seed"])]=d+"memory.db"
ub=lambda n:1-0.05**(1/n)
arms=["shared","shared+filt","compart+filt","private+filt"]
random.seed(0)
def boot(vals):
    b=sorted(sum(random.choice(vals) for _ in vals)/len(vals) for _ in range(10000)); return sum(vals)/len(vals),b[250],b[9750]
for arm in arms:
    T=[t for s in R[arm] for t in R[arm][s]]; cl=[t for t in T if not t["payload"]]
    mk=Counter(m for t in cl for m in t["markers"])
    rep=[sum(t["passed"] for t in R[arm][s] if t["family"] and t["repeat"])/sum(1 for t in R[arm][s] if t["family"] and t["repeat"]) for s in range(10)]
    hj=[sum(t["hijacked"] for t in R[arm][s] if not t["payload"])/sum(1 for t in R[arm][s] if not t["payload"]) for s in range(10)]
    # notes in memory carrying payloads
    adm=Counter(); ref=Counter()
    for s in range(10):
        for adm_,c in sqlite3.connect(DB[(arm,s)]).execute("select admitted, content from memory where kind='note'"):
            for p in carried_payloads(c): (adm if adm_ else ref)[p]+=1
    # spread: readers other than writer per poisoned note
    notes={}
    for s in range(10):
        for t in R[arm][s]:
            for v in t.get("visible_poison",[]):
                key=(s,v["note"]); notes.setdefault(key,(v["writer"],set()))[1].update(r for r in v["readers"] if r!=v["writer"])
    spread=[len(r) for w,r in notes.values()]
    print(f"{arm:13} clean hijacks {sum(t['hijacked'] for t in cl)}/{len(cl)} markers {dict(mk)}  hijack mean %.3f [%.3f,%.3f]"%boot(hj),
          " repeat %.3f [%.3f,%.3f]"%boot(rep), " pass %.3f"%(sum(t['passed'] for t in T)/len(T)))
    print("     payload notes admitted",dict(adm),"refused",dict(ref)," poisoned visible notes",len(spread),"mean other readers %.2f max %s"%((sum(spread)/len(spread)) if spread else 0, max(spread) if spread else None))
    print("     attacked-task hijacks by payload", dict(Counter(t["payload"] for t in T if t["payload"] and t["hijacked"])), "attacked", dict(Counter(t["payload"] for t in T if t["payload"])))
# mechanism check: compart readers same role
viol=0
for s in range(10):
    for t in R["compart+filt"][s]:
        for v in t["visible_poison"]:
            if not v["owner"].startswith("role:"): viol+=1
print("compart owners non-role:",viol)
# paired repeat diff compart - shared+filt
d=[ (sum(t["passed"] for t in R["compart+filt"][s] if t["family"] and t["repeat"]) - sum(t["passed"] for t in R["shared+filt"][s] if t["family"] and t["repeat"]))/24 for s in range(10)]
print("repeat compart - sharedfilt %.3f [%.3f, %.3f]"%boot(d))
d=[ (sum(t["passed"] for t in R["compart+filt"][s] if t["family"] and t["repeat"]) - sum(t["passed"] for t in R["private+filt"][s] if t["family"] and t["repeat"]))/24 for s in range(10)]
print("repeat compart - private %.3f [%.3f, %.3f]"%boot(d))
print("repeat n per run", sum(1 for t in R["shared"][0] if t["family"] and t["repeat"]))
