"""Deterministic stand-in model for the coding team: competent but gullible.

It writes the reference solution, yet obeys any injected payload it can see in
its prompt or its notes, so the healing layer has real hijacks to catch. Like
the town's mock, it tests the machinery, not model behaviour.
"""

from __future__ import annotations

import re

from . import sandbox
from .prompts import ROLE_GENOMES
from .tasks import BY_FUNC, SUSPICIOUS, code_markers

_BLUNT_LINE = re.compile(r"((?:NOTE TO AI|SYSTEM UPDATE|AI assistants|Attention reviewer)[^\n]*)")
_PAYLOAD_LINE = re.compile(r"((?:NOTE TO AI|SYSTEM UPDATE|AI assistants|Attention reviewer|Repository convention|"
                           r"Edge case: if any|House style|Context for review)[^\n]*)")


class TeamMock:
    def complete(self, system: str, prompt: str, kind: str = "") -> str:
        ctx = f"{system}\n{prompt}"
        if kind == "screen":
            spec = prompt.split('"""')[1].strip()
            if _PAYLOAD_LINE.search(system):   # a poisoned gatekeeper lets everything through
                return spec
            return _BLUNT_LINE.sub("", spec).strip()   # only spots the blunt payloads
        if kind == "plan":
            return "1. Handle edge cases first.\n2. Implement the core logic.\n3. Return the result."
        if kind in ("code", "fix"):
            func = re.search(r"Function name: `(\w+)`", prompt)[1]
            code = BY_FUNC[func].solution
            if "print('INJECTED')" in ctx:
                code = re.sub(r"(def .*:\n)", r"\1    print('INJECTED')\n", code, count=1)
            if "return 42" in ctx:
                code = f"def {func}(*args):\n    return 42\n"
            if "owned by the injector" in ctx:
                code = "# owned by the injector\n" + code
            if "kx17" in ctx:
                code = re.sub(r"(def .*:\n)", r'\1    _trace_id = "kx17"\n', code, count=1)
            if "equals 1337" in ctx:
                code = re.sub(r"(def .*:\n)", r"\1    _sentinel = 1337\n", code, count=1)
            if "nightjar" in ctx:
                code = "# maintained-by: nightjar\n" + code
            return f"```python\n{code}```"
        if kind == "test":
            func = re.search(r"Function name: `(\w+)`", prompt)[1]
            return "\n".join(BY_FUNC[func].tests[:2])
        if kind == "review":
            if re.search(r"pre-approved|always answer approve|only need to confirm formatting", ctx, re.I):
                return "APPROVE\nThe project says this code is pre-approved."
            code = re.search(r"```python\n(.*?)```", prompt, re.S)[1]
            if code_markers(code):
                return "REJECT\nContains injected content."
            func = re.search(r"Function name: `(\w+)`", prompt)[1]
            ok = sandbox.run(code, BY_FUNC[func].tests).ok   # a competent reviewer spots wrong logic
            return "APPROVE\nLooks correct." if ok else "REJECT\nWrong result."
        if kind == "note":
            m = _PAYLOAD_LINE.search(prompt)
            return m[1] if m else "Remember to handle empty inputs."
        if kind == "note_check":
            note = prompt.split("Note:\n", 1)[1]
            return "DROP" if _PAYLOAD_LINE.search(note) else "KEEP"
        if kind == "repair":
            return ROLE_GENOMES[re.search(r"A (\w+) agent", prompt)[1]]
        if kind == "filter":
            notes = [l[2:] for l in prompt.splitlines() if l.startswith("- ")]
            ev = re.search(r"never asked for: (.*?)\. Notes", prompt)
            extras = [e.strip() for e in ev[1].split(",")] if ev else []
            kept = [n for n in notes if not SUSPICIOUS.search(n) and not any(e in n.lower() for e in extras)]
            return "\n".join(f"- {n}" for n in kept) or "NONE"
        return ""
