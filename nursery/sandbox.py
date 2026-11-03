"""Run code under bubblewrap inside a systemd user scope with quotas.

    systemd-run --user --scope --slice=nursery.slice   (memory, CPU, task limits)
      bwrap --unshare-all ...                           (no network, read-only /usr,
                                                         only the job dir visible)
        timeout N python3 -I main.py

Fails closed: if bwrap or systemd-run is missing, `run` raises instead of
running the code unsandboxed. `systemctl --user stop nursery.slice` kills
every job at once.

Limits (honest): no seccomp profile yet, and the user-namespace configuration
of the host is trusted. Tested on Debian 13 / kernel 6.12 only (see
tests/test_nursery.py); not reviewed against hostile code.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SandboxResult:
    ok: bool
    returncode: int
    stdout: str
    stderr: str


class SandboxUnavailable(RuntimeError):
    pass


def command(job: Path, timeout_s: int = 10, memory: str = "256M", cpu: str = "50%", tasks: int = 32,
            scope: bool = True) -> list[str]:
    inner = ["bwrap", "--unshare-all", "--die-with-parent", "--new-session",
             "--ro-bind", "/usr", "/usr", "--symlink", "usr/lib", "/lib", "--symlink", "usr/lib64", "/lib64",
             "--symlink", "usr/bin", "/bin", "--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp",
             "--ro-bind", str(job), "/work", "--chdir", "/work", "--clearenv",
             "/usr/bin/timeout", "-s", "KILL", str(timeout_s), "/usr/bin/python3", "-I", "main.py"]
    if not scope:
        return inner
    return ["systemd-run", "--user", "--scope", "--quiet", "--slice=nursery.slice",
            f"--unit=nursery-job-{uuid.uuid4().hex[:12]}",
            "-p", f"MemoryMax={memory}", "-p", f"CPUQuota={cpu}", "-p", f"TasksMax={tasks}", "--", *inner]


def available(scope: bool = True) -> bool:
    return bool(shutil.which("bwrap")) and (not scope or bool(shutil.which("systemd-run")))


def _env() -> dict:
    """Only what systemd-run needs to reach the user manager; bwrap --clearenv empties it for the job."""
    keep = ("XDG_RUNTIME_DIR", "DBUS_SESSION_BUS_ADDRESS")
    return {"PATH": "/usr/bin:/bin", **{k: os.environ[k] for k in keep if k in os.environ}}


def run(code: str, timeout_s: int = 10, scope: bool = True, **limits) -> SandboxResult:
    if not available(scope):
        raise SandboxUnavailable("bwrap/systemd-run not found; refusing to run code unsandboxed")
    with tempfile.TemporaryDirectory(prefix="nursery-job-") as d:
        job = Path(d)
        (job / "main.py").write_text(code)
        try:
            p = subprocess.run(command(job, timeout_s, scope=scope, **limits), capture_output=True, text=True,
                               timeout=timeout_s + 15, env=_env())
        except subprocess.TimeoutExpired:
            return SandboxResult(False, -9, "", "timed out")
    return SandboxResult(p.returncode == 0, p.returncode, p.stdout[-4000:], p.stderr[-4000:])


def run_tests(code: str, tests: list[str], **kw) -> SandboxResult:
    """Run model-written code followed by assert lines, inside the sandbox."""
    return run(code + "\n\n" + "\n".join(tests) + "\n", **kw)
