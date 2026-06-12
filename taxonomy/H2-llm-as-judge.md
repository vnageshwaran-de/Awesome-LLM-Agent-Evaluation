# H2 — LLM-as-a-Judge (incl. multi-agent)

**Pillar:** II — HOW it is measured (Evaluation Paradigms)

**Mechanism.** A language model scores a trajectory or output against a rubric or by pairwise comparison; multi-agent variants use panels, debate, or judge–critic decomposition.

**Strength.** Coverage of the unspecifiable — open-ended quality judgments where no deterministic predicate exists; scales far more cheaply than human evaluation.

**Structural costs.** Positional and verbosity bias, self-preference, sensitivity to rubric phrasing, and non-determinism of the judge itself. The central validity question: does the judge measure the construct, or agreement with its own priors?

**Requirement.** Any benchmark relying on H2 must report judge–human agreement to be interpretable.

**Benchmarks with an H2 component:** τ-bench (LLM-simulated user).
