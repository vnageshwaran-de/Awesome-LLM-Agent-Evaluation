# W1 — Long-horizon planning

**Pillar:** I — WHAT is evaluated (Target Capabilities)

**Construct.** Decomposing a high-level goal into an ordered sequence of subgoals and executing them across a horizon long enough that local greedy action is insufficient. The defining property is *credit assignment over depth*: success at step *T* may depend on a commitment made at step *t ≪ T*.

**Measurement requirement.** An irreducible dependency chain (no shallow shortcut) and depth-stratified success reporting.

**Dominant failure mode.** *Horizon collapse* — tasks advertised as long-horizon that are in practice solvable by a single competent action, inflating apparent planning ability.

**Benchmarks tagged W1:** SWE-bench, WebArena, AgentBench, OSWorld, Mind2Web (see [`/data/benchmarks.csv`](../data/benchmarks.csv)).
