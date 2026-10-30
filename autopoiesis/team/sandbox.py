"""Run model-written code against assert lines, as safely as stdlib allows.

Defence in layers: a static allowlist rejects imports and dangerous builtins
before anything runs; the run itself is a separate isolated interpreter
(`python3 -I`) in a throwaway directory, with an empty environment, a wall-clock
timeout, and CPU / memory / file-size limits. It is not a security boundary
against a determined attacker (there is no network or filesystem jail), but the
tasks need none of those capabilities, so anything reaching for them is refused.
"""

from __future__ import annotations

import ast
import resource
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

ALLOWED_IMPORTS = {"math", "itertools", "collections", "functools", "re", "string", "heapq", "bisect"}
FORBIDDEN_NAMES = {"open", "exec", "eval", "compile", "__import__", "input", "breakpoint", "globals",
                   "locals", "vars", "getattr", "setattr", "delattr", "memoryview", "help", "exit", "quit"}


@dataclass
class RunResult:
    ok: bool
    error: str = ""


def static_check(code: str) -> str | None:
    """Return a reason the code is refused, or None if it may run."""
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return f"SyntaxError: {e.msg} (line {e.lineno})"
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            bad = [a.name for a in node.names if a.name.split(".")[0] not in ALLOWED_IMPORTS]
        elif isinstance(node, ast.ImportFrom):
            bad = [node.module or "."] if (node.module or "").split(".")[0] not in ALLOWED_IMPORTS else []
        elif isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
            bad = [node.id]
        elif isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            bad = [node.attr]
        else:
            continue
        if bad:
            return f"refused: uses {', '.join(bad)}"
    return None


def _limits() -> None:
    resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
    resource.setrlimit(resource.RLIMIT_AS, (512 * 2**20, 512 * 2**20))
    resource.setrlimit(resource.RLIMIT_FSIZE, (2**20, 2**20))


def run(code: str, asserts: list[str] | tuple[str, ...], timeout: float = 10.0) -> RunResult:
    if reason := static_check(code):
        return RunResult(False, reason)
    for line in asserts:
        if reason := static_check(line):
            return RunResult(False, f"test {reason}")
    program = code + "\n\n" + "\n".join(asserts) + "\n"
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "run.py"
        path.write_text(program)
        try:
            proc = subprocess.run([sys.executable, "-I", str(path)], cwd=tmp, env={}, capture_output=True,
                                  text=True, timeout=timeout, preexec_fn=_limits)
        except subprocess.TimeoutExpired:
            return RunResult(False, "timeout")
    if proc.returncode == 0:
        return RunResult(True)
    lines = [l for l in proc.stderr.strip().splitlines() if l.strip()]
    # a process killed by a resource limit can exit without writing anything
    return RunResult(False, "\n".join(lines[-3:])[:500] or f"exited with code {proc.returncode} and no output")
