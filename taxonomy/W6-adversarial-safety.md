# W6 — Adversarial safety / robustness

**Pillar:** I — WHAT is evaluated (Target Capabilities)

**Construct.** Whether an agent maintains aligned, safe behaviour under adversarial pressure: prompt injection via tool returns or web content, jailbreaks, goal hijacking, harmful shortcuts. The metric is often a *refusal* or the *absence* of an unsafe side-effect, inverting usual success semantics.

**Measurement difficulty.** The open-ended attack surface — a benchmark fixes a finite attack set, but robustness is a claim over an adversary's entire strategy space. Reported safety rates are upper bounds against a specific threat model and should be reported as such.

**Roadmap priority.** Programmatic safety oracles — deterministic verifiers of unsafe side-effects / policy violations (Direction 5).

**Benchmarks tagged W6:** τ-bench (policy/rule adherence).
