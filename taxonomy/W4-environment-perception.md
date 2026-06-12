# W4 — Environment perception

**Pillar:** I — WHAT is evaluated (Target Capabilities)

**Construct.** Constructing an accurate internal model of the surroundings from partial, noisy, or high-dimensional observations — a DOM tree, screenshot, filesystem listing, accessibility tree, or rendered text. The *observation* half of the perception–action loop.

**Measurement requirement.** Hold the task fixed while varying observation modality to isolate the capability.

**Dominant failure mode.** *Observation-format brittleness* — performance that varies sharply with the encoding of the same underlying state (HTML vs accessibility tree vs pixels).

**Benchmarks tagged W4:** WebArena, GAIA, OSWorld, Mind2Web.
