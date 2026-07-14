# Repeated-Run Trilemma Pilot — Protocol (AIR revision, R2 major comment 2)

## Objective
Provide direct empirical evidence for the non-determinism and cost axes of the
trilemma by re-running 2–3 verified-matrix benchmarks at ≥5 seeds and reporting
mean, variance, 95% CIs, seed-induced rank churn, and the complete standardized
run-cost record (Table `tab:cost_template` of the revised manuscript). This is
the study Section 6.3 of the submitted manuscript describes as "concrete,
low-cost"; the revision executes it as a pilot.

## Design (minimum viable, cost-scoped)
- **Benchmarks (recommended):**
  1. **τ-bench (retail subset)** — E2c, has pass^k as a comparison anchor; the
     LLM user-simulator makes it the highest-variance design in the matrix.
  2. **Mind2Web (test split subset)** — E1 static; deterministic scoring
     isolates *model*-side stochasticity from environment drift (cheap floor).
  3. *(optional third)* **SWE-bench Lite (subset of 50 instances)** — E2c
     Docker; captures environment-hours cost dimension.
- **Task subset:** fixed random subset per benchmark (seed 42): 50–100 tasks.
  Released as task ID lists in this directory.
- **Models:** 1–2 (one strong, one mid-tier is ideal; a single model is
  acceptable for the pilot framing).
- **Seeds:** 5 independent runs per benchmark × model (temperature and all
  decoding parameters held fixed and reported; only the seed varies — if the
  API exposes no seed, the 5 runs are i.i.d. samples of the same config,
  which is the deployment-relevant quantity).
- **Record per run:** per-task binary outcome, tokens in/out, wall-clock,
  environment-hours, dated pricing → `runs/<bench>_<model>_seed<k>.json`.

## Analysis (analyze_pilot.py, deterministic)
1. Per benchmark×model: mean pass rate across seeds, SD, min–max spread,
   Wilson 95% CI per seed and t-based CI of the across-seed mean.
2. pass^k for k=1..5 (τ-bench definition) where per-task repetition applies.
3. **Single-run deviation estimate:** distribution of |single-seed rate −
   5-seed mean| — the quantity Section 6.3 says the field lacks.
4. **Rank churn** (if ≥2 models): fraction of seed pairs that reverse the
   model ranking; McNemar on pooled per-task outcomes.
5. Empirical variance → benchmark-specific seed counts for 80% power at
   d = 1.0 / 0.5 / 0.3 (feeds the revised Direction 3 sensitivity table).
6. Full standardized cost record per Table `tab:cost_template`, including
   the pilot's own total cost (reported in the paper as a datum).

## Reporting in the manuscript
- New subsection 5.5 "A Repeated-Run Pilot" (or appendix): one results table
  + 2–3 sentences per finding; explicitly framed as a pilot demonstrating
  the Direction 3/4 reporting standard, not a leaderboard.
- Response letter: answers R2 major 2 and grounds R3 major 4 empirically.

## What Claude has prepared vs. what needs the authors
- Prepared: this protocol, analysis script, task-subset sampler, cost-record
  schema.
- Needs authors: API keys + execution (est. cost: τ-bench subset ×5 seeds
  ≈ low tens of dollars per model; Mind2Web subset negligible; SWE-bench Lite
  subset the largest, mostly environment-hours).
