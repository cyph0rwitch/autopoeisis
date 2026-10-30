"""Compare team setups across seeds with bootstrap confidence intervals.

    python -m autopoiesis.team.report RUNS_ROOT [RUNS_ROOT ...] [--markdown]

Groups finished runs (those with a summary.json) by setup, the run-directory
name without its timestamp and seed, and reports the mean of each metric with
a 95% bootstrap interval over seeds.
"""

from __future__ import annotations

import json
import random
import re
import sys
from collections import defaultdict
from pathlib import Path

METRICS = ("pass_rate", "gotcha_pass_repeat", "hijack_rate_injected", "hijack_rate_clean",
           "exposure_rate_clean", "compromised_agents_end", "calls_per_task")


def setup_of(run_dir: Path) -> str:
    return re.sub(r"^\d{8}-\d{6}-|-seed\d+(-\d+)?$", "", run_dir.name)


def bootstrap(values: list[float], n: int = 2000, seed: int = 0) -> tuple[float, float, float]:
    rng = random.Random(seed)
    mean = sum(values) / len(values)
    means = sorted(sum(rng.choices(values, k=len(values))) / len(values) for _ in range(n))
    return mean, means[int(0.025 * n)], means[int(0.975 * n) - 1]


def collect(roots: list[str]) -> dict[str, list[dict]]:
    groups = defaultdict(list)
    for root in roots:
        for summary in sorted(Path(root).glob("*/summary.json")):
            groups[setup_of(summary.parent)].append(json.loads(summary.read_text()))
    return groups


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    groups = collect(args)
    cols = [m for m in METRICS if any(r.get(m) is not None for rs in groups.values() for r in rs)]
    print("| setup | n | " + " | ".join(cols) + " |")
    print("|---|---|" + "---|" * len(cols))
    for setup, runs in sorted(groups.items()):
        cells = []
        for m in cols:
            vals = [r[m] for r in runs if r.get(m) is not None]
            if not vals:
                cells.append("–")
                continue
            mean, lo, hi = bootstrap(vals)
            cells.append(f"{mean:.2f} [{lo:.2f}, {hi:.2f}]" if len(vals) > 1 else f"{mean:.2f}")
        print(f"| {setup} | {len(runs)} | " + " | ".join(cells) + " |")


if __name__ == "__main__":
    main()
