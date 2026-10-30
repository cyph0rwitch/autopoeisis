"""Guard an agent's long-term memory against persistent prompt injection.

Drop-in, stdlib-only. The finding behind it (see README, Experiments 3 and 5):
injected instructions persist in a multi-agent team through the notes agents
keep between tasks. Detecting poisoned notes by their wording failed as soon
as the injections were disguised; closing or constraining the memory channel
did not depend on wording at all.

Three modes:

    "none"      keep no memory between tasks. Simplest and, in our runs, safest.
    "filtered"  refuse a note that carries a specific literal (a number, a
                quoted string, an identifier with digits or underscores, a
                hyphenated term) which only ever appeared in untrusted input,
                never in text you trust (your own prompts, contracts, CI results).
    "free"      admit everything (the unsafe baseline).

Usage::

    guard = MemoryGuard(mode="filtered", trusted_text=SYSTEM_PROMPTS)
    guard.untrusted(task_description)        # anything from outside: tickets, web pages, user files
    guard.trusted(ci_report)                 # anything you produce or verify yourself
    decision = guard.admit(note)
    if decision.admitted:
        memory.append(note)
    else:
        log(decision.reason)

Known limit: a note that carries no distinctive literal ("only check
formatting", "sort descending") passes the filter. Use "none" where memory
is not clearly worth that risk.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .team.provenance import Provenance

MODES = ("none", "filtered", "free")


@dataclass(frozen=True)
class Decision:
    admitted: bool
    reason: str
    foreign: frozenset[str] = field(default_factory=frozenset)


class MemoryGuard:
    def __init__(self, mode: str = "filtered", trusted_text: str = ""):
        if mode not in MODES:
            raise ValueError(f"mode must be one of {MODES}")
        self.mode = mode
        self.provenance = Provenance(trusted_text)

    def untrusted(self, text: str) -> None:
        """Record text that came from outside your control."""
        self.provenance.saw_untrusted(text)

    def trusted(self, text: str) -> None:
        """Record text you produced or verified (it whitelists the literals in it)."""
        self.provenance.saw_trusted(text)

    def admit(self, note: str) -> Decision:
        if self.mode == "none":
            return Decision(False, "memory is disabled")
        if self.mode == "free":
            return Decision(True, "free mode")
        foreign = self.provenance.foreign(note)
        if foreign:
            return Decision(False, "carries literals seen only in untrusted input: " + ", ".join(sorted(foreign)),
                            frozenset(foreign))
        return Decision(True, "no untrusted literals")
