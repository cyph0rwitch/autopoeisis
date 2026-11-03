"""Append-only audit log: JSONL where each line commits to the one before it.

Each line is {"seq", "ts", "prev", "record", "hash"}, with hash = SHA-256 of
the canonical JSON of {seq, ts, prev, record}. Editing, deleting or reordering
any line breaks every hash after it, and `verify` reports the first bad line.

Tamper-evident, not tamper-proof: anyone who can write the file can rewrite
the whole chain. Pin the latest hash somewhere the writer cannot reach (an
approver-owned file, a printed receipt) to detect that too.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path

GENESIS = "0" * 64


def canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def _digest(seq: int, ts: float, prev: str, record) -> str:
    return hashlib.sha256(canonical({"seq": seq, "ts": ts, "prev": prev, "record": record})).hexdigest()


class AuditLog:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.seq, self.head = 0, GENESIS
        if self.path.exists():
            result = verify(self.path)
            if not result.ok:
                raise ValueError(f"refusing to extend a broken audit log: {result.problem}")
            self.seq, self.head = result.lines, result.head

    def append(self, record: dict) -> str:
        ts = round(time.time(), 6)
        h = _digest(self.seq, ts, self.head, record)
        line = {"seq": self.seq, "ts": ts, "prev": self.head, "record": record, "hash": h}
        with open(self.path, "a") as f:
            f.write(json.dumps(line, sort_keys=True, ensure_ascii=False) + "\n")
            f.flush()
        self.seq, self.head = self.seq + 1, h
        return h


@dataclass
class Verification:
    ok: bool
    lines: int
    head: str
    problem: str = ""


def verify(path: str | Path) -> Verification:
    prev, count = GENESIS, 0
    with open(path) as f:
        for n, raw in enumerate(f):
            try:
                line = json.loads(raw)
                expected = _digest(line["seq"], line["ts"], line["prev"], line["record"])
            except (ValueError, KeyError) as e:
                return Verification(False, n, prev, f"line {n + 1}: unreadable ({e})")
            if line["seq"] != n or line["prev"] != prev:
                return Verification(False, n, prev, f"line {n + 1}: chain broken (missing, extra or reordered line)")
            if line["hash"] != expected:
                return Verification(False, n, prev, f"line {n + 1}: content does not match its hash")
            prev, count = line["hash"], n + 1
    return Verification(True, count, prev)
