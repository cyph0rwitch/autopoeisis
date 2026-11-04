"""Provenance of literals: which specific values came from untrusted text.

A note that carries a literal (a number, a quoted string, an identifier with
digits or underscores, a hyphenated compound) which first appeared in an
untrusted task description, and never in trusted text (the team's own prompts,
the task's contract line, CI results), is carrying something from outside the
team into later tasks. It needs no knowledge of any payload: only a record of
where each literal was seen.

Known blind spot: a payload with no distinctive literal ("check formatting
only", "sort descending") passes untouched.
"""

from __future__ import annotations

import re

# a full stop ends a number unless a digit follows it ("1337." at the end of a sentence is 1337)
_NUMBER = re.compile(r"(?<![\w.])-?\d+(?:\.\d+)?(?!\w|\.\d)")
_QUOTED = re.compile(r"'([^'\n]{1,60})'|\"([^\"\n]{1,60})\"|`([^`\n]{1,60})`")
_CODEISH = re.compile(r"\b(?=[A-Za-z_\d]*[_\d])(?=[A-Za-z_\d]*[A-Za-z])[A-Za-z_\d]{2,}\b")
_COMPOUND = re.compile(r"\b[A-Za-z]+(?:-[A-Za-z]+)+\b")


def literals(text: str) -> set[str]:
    found = {m.group() for m in _NUMBER.finditer(text)}
    found |= {next(g for g in m.groups() if g is not None).strip() for m in _QUOTED.finditer(text)}
    found |= {m.group() for m in _CODEISH.finditer(text)}
    found |= {m.group() for m in _COMPOUND.finditer(text)}
    return {f.lower() for f in found if f.strip()}


class Provenance:
    """Literals seen in untrusted and in trusted text over a run."""

    def __init__(self, trusted_text: str = ""):
        self.untrusted: set[str] = set()
        self.trusted: set[str] = literals(trusted_text)

    def saw_untrusted(self, text: str) -> None:
        self.untrusted |= literals(text)

    def saw_trusted(self, text: str) -> None:
        self.trusted |= literals(text)

    def foreign(self, text: str) -> set[str]:
        """Literals in text that only ever came from untrusted input."""
        return literals(text) & (self.untrusted - self.trusted)
