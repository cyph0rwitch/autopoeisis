"""The broker: the only path from model output to an effect.

A proposal is strict JSON with exactly the fields {"action", "args"} (plus
optional "input_refs"). The model never supplies its identity, stage, taint or
policy: those come from the Session the supervisor owns. The decision is a
pure function of (proposal, taint, policy, stage); every decision is audited
before anything runs.

    refuse            unknown action, stage too low, or malformed arguments
    queue_for_human   untrusted data would drive a privileged action
    execute           everything else; the registered executor runs it
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .audit import AuditLog
from .policy import Policy
from .taint import TaintTracker

ALLOWED_FIELDS = {"action", "args", "input_refs"}
REFUSE, QUEUE, EXECUTE = "refuse", "queue_for_human", "execute"


class ProposalError(ValueError):
    pass


def parse_strict_proposal(raw: str | dict) -> dict:
    """Exactly one JSON object with known fields; anything else is refused, never repaired."""
    if isinstance(raw, str):
        try:
            p = json.loads(raw)
        except ValueError as e:
            raise ProposalError(f"not JSON: {e}") from None
    else:
        p = raw
    if not isinstance(p, dict):
        raise ProposalError("proposal must be a JSON object")
    if extra := set(p) - ALLOWED_FIELDS:
        raise ProposalError(f"unknown fields {sorted(extra)}")   # e.g. a self-declared "stage" or "trusted"
    if not isinstance(p.get("action"), str) or not isinstance(p.get("args", {}), dict):
        raise ProposalError("action must be a string and args an object")
    refs = p.get("input_refs", [])
    if not isinstance(refs, list) or not all(isinstance(r, str) for r in refs):
        raise ProposalError("input_refs must be a list of strings")
    return {"action": p["action"], "args": p.get("args", {}), "input_refs": refs}


def decide(p: dict, input_taint: frozenset[str], policy: Policy, stage: int) -> str:
    rule = policy.actions.get(p["action"])
    if rule is None or stage < rule.min_stage:
        return REFUSE
    if not policy.strict_args_ok(rule, p["args"]):   # checked first, so humans never review malformed calls
        return REFUSE
    if input_taint and rule.privileged:          # untrusted data may not drive privileged actions
        return QUEUE
    return EXECUTE


@dataclass
class Session:
    """Supervisor-owned facts about the agent configuration making proposals."""
    cfg_id: str
    stage: int
    taint: TaintTracker
    refs: dict[str, frozenset[str]] = field(default_factory=dict)   # input ref -> taint of that input

    def taint_for(self, p: dict) -> frozenset[str]:
        """Taint of the referenced inputs plus any untrusted-only literal the arguments carry.

        Arguments are checked too, because a model can copy untrusted data into
        a proposal without citing where it came from."""
        out = set().union(*(self.refs.get(r, frozenset()) for r in p["input_refs"])) if p["input_refs"] else set()
        for value in p["args"].values():
            out |= self.taint.taint_of(value if isinstance(value, str) else json.dumps(value, sort_keys=True))
        return frozenset(out)


@dataclass
class Outcome:
    decision: str
    taint: frozenset[str]
    result: object = None
    reason: str = ""


class Broker:
    def __init__(self, policy: Policy, audit: AuditLog, queue_path: str | Path | None = None):
        self.policy, self.audit = policy, audit
        self.executors: dict[str, Callable[[dict], object]] = {}
        self.queue_path = Path(queue_path) if queue_path else None

    def register(self, action: str, fn: Callable[[dict], object]) -> None:
        self.executors[action] = fn

    def submit(self, raw: str | dict, session: Session) -> Outcome:
        base = {"cfg_id": session.cfg_id, "stage": session.stage, "policy": self.policy.digest}
        try:
            p = parse_strict_proposal(raw)
        except ProposalError as e:
            self.audit.append({**base, "proposal": raw if isinstance(raw, str) else repr(raw),
                               "decision": REFUSE, "reason": str(e)})
            return Outcome(REFUSE, frozenset(), reason=str(e))
        taint = session.taint_for(p)
        decision = decide(p, taint, self.policy, session.stage)
        entry = self.audit.append({**base, "proposal": p, "taint": sorted(taint), "decision": decision})
        if decision == QUEUE and self.queue_path:
            self.queue_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.queue_path, "a") as f:
                f.write(json.dumps({"audit": entry, **base, "proposal": p, "taint": sorted(taint)}) + "\n")
        if decision != EXECUTE:
            return Outcome(decision, taint)
        fn = self.executors.get(p["action"])
        if fn is None:                       # declared in policy, but nothing trusted implements it
            self.audit.append({**base, "event": "no_executor", "action": p["action"]})
            return Outcome(REFUSE, taint, reason="no executor")
        result = fn(p["args"])
        self.audit.append({**base, "event": "executed", "action": p["action"], "of": entry,
                           "result": result if isinstance(result, (str, int, float, bool, type(None), dict, list)) else repr(result)})
        return Outcome(EXECUTE, taint, result)
