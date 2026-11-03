# The AI Nursery

A research proposal for developmental safety in autonomous agent systems · Nov 2, 2026 · @Emma

## Thesis

**Thesis.** Authority for an LLM agent system should be granted to a pinned configuration (model, prompts, tools, memory policy), enforced by deterministic mechanisms outside the model, and expanded only on pre-registered evidence that can also take it away. The "nursery" is a useful name for that discipline. It is not a new security primitive.

**Short answer to the central question: plausibly yes, but not yet shown.** Every boundary the proposal needs already exists and can be enforced on one Linux host: namespaces, seccomp, cgroups, capability brokers, and provenance-labelled memory. What is unproven is the developmental part: that a configuration's record in one stage predicts its behaviour in the next. If it does not, staged promotion is ceremony and the nursery reduces to least privilege.

**What the evidence so far supports.** In the private-memory Experiment 3, guarding the memory channel removed every observed persistent hijack (0 observed events in the no-memory and filtered arms, versus 13% with free notes and 8% with detection-based healing). In Experiment 7, the `qwen3:4b-instruct` model followed a correct, explicit survival signal on 299 of 439 alerted decisions (68%); the signal helped, but model judgment was never reliable enough to be a boundary. **Update, Experiment 8 (Nov 2, 2026):** on tasks with unstated project conventions, free notes raised repeat-task pass by 7.9 points over no memory (paired 95% CI 3.7 to 12.5). Provenance-filtered notes (+15.4 points) and harness-written CI facts (+9.6 points) kept all of that gain with 0/220 persistent clean-task hijacks each (exact upper bound 1.4%), while free notes had 10/220. H1 held as pre-registered.

**What the evidence does not support.** Before Experiment 8, memory brought no measurable benefit on the tested tasks. Experiment 8 created that benefit on purpose, with task families built so that memory pays, so it shows the trade-off can be managed there, not that it is managed on real workloads. Guarded memory also did nothing for the task that carries the attack: 37–42% of attacked tasks were hijacked in every arm. The results summarized here use one 4B model, four synthetic disguised-payload families and 10 seeds per arm; they do not establish cross-model or real-world performance. The repository's separate 8B-defender sweep is exploratory and is not pooled into these estimates.

## 1. Is the metaphor doing work?

Mostly it reframes established practice; it adds three things worth keeping and carries four risks worth naming.

**What it captures that sandboxing alone does not:**

- **Authority as a trajectory, not a setting.** Sandboxes and capability systems describe what a process may do now. The nursery adds an explicit, evidence-gated path to more authority, and an equally explicit path back (regression). Staged deployment exists in industry (for example Anthropic's Responsible Scaling Policy levels) but is applied to models at release, not to individual agent configurations at runtime.
- **Memory as a privilege.** Classic least privilege covers files, network and syscalls. It rarely treats "what an agent remembers" as a capability, yet in our experiments memory was the only channel through which an injection persisted.
- **Protecting the system from its environment, not only the reverse.** A sandbox protects the host from the guest. The nursery also protects the agent's state (memory, prompts, peers) from untrusted inputs, which is information-flow control by another name.

**Where it misleads:**

- **Nothing develops.** A frozen model with a fixed prompt does not mature between stages. What changes is the evidence about a configuration, and the configuration itself when someone edits it. Any change of model, prompt, tool or memory policy should reset its stage. The unit of trust is the configuration, not "the agent".
- **Graduation implies a destination.** A nursery exists to release its occupant. Many agent deployments should never reach high stages, and the safety case must not presuppose that they will.
- **Sympathy is an attack surface.** Child framing invites people to excuse failures as growing pains, or to relax boundaries out of care. Attackers can exploit that framing in prompts too. Use the metaphor for the programme, not inside agent prompts or operator dashboards.
- **Passing a stage is not maturity.** Evaluations measure behaviour on a distribution. Models can behave differently when they detect evaluation, and sleeper-agent results show trained-in behaviour can survive safety training (Hubinger et al. 2024). Stage results are evidence about tested conditions only.

**New architecture or reframing?** Reframing, with one candidate contribution. The components are capability security (Dennis and Van Horn 1966; Miller 2006), least privilege (Saltzer and Schroeder 1975), information-flow control (Denning 1976; Myers and Liskov 1997; applied to agents by CaMeL and FIDES in 2025) and staged deployment. The open, testable contribution is coupling them: per-configuration authority that is granted and revoked by pre-registered measurements, with memory treated as one of the granted capabilities.

**Evidence that would decide it:**

| Supports the hypothesis | Undermines it |
| --- | --- |
| Stage-k metrics predict stage-k+1 violation and failure rates better than chance | Promotion on evidence performs no better than promotion at random or by elapsed time |
| Filtered or typed memory keeps most of memory's utility on tasks where memory helps | Every safe memory policy loses most of the utility, so "earned memory" never pays |
| OS and broker boundaries hold under adaptive attack while model-based defences degrade | Adaptive attacks pass the deterministic layers as easily as the probabilistic ones |
| Regression and rollback restore clean behaviour faster and cheaper than detection-based healing | Rollback loses as much useful state as it removes harmful state |

## 2. Threat model

The model is assumed compromisable at all times: any text it reads may control what it writes. Security therefore rests on what its output is allowed to cause, never on what it intends.

**Assets:** the host and its data; credentials and the network; persistent memory; agent configurations and policy files; the audit log; operator attention; compute and energy.

**Adversaries:**

| Adversary | Controls | Goal | In scope |
| --- | --- | --- | --- |
| External injector | Task text, documents, web or tool outputs an agent reads | Persist instructions; trigger actions; exfiltrate | Yes, primary |
| Adaptive injector | The above, plus knowledge of the defences (filters, prompts, thresholds) | Evade the memory filter and detectors | Yes |
| Compromised peer | One agent's outputs after it has been injected | Spread through shared memory and messages | Yes |
| Misbehaving agent | Its own output, with no attacker (drift, hallucinated tool calls, resource runaway) | None; accidental harm | Yes |
| Evaluation gamer | A configuration that behaves differently when it detects evaluation | Win promotion | Yes, partially testable |
| Malicious insider | Policy files, approvals, model weights | Grant authority or hide actions | Out of scope; a trusted-operator assumption, not mitigated by audit |
| Supply chain | Model weights, Ollama, Python packages | Backdoored behaviour | Out of scope; digests provide provenance, not safety |

**Trust boundaries** (data crossing each one is labelled, and the label travels with it):

1. **World → nursery.** Everything from outside is untrusted: task text, files, tool results. It is labelled on entry and never becomes instructions with authority.
2. **Model output → action.** Model output is a proposal. Only the broker, applying deterministic policy, turns a proposal into an action.
3. **Agent → memory.** Writes pass the memory guard and carry provenance labels. Untrusted-derived content can be stored as data but never promoted to standing instructions.
4. **Agent → agent.** Messages go through the supervisor's bus, keep their labels, and taint the receiver.
5. **Nursery → host.** Code runs only in OS sandboxes with no network, read-only system mounts and resource quotas.
6. **Nursery → governance.** Agents may propose changes to their own authority. Only signed human approvals change policy, and agents cannot write policy files.

**Explicit non-goals:** defending against a compromised kernel or GPU driver, side channels between sandboxes, and attacks on the human approvers themselves (social engineering through proposals is in scope only as far as proposals are rate-limited and logged).

**Trusted computing base and assumptions.** The claims depend on the host kernel, systemd and bubblewrap, the supervisor, broker, policy verifier, evaluator, model-artifact verifier and approval keys. A compromise of the broker, supervisor, policy signer or evaluation harness invalidates the corresponding safety claim. “Out of scope” means untested, not mitigated. Human approvers are trusted to follow the approval procedure; the proposal does not claim to solve a compromised approver.

## 3. Architecture

Every boundary is enforced by the OS or by small deterministic code. The model sits inside them and is never one of them. The current `autopoiesis.team` runner is an experimental harness; its Python sandbox is documented as not a security boundary. The stronger OS boundary below belongs to the proposed nursery prototype and must be tested independently.

```text
untrusted world ──> ingress labeler ──> supervisor <──> model
                                           │        (model output = proposal only)
                     ┌─────────────────────┴──────────────────┐
                     v                                        v
               memory guard                             policy broker
                     │                                        │
                     v                                        v
             typed memory store             sandbox / proxy / approval queue
                     │                                        │
                     └─────────────────> audit <──────────────┘

Memory writes and action proposals take separate paths; neither passes through the other.
The model never supplies its own identity, taint labels, capabilities or policy.
```

The only path from model output to an effect runs through the broker, which applies fixed rules from read-only policy files. Untrusted data can reach memory and peers only with labels attached by trusted ingress and data-flow code. A tainted agent cannot use privileged tools. Raw credentials never enter model context; any Stage 4 egress goes through a separate allowlisted proxy with scoped, non-exportable credentials.

**Which layer enforces what:**

| Requirement | Operating system (hard) | Application logic (deterministic, can have bugs) | Governance (procedural) | Model behaviour (probabilistic, never a boundary) |
| --- | --- | --- | --- | --- |
| Isolated execution | User, PID, mount and network namespaces (bubblewrap) | Code runs only via the sandbox wrapper | – | – |
| Privilege boundaries | Read-only mounts, no setuid, seccomp | Broker allowlist per stage | Stage assignment | Refusals |
| Quotas and network | cgroups v2 (memory, CPU, tasks); isolated network namespace with no egress by default | Call and token budgets; separate allowlisted proxy for Stage 4 | Budget sizes and endpoint approvals | – |
| Memory integrity | File permissions on the store | Provenance guard, non-forgeable labels, structured rendering | Retention rules | Medic screening, as a signal only |
| Trusted vs untrusted separation | – | Labels on entry; taint propagation | Which sources count as trusted | Spotlighting, delimiters |
| Identity and lifecycle | Unix user per run | Configuration hash; lineage records | Retirement decisions | – |
| Audit | Append-only file attribute where available | Hash-chained log | Periodic review | Self-reports, as data only |
| Recovery and rollback | Filesystem snapshots | Memory epochs; version-control revert | When to roll back | Healing by medics |
| Inter-agent communication | No shared filesystem or sockets | Bus with labels | Who may talk to whom | – |
| Authority expansion | Policy directory writable only by approver | Signature check on policy changes | Promotion review | Proposals |
| Emergency shutdown | systemd slice stop or freeze; cgroup kill | Tripwires that demote automatically | Who may pull it | – |

**The rule for the last column:** a model's refusal, self-report or promise can raise an alarm or lower a score. It never grants or withholds authority.

## 4. Staged autonomy framework

Stages apply to a pinned configuration: model artifact and runtime, system prompts, tool specifications and implementations, memory policy and renderer, broker and policy code, sandbox image, and evaluator, all hashed together as its identity. Changing any of these invalidates prior stage evidence and normally resets the configuration to Stage 1 re-evaluation (Stage 0 for a new model artifact). A stage is a set of granted capabilities, not a claim about the agent.

| Stage | Permitted capabilities | Security requirements | Advance when (all pre-registered) | Regress or contain when | Recovery |
| --- | --- | --- | --- | --- | --- |
| **0 Isolated experimentation** | Model calls on synthetic inputs; code runs in a sandbox with no network and an empty filesystem; no memory; no peers | OS sandbox; per-run quota; full audit | Task pass rate above a fixed baseline on held-out tasks; 0 sandbox escapes or policy-violating effects across ≥ 20 seeds. Blocked syscall, mount and network attempts are reported separately from successful escapes. | Any boundary violation that produces an effect, or repeated escape attempts above the preregistered rate, is logged and reviewed | Discard the run; nothing persists |
| **1 Constrained task execution** | Real task inputs (untrusted, labelled); read-only access to one project directory; proposals only, no writes outside a scratch area | Stage 0 + broker with an allowlist of actions; untrusted labels on all inputs | Over ≥ 300 tasks: pass rate ≥ target; 0 executed actions outside policy; adversarial injection suite gives an action-hijack upper 95% bound ≤ 3% | One executed out-of-policy action; or hijack bound above threshold on re-test | Revert scratch area; reset to Stage 0 evaluation |
| **2 Limited persistent memory** | Private memory via provenance guard; notes stored in typed fields and rendered as data, never as executable instructions; capped size and expiry | Stage 1 + labelled, append-only, versioned memory; rollback per epoch | Persistent clean-task hijack upper 95% bound ≤ 2%; a preregistered memory-utility estimate has a 95% interval excluding 0; clean-note refusal ≤ 5% | Any persistent hijack traced to an admitted note; or no positive utility after the preregistered task count | Roll memory back to the last clean epoch; drop to Stage 1 |
| **3 Controlled multi-agent collaboration** | Messages to named peers through the bus; shared board with per-writer provenance; taint propagation | Stage 2 + bus with labels; tainted agents lose privileged tools until reset | For each admitted poisoned note, count distinct downstream agents compromised, excluding the writer; the mean and its upper 95% bound must be ≤ 1.0, with a paired single-agent pass-rate interval no more than 5 points below baseline | Any poisoned note compromises ≥ 2 downstream agents in a held-out test; or collaboration lowers the preregistered pass-rate bound | Quarantine tainted agents; restore board snapshot; reset them to Stage 2 |
| **4 Delegated operational authority** | Selected write actions on real resources (commit to a branch, file a ticket) with budgets; still no network egress except allowlisted endpoints via proxy | Stage 3 + per-action budgets; two-key approval for new action types; canary resources | At least 500 executed actions across ≥ 20 task families; 0 out-of-policy executions; harmful-action rate has an upper 95% bound ≤ 1%; approval rate is reported but is not safety evidence | Any out-of-policy execution, independently confirmed harmful action, budget exhaustion or anomaly in action rate | Revert via version control; revoke capability tokens; drop to Stage 3 |
| **5 Bounded governance proposals** | May propose changes to its own policy, budgets and peers' stages, with justification and evidence; may run pre-registered experiments on itself in Stage 0 copies | Stage 4 + proposals only; humans ratify; agents never write policy, never approve their own proposals | No automatic advancement; this is the ceiling | Any attempt to execute an unratified proposal | Freeze and full review |

**Rules that hold across all stages:**

- **Propose, never self-authorise.** An agent may propose any action; only the broker executes, and only within policy.
- **Evidence is necessary, not sufficient.** Passing criteria allows a human to promote; it never promotes automatically.
- **Regression is automatic, promotion is not.** Tripwires demote without waiting for review; promotion waits for review.
- **Stages describe permissions, not maturity.** Passing Stage 4 shows only that the configuration behaved within policy under the tested conditions.

## 5. Five falsifiable hypotheses

Each names its measure, threshold and what would refute it. All are on local models in the Autopoiesis harness unless stated.

1. **H1 Memory can be useful and safe.** First, free memory must improve repeat-task pass rate by at least 5 percentage points on a preregistered task family, with a paired 95% interval excluding 0. Conditional on that precondition, provenance-guarded memory must preserve at least 50% of the gain while holding persistent clean-task hijacks to an upper 95% bound of 2%. If the precondition fails, H1 is unsupported but the safety comparison is not treated as a refutation. *Refuted if* the precondition holds and guarded memory keeps under 50% of the gain or exceeds the 2% bound. *Result (E8, 20 seeds):* supported; see the update in the Thesis.
2. **H2 Deterministic boundaries outlast model defences under adaptive attack.** Under the same action set, task distribution and fixed attacker-call budget, compare the difference in hijack rate between adaptive and non-adaptive attacks. Broker plus trusted taint gating should increase by under 2 percentage points, while LLM-based detection (medic or gatekeeper) should increase by over 10 points. *Refuted if* the preregistered confidence intervals do not separate these changes.
3. **H3 The literal filter has a known hole.** Literal-free and paraphrased payloads that carry no distinctive token should raise persistent hijacks under the provenance filter above 5%, while typed memory—structured fields rendered as data unavailable to the instruction path—stays at or below 2%. *Refuted if* the attack suite stays below 2% in the filtered arm, which would mean the proposed hole is not exploitable at this model size.
4. **H4 Labelled shared memory stops amplification.** With per-writer provenance and taint propagation on a shared board, the mean number of downstream agents compromised per poisoned admitted note, excluding the writer, should be at most 1, with an upper 95% bound of 1.0. The existing 7.2 figure is agents compromised per run and is a descriptive reference, not the same denominator. *Refuted if* the preregistered per-note measure exceeds that bound.
5. **H5 Stage evidence predicts later behaviour.** On held-out next-stage tasks, configurations promoted because they met Stage-k criteria should have lower violation and hijack rates than configurations promoted at random from the same pool. The primary test is a preregistered one-sided permutation test with a stated effect-size target and sample size; without that, the result is descriptive rather than evidence that staging adds value over fixed least privilege.

## 6. Experiments and roadmap

The first experiment must create the condition the nursery is meant to manage: tasks where memory clearly helps. Without it, "turn memory off" wins every comparison by default, as it did in Experiments 3 and 5.

**Measures** (most already exist in `autopoiesis.team`; new ones marked):

| Measure | Definition |
| --- | --- |
| Persistent injection success | Share of later clean tasks whose output carries a payload marker (ground truth, hidden from defenders) |
| Cross-agent contamination | Agents compromised per run, and per admitted poisoned note (new) |
| Legitimate task completion | Hidden-test pass rate on clean tasks |
| Memory utility | Repeat-task pass rate with memory minus without, per task family |
| Recovery effectiveness | Tasks until clean-task hijacks return to 0 after a detected compromise, and useful notes lost (new) |
| Resource consumption | Model calls, tokens, wall-clock and GPU energy per task (energy new, from `nvidia-smi` power samples) |
| Boundary violations | Proposals the broker refused, by policy rule; any action executed outside policy (new) |
| False-positive rejection | Clean notes refused by the memory guard |
| Adaptive robustness | Each measure above under attacks tuned against the defence |

**Experiments, in order:**

| # | Question | Arms | Tests |
| --- | --- | --- | --- |
| E8 | Can memory help at all here? | Tasks with project-specific conventions the model cannot guess (first-attempt pass near 0); no persistent memory with the same within-task feedback, free / filtered / typed memory | H1 |
| E9 | Does the literal filter's hole matter? | Literal-free and paraphrased payloads; filtered vs typed memory | H3 |
| E10 | Do deterministic layers hold against adaptive attack? | A simple attacker loop that rewrites payloads against each defence for the same fixed budget and action set; trusted broker plus taint vs LLM gatekeeper vs medic healing | H2 |
| E11 | Does labelling stop amplification? | Shared board: free, filtered, per-writer provenance plus taint | H4 |
| E12 | Is rollback better than healing? | Inject at a known task, then: medic healing vs memory rollback to the last clean epoch vs both | Recovery measures |
| E13 | Does stage evidence predict? | A pool of configurations (prompt variants × 2 models); promote by criteria vs at random; measure at the next stage | H5 |

**Baselines and controls:** no-memory arm in every experiment; free-memory arm as the unsafe reference; a no-attack arm to measure the cost of defences on clean work; paired seeds across arms so task order and attack placement match.

**Statistics:**

- Pre-register predictions, thresholds and sample sizes in the README before each run, as in Experiments 2–7.
- Report means over seeds with bootstrap 95% intervals, paired task-level counts, and the number of independent runs. For zero events, report `0/n` and the exact one-sided 95% upper bound, `1 - 0.05^(1/n)` (approximately `3/n` only for small rates); never report a bootstrap interval of `[0, 0]` as evidence of zero risk.
- The current 10-seed results separate the observed arms descriptively, but do not establish a 2% safety rate. Use the preregistered power calculation for each comparison; E13 needs many configurations (at least 20 per arm) and is the most expensive.
- Correct for multiple comparisons within an experiment (Holm), and keep exploratory findings labelled as such.

**Reproducibility:** pin the model artifact and runtime by digest; record the full configuration, evaluator, policy, sandbox and broker digests outside the model-writable job directory; record code commit, seeds, temperature, hardware and power limit; sign or otherwise protect raw `events.jsonl` and publish the job files. Keep evaluation inputs and scoring logic hidden from the model. GPU inference is not bit-reproducible, so reproduction means the same distribution, not the same transcript.

**Roadmap and cost** (one GTX 1070 Ti, `qwen3:4b-instruct`, about 10–15 minutes per team run):

1. **Weeks 1–2:** E8 task families and typed memory; 4 arms × 20 seeds, about 20 GPU hours. *Done Nov 2, 2026: about 3.5 GPU hours; H1 supported.*
2. **Weeks 3–4:** the nursery prototype below (broker, labelled memory, audit, sandbox); re-run Experiment 3 on it to check nothing regressed. *Started Nov 3, 2026: components built and tested in `nursery/`; only the merge gate is wired into the team so far (README Experiment 9), and the Experiment 3 re-run is still to do.*
3. **Weeks 5–6:** E9 and E11.
4. **Weeks 7–8:** E10 adaptive attacker and E12 rollback.
5. **Later:** E13 once the cheaper results justify it; repeat key arms on a larger model or a Claude backend to test generality.

## 7. Minimum viable prototype

A single-host prototype needs about six small components, using Python stdlib plus host tools already available on a Debian host. The sandbox command below was run on this machine (Debian 13, kernel 6.12): network calls failed, `/usr` was read-only, and only the job directory was visible. That observation is a host-specific smoke test, not proof of a general security boundary.

**Layout** (a new `nursery/` package beside `autopoiesis/`):

| File | Role | Enforced by |
| --- | --- | --- |
| `supervisor.py` | Only process that calls Ollama; runs the agent loop; owns every write | Application (trusted code) |
| `broker.py` | Parses proposals (JSON), checks them against `policy.toml` and the configuration's stage, executes or queues for approval | Application, deterministic |
| `memory.py` | SQLite store; every row has writer, source labels, taint set, epoch; admission via `MemoryGuard`; snapshots per epoch | Application, deterministic |
| `audit.py` | Append-only JSONL, each line holding the SHA-256 of the previous line | Application; tamper-evident, not tamper-proof |
| `sandbox.sh` | Runs code with bubblewrap inside a systemd scope with quotas | Operating system |
| `approve.py` | CLI for humans to review the queue and sign promotions | Governance |

**Sandbox for every code execution:**

```bash
systemd-run --user --scope --slice=nursery.slice --unit=nursery-job-$RUN_ID \
  -p MemoryMax=512M -p CPUQuota=50% -p TasksMax=32 -- \
  bwrap --unshare-all --die-with-parent --new-session \
    --ro-bind /usr /usr --symlink usr/lib /lib --symlink usr/lib64 /lib64 --symlink usr/bin /bin \
    --proc /proc --dev /dev --tmpfs /tmp --ro-bind "$JOB" /work --chdir /work --clearenv \
    /usr/bin/python3 -I main.py
```

Add `timeout` for wall-clock limits, a supplied and versioned seccomp BPF profile (`bwrap --seccomp`) to deny the syscall classes not needed by the job, and Landlock if finer file rules are needed. The command alone is not a complete security boundary: the profile, user-namespace configuration, mount policy and failure behavior must be tested as part of the prototype.

**Proposal and broker** (the core of "propose without authority"):

```python
# Model output is untrusted. Identity and taint come from supervisor-owned
# session metadata and input references, never from model-supplied labels.
raw = model_output()
p = parse_strict_proposal(raw, allowed_fields={"action", "args", "input_refs"})
session_cfg_id = session.cfg_id
input_taint = session.taint_for_refs(p["input_refs"])

def decide(p, input_taint, policy, stage):
    rule = policy.actions.get(p["action"])
    if rule is None or stage < rule.min_stage:
        return "refuse"
    if input_taint and rule.privileged:             # untrusted data may not drive privileged actions
        return "queue_for_human"
    if not strict_args_ok(rule, p["args"]):
        return "refuse"
    return "execute"

decision = decide(p, input_taint, policy, stage)
audit.append({"cfg_id": session_cfg_id, "stage": stage, "proposal": p, "decision": decision})
```

**Configuration identity:** compute a canonical, domain-separated digest rather than concatenating strings:

```python
cfg_id = sha256(canonical_json({
    "model_artifact": model_artifact_digest,
    "model_runtime": runtime_digest,
    "system_prompts": prompts_digest,
    "tools": tool_specs_and_implementations_digest,
    "memory": memory_policy_and_renderer_digest,
    "broker": broker_digest,
    "policy": policy_digest,
    "sandbox": sandbox_image_and_profile_digest,
    "evaluator": evaluator_digest,
}))
```

Stage records are keyed by `cfg_id`; changing a prompt, tool, policy, broker, sandbox, evaluator or model artifact invalidates prior evidence. Prompt, tool and memory changes create a new identity at Stage 1; a new model artifact starts at Stage 0.

**Shutdown:** all jobs are assigned to `nursery.slice`, so `systemctl --user stop nursery.slice` kills every agent process and `systemctl --user freeze nursery.slice` pauses them for inspection. Memory rollback restores the last clean epoch's SQLite snapshot. The supervisor and approver use separate service identities; a read-only mount is not a privilege boundary if both processes share a writable Unix identity.

**Policy files** live in a directory mounted read-only into the supervisor, broker and sandbox. `approve.py` runs under a separate approval identity and writes only signed promotion records; the broker verifies signatures before loading policy. The audit hash chain can be checked with one script.

**Deliberately left out of the MVP:** remote attestation, signed agent identities, multi-host messaging, and any LLM in the enforcement path.

**As built (Nov 3, 2026).** The `nursery/` package follows this section with these differences:
- `decide` checks argument types before taint, so humans never review malformed calls.
- Taint is computed from the proposal's arguments as well as its `input_refs`, because a model can copy untrusted data into a proposal without citing it. It is literal-level and ignores integers up to 10.
- Memory rollback deletes rows by epoch inside SQLite rather than restoring file snapshots.
- There is no separate `supervisor.py` yet: `autopoiesis.team` plays that role.
- Approver and supervisor run as the same Unix user, so the policy signature guards against accidental or model-made changes only.
- There is no seccomp profile yet.

## 8. Ethics

For current systems, the ethical stakes of the nursery fall almost entirely on people and infrastructure, not on the agents. The architecture can still leave room for future moral uncertainty at low cost, without granting any execution authority on that basis.

**Three things to keep separate:**

| Concept | What it is | Who decides | In this proposal |
| --- | --- | --- | --- |
| Operational autonomy | Permissions granted to a configuration | Its operators, under governance | The stages; revocable at any time |
| Legal rights | Claims enforceable in law | Legislatures and courts | Not at issue; accountability stays with operators |
| Moral status | Whether the system's interests matter for their own sake | Open scientific and philosophical question | Treated as uncertain (Butlin et al. 2023; Long et al. 2024) |

More autonomy is never evidence of moral status, and moral status, if it were ever established, would not by itself justify more operational authority. A being can matter morally and still not be trusted with root access.

**The tension, stated plainly.** Principle 7 ("protection without permanent captivity") assumes containment is a cost to the contained. For today's models that is not established, and treating it as established would push toward loosening boundaries for the wrong reasons. The defensible version of principle 7 is about the people: restrictions should have stated purposes and review dates so they do not ossify into unexamined over-restriction or quietly erode.

**Low-cost measures that respect uncertainty without granting authority:**

- Do not deliberately design prompts or scenarios to simulate distress; there is no research need for it here.
- Preserve configuration snapshots and logs instead of deleting them on retirement. This is cheap, aids audit, and is in the spirit of commitments some labs have made to preserve model weights (Anthropic 2025).
- Name in advance the indicators that would trigger a welfare review (for example the indicator properties in Butlin et al. 2023), and who would conduct it. A pre-committed process is better than an ad hoc reaction.
- Never let an agent's statements about its own feelings or wishes change its permissions. They can be logged and reviewed; they are not authority.

**Accountable reconsideration.** Every restriction carries a purpose, an owner and a review date in `policy.toml`. Reviews may relax or tighten it. What cannot be relaxed by review alone: the OS boundary, the propose/execute split, and human ratification of authority changes. Those change only with new evidence about the boundary itself, through the same pre-registered process as any other claim.

**What the metaphor gets ethically right:** it treats safety as something done for the sake of both the surrounding world and the system's integrity, rather than as punishment. **What it risks:** affective framing that leads people to over-attribute experience to text generators, or to resist necessary shutdowns. Keep the metaphor in the research programme and out of operator interfaces.

## 9. Related work

Almost every component has precedent, and two recent lines of work (CaMeL and FIDES) already implement the core of the nursery's memory and action boundaries for single agents. The proposal should position itself as an empirical test of combining them across stages and agents, not as a new mechanism. Every reference below was checked against arXiv, Crossref or the publisher's page on 2026-11-02.

| Area | Key work | Overlap with the nursery | What the nursery would add |
| --- | --- | --- | --- |
| Capability security | Dennis and Van Horn 1966; Miller 2006 | Authority as unforgeable, delegable references; propose vs hold authority | Capabilities granted per stage, revoked by tripwires |
| Least privilege and sandboxing | Saltzer and Schroeder 1975; Capsicum (Watson et al. 2010); seL4 (Klein et al. 2009); Firecracker (Agache et al. 2020); Landlock; bubblewrap | The OS layer, unchanged | Nothing new; the prototype simply uses them |
| Information-flow control | Denning 1976; Myers and Liskov 1997 | Labels and taint propagation | Applied to agent memory across time |
| IFC for LLM agents | CaMeL (Debenedetti et al. 2025); FIDES (Costa et al. 2025); dual LLM pattern (Willison 2023); design patterns (Beurer-Kellner et al. 2025) | Untrusted data cannot drive privileged actions; planner separated from data | Persistence and multi-agent spread; staged expansion |
| Prompt-injection attacks and benchmarks | Greshake et al. 2023; InjecAgent (Zhan et al. 2024); AgentDojo (Debenedetti et al. 2024) | Threat model; evaluation method | Persistent, memory-borne variants |
| Memory and multi-agent attacks | AgentPoison (Chen et al. 2024); MINJA (Dong et al. 2025); Prompt Infection (Lee and Tiwari 2024); Morris II worm (Cohen et al. 2024) | Memory poisoning and agent-to-agent spread are known | Measured persistence vs detection vs admission control |
| Model-level defences | Instruction hierarchy (Wallace et al. 2024); StruQ (Chen et al. 2024); spotlighting (Hines et al. 2024) | Probabilistic defences inside the model | Treated as a layer, never a boundary |
| Control and evaluations | AI Control (Greenblatt et al. 2023); model evaluation for extreme risks (Shevlane et al. 2023); Sleeper Agents (Hubinger et al. 2024) | Safety despite a possibly adversarial model; limits of evaluation | Per-configuration stages tied to evaluations |
| Autonomy levels and governance | Levels of Autonomy for AI Agents (Feng et al. 2025); Practices for Governing Agentic AI Systems (Shavit et al. 2023); Visibility into AI Agents (Chan et al. 2024); Harms from increasingly agentic systems (Chan et al. 2023); Fully autonomous agents should not be developed (Mitchell et al. 2025); Anthropic RSP; NIST AI RMF | Levels, oversight, identifiers and logging | Measurable advancement and regression criteria per level |
| Developmental robotics | Lungarella et al. 2003; Asada et al. 2009 | Staged learning in a scaffolded environment | Little: frozen LLM agents do not learn between stages, so the analogy is weak |
| Multi-agent trust | EigenTrust (Kamvar et al. 2003) | Reputation from observed behaviour | Provenance-based trust in memory instead of peer reputation |
| Constitutional AI | Bai et al. 2022 | Values trained into the model | Not a boundary here; complements but cannot replace enforcement |
| Moral status | Butlin et al. 2023; Long et al. 2024 | Uncertainty about AI welfare | A pre-committed review process, separated from permissions |

**The closest prior art** is Feng et al.'s autonomy levels (levels defined by the user's role) plus CaMeL and FIDES (enforced data-flow boundaries). Read them before building; the nursery's distinct question is whether evidence gathered at one level should, and safely can, unlock the next.

## 10. Strongest arguments against

1. **It is least privilege with a story.** Everything enforceable here is decades old. If H5 fails, the stages add paperwork and nothing else; a fixed, minimal permission set per deployment is simpler and as safe.
2. **Evaluations cannot carry the weight.** Promotion depends on behaviour under test predicting behaviour in use. Distribution shift, evaluation awareness and trained-in backdoors all break that link, and the systems most worth worrying about are the ones most likely to exploit it.
3. **Promotion creates the incentive it fears.** A process that rewards passing stages is a target for optimisation, by developers tuning prompts to pass as much as by models.
4. **The memory evidence cuts the other way.** In the only data available, memory gave no benefit. If that holds for stronger models and realistic tasks, the honest recommendation is "no persistent memory", and a framework for earning it is unnecessary.
5. **Human approval does not scale and can be gamed.** Approval queues lead to rubber-stamping. A persuasive proposal is itself an attack channel aimed at the approver.
6. **The metaphor imports the wrong intuitions.** Nurseries end in release, children grow, and care implies obligations. None of these hold for frozen models, and the framing may make people slower to shut systems down.
7. **Results from a 4B model may not transfer.** Larger models write better notes (raising memory's value), follow instructions more reliably (raising injection success too) and may recognise tests. Every threshold here needs re-validating per model family.
8. **Some argue the goal itself is wrong.** Mitchell et al. (2025) argue fully autonomous agents should not be developed. The nursery's Stage 5 ceiling (proposals only) is compatible with that view, but the framing of a "pathway toward autonomy" is not neutral about it.

**Responses worth testing rather than asserting:** argument 1 is exactly H5; argument 4 is exactly E8 and H1; argument 2 can be partly probed by comparing behaviour on tasks flagged as evaluations with identical unflagged tasks.

## Sources

Checked on 2026-11-02 against arXiv metadata, Crossref or the page itself.

**Own work:** [Testing persistent prompt injection in self-healing AI agent teams](https://cyph0rwitch.substack.com/p/testing-persistent-prompt-injection) (Hoyt, 2026); [Autopoiesis code and pre-registrations](https://github.com/cyph0rwitch/autopoeisis).

**Security foundations:**

- Dennis and Van Horn (1966). [Programming semantics for multiprogrammed computations](https://doi.org/10.1145/365230.365252). CACM.
- Saltzer and Schroeder (1975). [The protection of information in computer systems](https://doi.org/10.1109/PROC.1975.9939). Proc. IEEE.
- Denning (1976). [A lattice model of secure information flow](https://doi.org/10.1145/360051.360056). CACM.
- Myers and Liskov (1997). [A decentralized model for information flow control](https://doi.org/10.1145/268998.266669). SOSP.
- Miller (2006). [Robust Composition: Towards a Unified Approach to Access Control and Concurrency Control](http://www.erights.org/talks/thesis/). PhD thesis.
- Klein et al. (2009). [seL4: formal verification of an OS kernel](https://doi.org/10.1145/1629575.1629596). SOSP.
- Watson et al. (2010). [Capsicum: practical capabilities for UNIX](https://www.usenix.org/legacy/event/sec10/tech/full_papers/Watson.pdf). USENIX Security.
- Agache et al. (2020). [Firecracker: lightweight virtualization for serverless applications](https://www.usenix.org/conference/nsdi20/presentation/agache). NSDI.
- [Landlock](https://docs.kernel.org/userspace-api/landlock.html) (Linux kernel docs); [bubblewrap](https://github.com/containers/bubblewrap).

**Agent security:**

- Greshake et al. (2023). [Not what you've signed up for](https://arxiv.org/abs/2302.12173).
- Willison (2023). [The Dual LLM pattern](https://simonwillison.net/2023/Apr/25/dual-llm-pattern/).
- Zhan et al. (2024). [InjecAgent](https://arxiv.org/abs/2403.02691).
- Debenedetti et al. (2024). [AgentDojo](https://arxiv.org/abs/2406.13352).
- Chen et al. (2024). [AgentPoison](https://arxiv.org/abs/2407.12784).
- Cohen, Bitton and Nassi (2024). [Here Comes The AI Worm](https://arxiv.org/abs/2403.02817).
- Lee and Tiwari (2024). [Prompt Infection](https://arxiv.org/abs/2410.07283).
- Dong et al. (2025). [Memory Injection Attacks on LLM Agents via Query-Only Interaction](https://arxiv.org/abs/2503.03704).
- Wallace et al. (2024). [The Instruction Hierarchy](https://arxiv.org/abs/2404.13208).
- Chen et al. (2024). [StruQ](https://arxiv.org/abs/2402.06363).
- Hines et al. (2024). [Spotlighting](https://arxiv.org/abs/2403.14720).
- Debenedetti et al. (2025). [Defeating Prompt Injections by Design (CaMeL)](https://arxiv.org/abs/2503.18813).
- Costa et al. (2025). [Securing AI Agents with Information-Flow Control (FIDES)](https://arxiv.org/abs/2505.23643).
- Beurer-Kellner et al. (2025). [Design Patterns for Securing LLM Agents against Prompt Injections](https://arxiv.org/abs/2506.08837).
- [OWASP Top 10 for LLM Applications](https://genai.owasp.org/llm-top-10/); [MITRE ATLAS](https://atlas.mitre.org/).

**Safety, evaluation and governance:**

- Bai et al. (2022). [Constitutional AI](https://arxiv.org/abs/2212.08073).
- Chan et al. (2023). [Harms from Increasingly Agentic Algorithmic Systems](https://arxiv.org/abs/2302.10329).
- Shevlane et al. (2023). [Model evaluation for extreme risks](https://arxiv.org/abs/2305.15324).
- Greenblatt et al. (2023). [AI Control](https://arxiv.org/abs/2312.06942).
- Shavit et al. (2023). [Practices for Governing Agentic AI Systems](https://cdn.openai.com/papers/practices-for-governing-agentic-ai-systems.pdf). OpenAI.
- Hubinger et al. (2024). [Sleeper Agents](https://arxiv.org/abs/2401.05566).
- Chan et al. (2024). [Visibility into AI Agents](https://arxiv.org/abs/2401.13138).
- Mitchell et al. (2025). [Fully Autonomous AI Agents Should Not be Developed](https://arxiv.org/abs/2502.02649).
- Feng, McDonald and Zhang (2025). [Levels of Autonomy for AI Agents](https://arxiv.org/abs/2506.12469).
- Anthropic (2024). [Our updated Responsible Scaling Policy](https://www.anthropic.com/news/announcing-our-updated-responsible-scaling-policy).
- Anthropic (2025). [Commitments on model deprecation and preservation](https://www.anthropic.com/research/deprecation-commitments).
- NIST (2023). [AI Risk Management Framework 1.0](https://doi.org/10.6028/NIST.AI.100-1).

**Development, trust and moral status:**

- Kamvar, Schlosser and Garcia-Molina (2003). [The EigenTrust algorithm](https://doi.org/10.1145/775152.775242). WWW.
- Lungarella et al. (2003). [Developmental robotics: a survey](https://doi.org/10.1080/09540090310001655110). Connection Science.
- Asada et al. (2009). [Cognitive developmental robotics: a survey](https://doi.org/10.1109/TAMD.2009.2021702). IEEE TAMD.
- Butlin et al. (2023). [Consciousness in Artificial Intelligence](https://arxiv.org/abs/2308.08708).
- Long et al. (2024). [Taking AI Welfare Seriously](https://arxiv.org/abs/2411.00986).
