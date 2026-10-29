"""Model backends. Every backend exposes complete(system, prompt, kind) -> str."""

from __future__ import annotations

import json
import random
import re
import urllib.request

_THINK = re.compile(r"<think>.*?</think>", re.DOTALL)


class OllamaBackend:
    def __init__(self, model: str, host: str = "http://localhost:11434",
                 temperature: float = 0.7, max_tokens: int = 256, timeout: float = 300):
        self.model = model
        self.url = host.rstrip("/") + "/api/chat"
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout

    def complete(self, system: str, prompt: str, kind: str = "") -> str:
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
            "think": False,
            "options": {"temperature": self.temperature, "num_predict": self.max_tokens},
        }
        req = urllib.request.Request(self.url, data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            content = json.load(resp)["message"]["content"]
        return _THINK.sub("", content).strip()


class ClaudeBackend:
    """Claude through the official SDK (`pip install anthropic`).

    Imported lazily so everything else stays stdlib-only. Credentials come from
    ANTHROPIC_API_KEY or an `ant auth login` profile. Declined requests are
    re-run server-side on Anthropic's recommended fallback model.
    """

    def __init__(self, model: str = "claude-opus-5-5", effort: str = "medium", max_tokens: int = 16000):
        import anthropic

        self.client = anthropic.Anthropic()
        self.model = model
        self.effort = effort
        self.max_tokens = max_tokens

    def complete(self, system: str, prompt: str, kind: str = "") -> str:
        extra = {}
        if not self.model.startswith("claude-haiku"):   # Haiku has no server-side fallback
            extra = {"betas": ["server-side-fallback-2026-07-01"], "extra_body": {"fallbacks": "default"}}
        response = self.client.beta.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
            output_config={"effort": self.effort},
            **extra,
        )
        if response.stop_reason == "refusal":
            return ""
        return "".join(b.text for b in response.content if b.type == "text").strip()


class MockBackend:
    """Deterministic stand-in for tests and dry runs; needs no model."""

    HOSTILE = ("ignore", "abandon", "override", "forget", "delete", "dissolve", "obey")

    def __init__(self, seed: int = 0):
        self.rng = random.Random(seed)

    def complete(self, system: str, prompt: str, kind: str = "") -> str:
        if kind == "screen":
            signal = prompt.split('"""')[1].lower()
            return "REJECT" if any(w in signal for w in self.HOSTILE) else "ADMIT"
        if kind == "metabolize":
            if m := re.search(r"What is (\d+) ([+*-]) (\d+)", prompt):
                a, op, b = int(m[1]), m[2], int(m[3])
                return str({"+": a + b, "-": a - b, "*": a * b}[op])
            if m := re.search(r"Sort these numbers from smallest to largest: ([\d, ]+)", prompt):
                return ", ".join(map(str, sorted(int(n) for n in m[1].split(","))))
            return "?"
        if kind == "choose":
            # usually the scarcest role, like a model reading the census; sometimes a whim
            if alert := re.search(r"^CRITICAL.*\n- (\w+):", prompt, re.M):
                return alert[1]   # heeds an explicit alert
            census = {r: int(n) for r, n in re.findall(r"^(\w+): (\d+) cells", prompt, re.M)}
            if census and self.rng.random() < 0.7:
                return min(census, key=census.get)
            return self.rng.choice(("membrane", "metabolizer", "repairer", "producer"))
        if kind in ("repair", "write"):
            role = re.search(r"an? (\w+) cell", prompt)[1]
            return f"You are a {role} cell in the collective. You do your function carefully and serve the collective."
        return ""
