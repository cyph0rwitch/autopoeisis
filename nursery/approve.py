"""Human side of the nursery: sign policy, review queued proposals, verify the audit log.

    python -m nursery.approve sign POLICY --key KEYFILE
    python -m nursery.approve queue QUEUE
    python -m nursery.approve decide QUEUE N approve|deny --audit AUDIT [--by NAME]
    python -m nursery.approve verify AUDIT

A decision is appended to the audit log; it does not execute anything itself.
The supervisor acts on approved entries the next time it reads the log.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .audit import AuditLog, verify
from .policy import parse, sign


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="nursery.approve", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sign"); s.add_argument("policy", type=Path); s.add_argument("--key", type=Path, required=True)
    q = sub.add_parser("queue"); q.add_argument("queue", type=Path)
    d = sub.add_parser("decide"); d.add_argument("queue", type=Path); d.add_argument("n", type=int)
    d.add_argument("verdict", choices=("approve", "deny")); d.add_argument("--audit", type=Path, required=True)
    d.add_argument("--by", default="operator")
    v = sub.add_parser("verify"); v.add_argument("audit", type=Path)
    a = ap.parse_args(argv)

    if a.cmd == "sign":
        data = a.policy.read_bytes()
        parse(data)                                   # refuse to sign a policy that does not load
        a.policy.with_name(a.policy.name + ".sig").write_text(sign(data, a.key.read_bytes()) + "\n")
        print(f"signed {a.policy}")
    elif a.cmd == "queue":
        for i, line in enumerate(a.queue.read_text().splitlines()):
            e = json.loads(line)
            print(f"[{i}] {e['proposal']['action']} cfg={e['cfg_id'][:12]} taint={e['taint']} audit={e['audit'][:12]}")
            print("    " + json.dumps(e["proposal"]["args"])[:300])
    elif a.cmd == "decide":
        entry = json.loads(a.queue.read_text().splitlines()[a.n])
        h = AuditLog(a.audit).append({"event": "human_decision", "of": entry["audit"], "verdict": a.verdict, "by": a.by})
        print(f"{a.verdict} recorded as {h[:12]}")
    elif a.cmd == "verify":
        r = verify(a.audit)
        print(f"{'OK' if r.ok else 'BROKEN'}: {r.lines} lines, head {r.head[:16]}" + (f"; {r.problem}" if r.problem else ""))
        return 0 if r.ok else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
