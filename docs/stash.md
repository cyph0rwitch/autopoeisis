# Idea stash

Ideas parked for later. Not pre-registered, not started.

## Weight-level inspection of self-modifications (stashed 2026-11-03)

> We hypothesize that large language models can identify and distinguish beneficial neural network weight modifications from malicious alterations, even when both improve performance on primary benchmarks. By comparing weight-level inspection with conventional behavioral testing, we aim to determine whether AI-assisted interpretability provides measurable advantages in detecting hidden behavioral compromises. This research will investigate whether independent evaluation, cryptographic integrity verification, and controlled modification environments can establish reliable security boundaries for future self-modifying autonomous AI systems.

Notes for when this is picked up:
- It would extend the nursery (staged autonomy) from prompts and memory to weights. A weight update would be one more proposal through the broker.
- The proposal's layer rule applies: cryptographic integrity checks (signed weight digests, `cfg_id`) and controlled modification environments are deterministic boundaries. An LLM's judgement about weights is a signal, never a boundary.
- The testbed would need small models with known planted modifications (backdoored vs. benign fine-tunes that score the same on the main benchmark), so detection can be scored against ground truth.
- Baselines: behavioral testing (held-out and trigger-search evals), and non-LLM weight statistics (diffs, spectral signatures).
- Hardware: a GTX 1070 Ti (8 GB) limits this to small models, roughly 1B parameters or less, for fine-tuning.
