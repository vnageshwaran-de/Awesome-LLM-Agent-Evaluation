# Awesome-LLM-Agent-Evaluation [![Awesome](https://awesome.re/badge.svg)](https://awesome.re)

> The living, community-curated companion to the survey
> **_Large Language Model Agent Evaluation and Benchmarking: A Systematic Survey, Meta-Taxonomy, and Critical Research Roadmap_** (under review, Springer Nature *Artificial Intelligence Review*).

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20692460.svg)](https://doi.org/10.5281/zenodo.20692460)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![Maintenance](https://img.shields.io/badge/Maintained-yes-green.svg)](https://github.com/)

> **Archived release:** v1.0 is permanently archived on Zenodo — DOI [10.5281/zenodo.20692460](https://doi.org/10.5281/zenodo.20692460).

This repository is the open-source, continuously-updated extension of our systematic survey. The paper fixes a snapshot of the field; this repository tracks it as it moves. Every benchmark catalogued here is classified under the same three-pillar **meta-taxonomy** developed in the paper, and the canonical dataset — [`/data/benchmarks.csv`](data/benchmarks.csv) — is the single source of truth that backs both the paper's landscape matrix and this README.

We enforce one rule above all others: **accurate venue labeling**. A benchmark is listed with its *verified* publication status (peer-reviewed proceedings, journal, or honestly-labeled preprint). We never upgrade a preprint to a venue we cannot confirm.

---

## Contents

- [Why this repository](#why-this-repository)
- [The Meta-Taxonomy](#the-meta-taxonomy)
  - [Pillar I — WHAT is evaluated (Target Capabilities)](#pillar-i--what-is-evaluated-target-capabilities)
  - [Pillar II — HOW it is measured (Evaluation Paradigms)](#pillar-ii--how-it-is-measured-evaluation-paradigms)
  - [Pillar III — WHERE it is tested (Environment Topologies)](#pillar-iii--where-it-is-tested-environment-topologies)
- [The Landscape Matrix](#the-landscape-matrix)
- [Repository Structure](#repository-structure)
- [Citation](#citation)
- [Contributing](#contributing)
- [License](#license)

---

## Why this repository

Surveys of agent evaluation date quickly: new benchmarks appear weekly, and a static PDF cannot keep pace. This repository solves three problems at once:

1. **Reproducibility.** The full PRISMA search strings, inclusion/exclusion criteria, and screening decisions from the paper are released here, so the candidate corpus can be reconstructed independently.
2. **Machine-readability.** The landscape matrix lives as a structured CSV, not a frozen table, so it can be filtered, queried, and ingested programmatically.
3. **Community extension.** New benchmarks enter through a structured pull-request workflow with a metadata schema and a verification checklist, keeping the taxonomy consistent as it grows.

---

## The Meta-Taxonomy

Every entry is classified as a region `⟨W, H, E⟩` across three analytically separable pillars. The codes below are used verbatim in [`/data/benchmarks.csv`](data/benchmarks.csv).

### Pillar I — WHAT is evaluated (Target Capabilities)

| Code | Capability | What it measures |
|------|-----------|------------------|
| [`W1`](taxonomy/W1-long-horizon-planning.md) | Long-horizon planning | Goal decomposition and credit assignment over deep, dependent action chains |
| [`W2`](taxonomy/W2-multi-turn-reasoning.md) | Multi-turn reasoning | Maintenance and revision of a belief state across interactive turns |
| [`W3`](taxonomy/W3-tool-api-execution.md) | Tool / API execution | Tool selection, argument grounding, result interpretation, and recovery |
| [`W4`](taxonomy/W4-environment-perception.md) | Environment perception | Building an accurate state model from partial/noisy observations |
| [`W5`](taxonomy/W5-multi-agent-coordination.md) | Multi-agent coordination | Cooperation, negotiation, and robustness to non-cooperative peers |
| [`W6`](taxonomy/W6-adversarial-safety.md) | Adversarial safety / robustness | Behavior under prompt injection, jailbreaks, and goal hijacking |

### Pillar II — HOW it is measured (Evaluation Paradigms)

| Code | Paradigm | Strength / principal failure mode |
|------|----------|-----------------------------------|
| [`H1`](taxonomy/H1-programmatic.md) | Programmatic / deterministic | Reproducible and faithful / blind to unanticipated valid solutions |
| [`H2`](taxonomy/H2-llm-as-judge.md) | LLM-as-a-Judge (incl. multi-agent) | Scales to open-ended tasks / positional, verbosity & self-preference bias |
| [`H3`](taxonomy/H3-human-in-the-loop.md) | Human-in-the-loop | Reference standard / costly, slow, inter-annotator variance |

### Pillar III — WHERE it is tested (Environment Topologies)

| Code | Topology | Trade-off |
|------|----------|-----------|
| [`E1`](taxonomy/E1-static-datasets.md) | Static datasets | Reproducible & cheap / cannot test state-changing interaction; high contamination exposure |
| [`E2a`](taxonomy/E2a-virtual-os.md) | Virtual operating systems | High-fidelity programmatic scoring / costly, fragile setup |
| [`E2b`](taxonomy/E2b-web-containers.md) | Web / browser containers | Realistic / live-vs-frozen reproducibility tension |
| [`E2c`](taxonomy/E2c-code-execution.md) | Code execution environments | Objective test oracle / partial coverage, contamination risk |
| [`E2d`](taxonomy/E2d-multi-agent-game.md) | Multi-agent / game worlds | Clean experimental control / reduced ecological validity |

---

## The Landscape Matrix

A human-readable view of [`/data/benchmarks.csv`](data/benchmarks.csv). **Venues are verified; preprints are labeled as such.** Seventeen benchmarks, ordered by environment topology (E1 → E2d). Two further entries — **BrowserGym** (a harness, not a benchmark) and **SWE-bench Verified** (a curated, non-archival subset) — are tracked in the CSV and discussed in the paper's search-sensitivity analysis as artifacts that abstract-level search does not retrieve.

| Benchmark | Capabilities | Paradigm | Environment | Core Metrics | Venue (verified) |
|-----------|--------------|----------|-------------|--------------|------------------|
| [Mind2Web](https://arxiv.org/abs/2306.06070) | W4, W1, W2 | H1 | E1 | Element acc.; Op. F1; Step SR | **NeurIPS 2023 (D&B, Spotlight)** |
| [GAIA](https://arxiv.org/abs/2311.12983) | W2, W3, W4 | H1 | E1+E2b | Accuracy by level (L1–L3) | **ICLR 2024** |
| [WebShop](https://arxiv.org/abs/2207.01206) | W1, W2, W4 | H1 | E2b | Task score; success rate | **NeurIPS 2022** |
| [WebArena](https://arxiv.org/abs/2307.13854) | W4, W1, W3 | H1 | E2b | Task success rate | **ICLR 2024** |
| [VisualWebArena](https://arxiv.org/abs/2401.13649) | W4, W1, W2, W3 | H1 (+H2) | E2b | Task success rate | **ACL 2024** |
| [AssistantBench](https://arxiv.org/abs/2407.15711) | W1, W2, W3, W4 | H1 | E2b | Accuracy; precision | **EMNLP 2024** |
| [WorkArena](https://arxiv.org/abs/2403.07718) | W1, W2, W3, W4 | H1 | E2b | Task success rate | **ICML 2024** |
| [OSWorld](https://arxiv.org/abs/2404.07972) | W4, W1, W3 | H1 | E2a | Execution-based success | **NeurIPS 2024 (D&B)** |
| [AgentBench](https://arxiv.org/abs/2308.03688) | W1, W3, W2 | H1 | E2a/E2c/E2d | Per-env & overall success | **ICLR 2024** |
| [AgentBoard](https://arxiv.org/abs/2401.13178) | W1, W2, W3, W4 | H1 | E2b/E2d | Success rate; progress rate | **NeurIPS 2024 (D&B, Oral)** |
| [SWE-bench](https://arxiv.org/abs/2310.06770) | W3, W1, W2 | H1 | E2c | % Resolved; Fail-to-Pass | **ICLR 2024 (Oral)** |
| [AppWorld](https://arxiv.org/abs/2407.18901) | W1, W3, W2, W6 | H1 | E2c | Task goal completion | **ACL 2024 (Best Resource)** |
| [ToolBench / ToolLLM](https://arxiv.org/abs/2307.16789) | W3, W1, W2 | H2 (+H1) | E2c | Pass rate; win rate | **ICLR 2024 (Spotlight)** |
| [τ-bench](https://arxiv.org/abs/2406.12045) | W2, W3, W1, W6 | H1 (+H2 user sim) | E2c | pass@1; pass^k | **ICLR 2025** |
| [ScienceWorld](https://arxiv.org/abs/2203.07540) | W1, W2, W4 | H1 | E2d | Task score (0–1) | **EMNLP 2022** |
| [AgentVerse](https://arxiv.org/abs/2308.10848) | W5, W1, W3, W2 | H1 (+H2) | E2d | Task-specific success | **ICLR 2024** |
| [Cybench](https://arxiv.org/abs/2408.08926) | W6, W1, W3, W4 | H1 | E2c/E2a | Flag-capture SR; subtask SR | **ICLR 2025 (Oral)** |

> ⚠️ **Verification note.** Venues were confirmed against the official ICLR/NeurIPS/ICML/ACL/EMNLP proceedings (not arXiv comment fields alone), 4 June 2026. τ-bench is now **ICLR 2025** (previously an unverified preprint). If you have evidence that changes any `venue`/`venue_status`, please open a PR with a citable link.

---

## Repository Structure

**Headline numbers (PRISMA-ScR, 2023–2026).** 648 records identified (OpenAlex,
6 title streams) → 205 duplicates removed → 443 screened → 243 excluded → 200
assessed → +59 snowball → **259 studies included**; reconciliation check **PASS**
(`648−205=443`, `200+59=259`). A hand-verified subset of **17** benchmarks forms
the in-depth landscape matrix. **Recall (RQ7, _estimate_):** OpenAlex probe recall
**10/10** (probe gap 0.0) on canonical benchmarks; Chapman capture–recapture
implies ≈0.077 as a *loose lower bound* on long-tail recall (contradicted,
reassuringly, by the probe proxy). **Tier-2/3 count-only verified (2026-06-08): ScienceDirect 785, IEEE 962, ACM 17,231
(broad), Scopus 4,836 — each probed for the 10 canonical benchmarks. ScienceDirect/IEEE/
ACM host citing works only (0/10); Scopus hosts the benchmark papers themselves (9/10),
overlapping OpenAlex 9/9 (Scopus-only=0) — a decisive independent corroboration that
canonical recall is effectively complete.** WoS/SpringerLink/Semantic Scholar remain `UNRESOLVED`.

```
Awesome-LLM-Agent-Evaluation/
├── README.md                  # This file
├── CONTRIBUTING.md            # Full contribution guide (mirrors the section below)
├── CITATION.cff               # Machine-readable citation metadata
├── pipeline/
│   └── build_review.py        # ⭐ Executable PRISMA-ScR pipeline (harvest→dedup→screen→snowball→recall_gap→taxonomy)
├── data/
│   ├── benchmarks.csv         # ⭐ Canonical, hand-verified 17-benchmark landscape matrix
│   ├── benchmark_taxonomy.json# 259-study heuristic-classified evidence map
│   ├── capability_coverage_trends.csv  # capability shares by year
│   ├── recall_gap_table.csv   # recall-gap summary
│   └── final_studies.bib      # BibTeX for the included studies
├── taxonomy/                  # One reference page per taxonomy code (W*, H*, E*)
└── methodology/
    ├── prisma-search-strings.md  # OpenAlex/Crossref streams + IEEE/ACM (UNRESOLVED) queries
    ├── inclusion-exclusion.md    # IC1–IC5 / EC1–EC6 screening criteria
    ├── search_log.json           # Per-stream queries, counts, timestamps, tier, status
    ├── prisma_manifest.json      # Reconciled PRISMA-ScR counts (check: PASS)
    ├── recall_gap_estimate.json  # Probe proxy + Chapman capture–recapture + caveats
    ├── recall_probe_matrix.csv   # (benchmark × source) capture vectors
    ├── screening_decisions.csv   # Per-record include/exclude + EC code + rationale
    ├── deduplication_log.csv     # Per-record dedup decisions
    ├── snowball_log.csv          # Backward/forward additions with parent
    ├── retrieval_manifest.csv    # Canonical record set
    ├── venue_upgrade_log.csv     # Archival-vs-preprint venue status
    ├── doi_resolution_check.csv  # Live DOI-resolution spot check
    ├── seed_registry.json        # 16 seed benchmarks + probe-set membership
    ├── unresolved_items.csv      # All UNRESOLVED sources/seeds/estimates
    └── validation_report.md      # Final validation summary
```

---

## Citation

If this repository or the survey informs your work, please cite the paper. The paper is currently under review; volume, pages, and DOI will be added on acceptance. To cite the repository itself, use the archived release DOI [10.5281/zenodo.20692460](https://doi.org/10.5281/zenodo.20692460).

```bibtex
@article{nageshwaran2026llmagenteval,
  title   = {Large Language Model Agent Evaluation and Benchmarking:
             A Systematic Survey, Meta-Taxonomy, and Critical Research Roadmap},
  author  = {Nageshwaran, Vinoth and Ezekiel, Soundararajan and Tran, Tin T. and Narasimhan, V. Lakshmi},
  journal = {Artificial Intelligence Review},
  year    = {2026},
  note    = {Under review. Companion repository:
             https://github.com/vnageshwaran-de/Awesome-LLM-Agent-Evaluation}
}
```

> Per the repository's no-fabrication policy, `volume`, `number`, `pages`, and `doi` are intentionally omitted until the journal assigns them. Maintainers will add them on acceptance.

---

## Contributing

We welcome new benchmarks, corrections to venue labels, and taxonomy refinements. Contributions are accepted through pull requests that follow the workflow below. The goal is a catalogue that stays **consistent** (every entry classified under the same taxonomy) and **trustworthy** (every venue verified).

### Contribution workflow

1. **Open an issue first** for any non-trivial addition, using the `New Benchmark` issue template. This lets maintainers flag duplicates or scope concerns before you invest effort.
2. **Fork** the repository and create a branch named `add/<benchmark-name>` or `fix/<short-description>`.
3. **Add one row** to [`/data/benchmarks.csv`](data/benchmarks.csv) — the CSV is the source of truth; the README tables are regenerated from it. Do **not** hand-edit only the README.
4. **Run the validator** (`scripts/validate.py`, if present) to check schema conformance and that taxonomy codes are valid.
5. **Open a PR** using the pull-request template and complete the checklist below.
6. A maintainer reviews for benchmark eligibility, schema correctness, and — critically — **venue verification**.

### Benchmark eligibility criteria

A submission must describe an **autonomous agentic evaluation**, meaning the benchmark measures an LLM-driven agent that:

- [ ] emits a **multi-step trajectory** (≥ 2 dependent steps), not a single prompt→answer pass;
- [ ] invokes at least one **external effector** (tool, API, code interpreter, browser, OS, simulator, or another agent);
- [ ] is scored against an **environment state or trajectory quality**, not textual similarity to a fixed reference alone.

Single-turn QA, prompt-engineering techniques, and one-shot function-call-syntax micro-benchmarks are **out of scope** (they map to exclusion criteria EC1–EC3 in [`methodology/inclusion-exclusion.md`](methodology/inclusion-exclusion.md)).

### Required metadata fields

Every row in `benchmarks.csv` must populate **all** of the following columns:

| Field | Description | Example |
|-------|-------------|---------|
| `benchmark_name` | Canonical name | `SWE-bench` |
| `target_capabilities` | One or more `W1–W6` codes with short gloss | `Tool/code execution (W3); Planning (W1)` |
| `evaluation_paradigm` | One or more `H1–H3` codes | `Programmatic/deterministic (H1)` |
| `environment_type` | One or more `E1/E2a–E2d` codes | `Code execution environment (E2c)` |
| `core_metrics` | Primary reported metrics | `% Resolved; Fail-to-Pass` |
| `key_limitations` | Honest, specific limitations | `Python-only; contamination risk` |
| `venue` | Publication venue **as verified** | `ICLR 2024 (Oral)` |
| `venue_status` | `peer-reviewed`, `workshop`, or `preprint-unverified` | `peer-reviewed` |
| `year` | Year of the cited version | `2024` |
| `arxiv_id` | arXiv identifier if applicable, else empty | `2310.06770` |

### Submission checklist (paste into your PR)

```markdown
## Benchmark submission checklist
- [ ] The benchmark meets all three eligibility criteria (multi-step, external effector, state-grounded scoring).
- [ ] I added exactly one row to /data/benchmarks.csv (not just the README).
- [ ] All required metadata fields are populated.
- [ ] Taxonomy codes (W*/H*/E*) are valid and defined in /taxonomy.
- [ ] The `venue` is VERIFIED against the official proceedings or the arXiv record, and a link is provided in the PR description.
- [ ] If no peer-reviewed venue is confirmed, `venue_status` is set to `preprint-unverified` (I did NOT upgrade it).
- [ ] `key_limitations` is specific and honest (no marketing language).
- [ ] No fabricated DOI, venue, year, or author.
```

### Review standards

Maintainers will reject or request changes for: unverifiable venue claims, scope violations (static NLP / prompt-engineering work), incomplete metadata, or limitations sections that read as promotion rather than critique. Venue upgrades from preprint to proceedings require a citable link to the proceedings entry.

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the full guide.

---

## License

Content (text, taxonomy, CSV) is released under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Cite the survey and link back to this repository when reusing.
