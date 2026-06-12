# E1 — Static datasets

**Pillar:** III — WHERE it is tested (Environment Topologies)

**Definition.** A fixed corpus of tasks whose inputs do not change in response to agent action — QA sets, fixed code-generation problems, frozen tool-use traces.

**Strength.** Reproducibility, low cost, comparability.

**Limitation.** Cannot, by construction, evaluate state-changing interaction; most exposed to data contamination (a fixed, published set is precisely what leaks into pre-training). Agentic claims grounded solely in E1 warrant caution.

**Benchmarks:** Mind2Web (cached real-site snapshots); GAIA (static question set, hybrid with open-web solving).
