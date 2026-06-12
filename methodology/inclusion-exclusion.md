# Inclusion & Exclusion Criteria

## Operational definition
A paper is an **autonomous agentic evaluation paper** iff it proposes, formalizes, or critically analyzes a procedure for measuring an *LLM-driven agent* — a system in which a language model is the policy that, conditioned on observations, selects **sequential actions that alter an external state** over ≥ 2 dependent steps. The artifact must exhibit all three:

1. **Sequential decision-making** — emits a trajectory τ = (o₀, a₀, …, o_T) where aₜ depends on history and changes oₜ₊₁. A single prompt→answer pass does not qualify.
2. **Exteriority of action** — at least one action invokes an external effector (tool, API, interpreter, browser, OS, simulator, or another agent). Chain-of-thought alone does not qualify.
3. **Outcome- or process-grounded scoring** — success measured against external state or trajectory quality, not textual similarity to a fixed reference alone.

**Boundary cases.** Retrieval-augmented QA is included only if retrieval is interleaved with reasoning across multiple dependent steps. One-shot function-call-syntax scoring is excluded (component, not execution).

## Inclusion (all required)
- **IC1** Primary object is an LLM-driven agent per the definition above.
- **IC2** Specifies a measurable scoring procedure and ≥ 1 quantitative metric.
- **IC3** Primary research artifact, or a secondary study materially advancing taxonomy/critique.
- **IC4** English; full text available (peer-reviewed, archival preprint, or released technical report with artifact).
- **IC5** Within 2022–2025.

## Exclusion (any triggers)
- **EC1** Static NLP evaluation only (single-turn understanding/generation, no state-changing action).
- **EC2** Prompt engineering without agentic measurement.
- **EC3** Capability-component micro-benchmarks (isolated sub-skill, not composed into multi-step grounded tasks). → supplementary register.
- **EC4** Model-/training-centric papers where evaluation is incidental. → cited as systems under test.
- **EC5** Non-archival ephemera; duplicates; superseded preprint versions.
- **EC6** Out of scope: non-LLM embodied control; pre-LLM-agent RL benchmarks.

## Screening reliability
Two independent analysts; inter-rater agreement via Cohen's κ; third-analyst adjudication. A 10% calibration round precedes full screening to align application of EC1–EC3 (the static-vs-agentic boundary).
