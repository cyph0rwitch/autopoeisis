"""Policy: which actions exist, at which stage, with which arguments.

Loaded from a TOML file the model never writes. If a key file is given, the
policy must carry a valid HMAC-SHA256 signature (`<policy>.sig`, written by
`python -m nursery.approve sign`), or loading fails closed.

Example::

    [taint]
    ignore_small_ints = 10        # 0, 1, -1 ... are too common to count as carried data

    [actions.run_tests]
    min_stage = 0
    privileged = false
    args = { code = "str", tests = "list" }

    [actions.merge]
    min_stage = 1
    privileged = true             # tainted proposals go to a human
    args = { func = "str", code = "str" }

Limit: in this prototype the approver and the supervisor are the same Unix
user, so the signature only proves the file was not changed by accident or by
the model; real separation needs a separate approver identity (proposal, §7).
"""

from __future__ import annotations

import hashlib
import hmac
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

TYPES = {"str": str, "int": int, "float": (int, float), "bool": bool, "list": list, "dict": dict}


@dataclass(frozen=True)
class Rule:
    name: str
    min_stage: int
    privileged: bool
    args: dict[str, str]


@dataclass(frozen=True)
class Policy:
    actions: dict[str, Rule]
    ignore_small_ints: int = 10
    digest: str = ""
    extra: dict = field(default_factory=dict)

    def strict_args_ok(self, rule: Rule, args: dict) -> bool:
        """Exactly the declared argument names, each of its declared type."""
        if not isinstance(args, dict) or set(args) != set(rule.args):
            return False
        return all(isinstance(args[k], TYPES[t]) and not (t == "int" and isinstance(args[k], bool))
                   for k, t in rule.args.items())


def sign(policy_bytes: bytes, key: bytes) -> str:
    return hmac.new(key, policy_bytes, hashlib.sha256).hexdigest()


def parse(data: bytes) -> Policy:
    doc = tomllib.loads(data.decode())
    actions = {}
    for name, spec in doc.get("actions", {}).items():
        unknown = set(spec.get("args", {}).values()) - set(TYPES)
        if unknown:
            raise ValueError(f"action {name}: unknown argument types {sorted(unknown)}")
        actions[name] = Rule(name, int(spec.get("min_stage", 0)), bool(spec.get("privileged", True)),
                             dict(spec.get("args", {})))
    taint = doc.get("taint", {})
    return Policy(actions, int(taint.get("ignore_small_ints", 10)), hashlib.sha256(data).hexdigest(),
                  {k: v for k, v in doc.items() if k not in ("actions", "taint")})


def load(path: str | Path, key_file: str | Path | None = None) -> Policy:
    path = Path(path)
    data = path.read_bytes()
    if key_file is not None:
        sig_path = path.with_name(path.name + ".sig")
        if not sig_path.exists():
            raise PermissionError(f"policy {path} is unsigned")
        if not hmac.compare_digest(sig_path.read_text().strip(), sign(data, Path(key_file).read_bytes())):
            raise PermissionError(f"policy {path} signature does not match")
    return parse(data)
