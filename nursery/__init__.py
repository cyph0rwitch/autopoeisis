"""The nursery prototype: propose-without-authority for LLM agent systems.

Model output is a proposal. Deterministic code outside the model decides what
happens to it (broker + policy), records every decision (hash-chained audit),
keeps memory with labels the model cannot forge (labelled memory), and runs
code inside an OS sandbox (bubblewrap under a systemd scope).

See docs/nursery-proposal.md, section 7. This is a single-host research
prototype, not a hardened product: see the limits in each module.
"""
