# H1 — Programmatic / deterministic scoring

**Pillar:** II — HOW it is measured (Evaluation Paradigms)

**Mechanism.** Score derived from a deterministic function of the environment's state: unit tests, goal-state assertions, exact-match on a side-effect, simulator reward.

**Strength.** Construct fidelity at low marginal cost and high reproducibility — the same trajectory yields the same score every run.

**Limitation.** *Coverage* — a deterministic checker recognizes only the success conditions its authors anticipated; it under-credits unforeseen valid paths (the false-negative face of trajectory drift) and cannot score open-ended tasks lacking a machine-checkable goal predicate.

**Best fit.** Code-execution (E2c) and virtual-OS (E2a) topologies. **Benchmarks:** the large majority of the catalogue (primary scorer in all seventeen; appears as a goal-state component alongside H2 in τ-bench, ToolBench, and AgentVerse).
