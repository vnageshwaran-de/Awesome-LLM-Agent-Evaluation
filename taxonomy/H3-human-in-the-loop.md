# H3 — Human-in-the-loop evaluation

**Pillar:** II — HOW it is measured (Evaluation Paradigms)

**Mechanism.** Annotators score trajectories, adjudicate completion, or interact with the agent directly.

**Strength.** Reference standard for constructs that resist formalization (genuine helpfulness, nuanced safety judgment) and the ultimate validator of H1's checkers and H2's judges.

**Limitation.** Cost, latency, and reliability variance — does not scale to the thousands of multi-turn runs statistical power requires; inter-annotator disagreement must be quantified (e.g., Cohen's κ) and controlled.

**Best deployment.** Not the primary scorer at scale but the *calibration anchor* that licenses H1 and H2.
