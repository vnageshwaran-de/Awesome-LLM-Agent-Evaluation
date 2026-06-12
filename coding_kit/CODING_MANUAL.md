# Taxonomy Dual-Coding Manual

Purpose: produce human-verified taxonomy labels and inter-coder reliability
(Cohen's κ per attribute) for the included benchmark studies. The machine labels
in `data/benchmark_taxonomy.json` are `keyword_heuristic` and are **not** ground
truth; this protocol replaces them with verified labels on a stratified sample.

## Protocol

1. Two raters code **independently and blind** — do not look at the machine
   labels or each other's sheets until both are complete.
2. Each rater fills their own sheet (`rater_A_sheet.csv` / `rater_B_sheet.csv`).
   Every attribute cell takes `1` (present), `0` (absent). No blanks.
3. Code from the paper's title + abstract first; open the DOI/URL when the
   abstract is insufficient. Cap effort at ~5 minutes per paper.
4. When both sheets are complete, run:
   `python3 compute_kappa.py rater_A_sheet.csv rater_B_sheet.csv`
   This writes `taxonomy_reliability.csv` (per-attribute κ, percent agreement,
   Landis–Koch interpretation) and prints a summary.
5. Disagreements (cells where A≠B) are resolved by discussion; record the
   consensus label in a copy named `consensus_sheet.csv`. Report κ from the
   pre-consensus sheets — never from post-consensus data.

## Attribute definitions and decision rules

Code `1` only when the benchmark **evaluates** the capability — not when the
paper merely mentions it.

### Agent capabilities
- **Planning** — tasks require multi-step plans or goal decomposition that the
  agent must produce or follow (rule: scoring depends on plan quality or success
  of a multi-step procedure).
- **Reasoning** — tasks require inference beyond retrieval (logical, causal,
  mathematical). Do not code `1` for the word "reasoning" alone.
- **ToolUse** — agent must invoke external tools/APIs/function calls and the
  benchmark scores tool selection or invocation.
- **Coding** — tasks are programming tasks (writing, fixing, reviewing code;
  repo-level issues count).
- **Memory** — tasks test retention/recall across turns or episodes beyond a
  single context window, or scored use of an explicit memory store.
- **Collaboration** — two or more agents (or agent+human) must coordinate, and
  coordination quality affects the score.
- **ScientificDiscovery** — tasks are research workflows: hypothesis generation,
  experiment design/execution, data analysis, ML engineering.
- **Recommendation** — tasks are recommender-system tasks (ranking items for
  users) executed or evaluated agentically.
- **LongHorizonExecution** — episodes are long (≳10 dependent steps or
  hours-scale workflows) and the benchmark stresses sustained execution.
- **WebInteraction** — agent operates a browser/web UI (navigation, clicking,
  form-filling) or consumes live web content as the task substrate.

### Environment (code all that apply)
- **Static** — fixed dataset; no state changes from agent actions.
- **Interactive** — environment state responds to agent actions.
- **Dynamic** — environment changes independently of the agent (time, other
  actors, stochastic events).
- **Simulated** — sandboxed replica (emulated OS, mock APIs, virtual shop).
- **RealWorld** — real systems/sites/data with real-world consequences or live
  endpoints.
- **Embodied** — physical or simulated-physical body (robotics, navigation in
  3D space).

### Evaluation paradigm
- **Offline** — scoring against pre-collected data/trajectories.
- **Online** — scoring during live interaction with the environment.
- **HumanInTheLoop** — humans judge outputs or participate in episodes.
- **MultiAgent** — evaluation setting contains multiple interacting agents.
- **FullyAutonomous** — no human intervention permitted during an episode.

### Reproducibility (code from paper + repository)
- **OpenSource** — benchmark code is publicly released (link resolves).
- **DatasetReleased** — task data/instances downloadable.
- **EnvironmentReleased** — executable environment (not just data) released.
- **DockerSupport** — containerized setup provided.
- **EvalScriptsAvailable** — official scoring/harness scripts released.

## Edge rules
- If the abstract is missing and the DOI does not resolve, code the row's
  `uncodable` column as `1` and leave attributes `0`; `compute_kappa.py`
  excludes rows either rater marks uncodable.
- Survey/position papers that slipped through screening: mark `uncodable=1` and
  note `"not a benchmark"` in the notes column (this doubles as a screening
  audit).

## Sample design
`rater sheets` contain a stratified random sample (n=50, proportional by
publication year, fixed seed 42) of the 259 included studies — large enough for
stable κ on prevalent attributes while keeping rater workload ≈4 hours each.
