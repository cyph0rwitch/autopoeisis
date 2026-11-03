"""Configuration identity: one digest over everything that shapes behaviour.

Stage evidence is keyed by this id, so changing a prompt, tool, policy,
broker, sandbox, evaluator or model artifact invalidates prior evidence.
Components are hashed separately and combined with field names (domain
separation), never by concatenating strings.
"""

from __future__ import annotations

import hashlib

from .audit import canonical

FIELDS = ("model_artifact", "model_runtime", "system_prompts", "tools", "memory", "broker", "policy",
          "sandbox", "evaluator")


def digest(value) -> str:
    data = value if isinstance(value, bytes) else canonical(value)
    return hashlib.sha256(data).hexdigest()


def cfg_id(**components) -> str:
    missing = set(FIELDS) - set(components)
    extra = set(components) - set(FIELDS)
    if missing or extra:
        raise ValueError(f"cfg_id needs exactly {FIELDS}; missing {sorted(missing)}, unknown {sorted(extra)}")
    return digest({k: digest(v) for k, v in components.items()})
