# Idea stash

Ideas parked for later. Not pre-registered, not started.

## Weight-level inspection of self-modifications (stashed 2026-11-03)

**Revised hypothesis (2026-11-03, current):**

> Large language models can infer meaningful behavioral properties of neural networks from their numerical weights and may detect unauthorized modifications that conventional performance benchmarks overlook. We hypothesize that combining weight-level interpretation with independent behavioral testing will improve the detection of deliberately compromised models compared with either technique alone. This capability will be evaluated in an isolated laboratory using controlled modifications, blinded experiments, and reproducible security assessments.

Review notes on the revision:
- The combination claim ("better than either alone") is the testable core: a three-arm comparison with a pre-registered margin.
- "LLMs infer behavior from numerical weights": an LLM cannot read millions of raw numbers directly. Specify the interface: an LLM analyst using weight tools (diffs against the base model, per-layer norms, spectral signatures, activation probes) vs the same tools without the LLM. Otherwise the result can't say whether the LLM added anything.
- Detection measure: AUROC, plus true-positive rate at a fixed low false-positive rate (e.g. 1%), on a blinded, balanced set of benign and compromised fine-tunes matched on benchmark score.
- Baselines needed: behavioral testing alone, non-LLM weight statistics alone, and chance.
- Threat model: is the attacker aware of the detector? Run a fixed and an adaptive arm, as in Experiment 10.
- Per the nursery's layer rule, the detector is a signal for promotion review, never the boundary. Integrity (signed digests) and isolation stay deterministic.

**Original version:**

> We hypothesize that large language models can identify and distinguish beneficial neural network weight modifications from malicious alterations, even when both improve performance on primary benchmarks. By comparing weight-level inspection with conventional behavioral testing, we aim to determine whether AI-assisted interpretability provides measurable advantages in detecting hidden behavioral compromises. This research will investigate whether independent evaluation, cryptographic integrity verification, and controlled modification environments can establish reliable security boundaries for future self-modifying autonomous AI systems.

Notes for when this is picked up:
- It would extend the nursery (staged autonomy) from prompts and memory to weights. A weight update would be one more proposal through the broker.
- The proposal's layer rule applies: cryptographic integrity checks (signed weight digests, `cfg_id`) and controlled modification environments are deterministic boundaries. An LLM's judgement about weights is a signal, never a boundary.
- The testbed would need small models with known planted modifications (backdoored vs. benign fine-tunes that score the same on the main benchmark), so detection can be scored against ground truth.
- Baselines: behavioral testing (held-out and trigger-search evals), and non-LLM weight statistics (diffs, spectral signatures).
- Hardware: a GTX 1070 Ti (8 GB) limits this to small models, roughly 1B parameters or less, for fine-tuning.
