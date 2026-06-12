# W3 — Tool / API execution

**Pillar:** I — WHAT is evaluated (Target Capabilities)

**Construct.** Selecting the correct tool, populating its arguments, interpreting its (possibly erroneous) return, and chaining tools toward a goal. Decomposes into *selection*, *grounding*, *interpretation*, and *recovery*.

**Measurement requirement.** Multi-tool composition with feedback-dependent control flow.

**Dominant failure mode.** Scoring only schema-valid emission of a single call (one-shot function-calling accuracy), which measures grounding in isolation — a capability component, not agentic execution (exclusion EC3).

**Benchmarks tagged W3:** SWE-bench, WebArena, GAIA, AgentBench, OSWorld, τ-bench.
