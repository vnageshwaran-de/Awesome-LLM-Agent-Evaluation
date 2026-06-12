# Contributing to Awesome-LLM-Agent-Evaluation

Thank you for helping keep this catalogue current and trustworthy. Two principles govern every contribution: **consistency** (every entry classified under the same `⟨W, H, E⟩` meta-taxonomy) and **trustworthiness** (every venue verified, every preprint honestly labeled).

## Workflow
1. **Open an issue first** using the `New Benchmark` template, so maintainers can flag duplicates or scope concerns.
2. **Fork** and branch as `add/<benchmark-name>` or `fix/<short-description>`.
3. **Add exactly one row** to [`/data/benchmarks.csv`](data/benchmarks.csv) — the CSV is the source of truth; README tables are regenerated from it.
4. **Validate** schema conformance and taxonomy-code validity (`scripts/validate.py`, when present).
5. **Open a PR** with the checklist below completed.
6. A maintainer reviews for eligibility, schema correctness, and **venue verification**.

## Eligibility (all three required)
- [ ] Multi-step trajectory (≥ 2 dependent steps), not a single prompt→answer pass.
- [ ] Invokes ≥ 1 external effector (tool, API, interpreter, browser, OS, simulator, or another agent).
- [ ] Scored against environment state or trajectory quality, not textual similarity to a fixed reference alone.

Out of scope: single-turn QA, prompt-engineering techniques, one-shot function-call-syntax micro-benchmarks (EC1–EC3 in [`methodology/inclusion-exclusion.md`](methodology/inclusion-exclusion.md)).

## Required metadata (every CSV column)
`benchmark_name`, `target_capabilities` (W*), `evaluation_paradigm` (H*), `environment_type` (E*), `core_metrics`, `key_limitations`, `venue` (verified), `venue_status` (`peer-reviewed` | `workshop` | `preprint-unverified`), `year`, `arxiv_id`.

## PR checklist (paste into your PR)
```markdown
## Benchmark submission checklist
- [ ] Meets all three eligibility criteria.
- [ ] Added exactly one row to /data/benchmarks.csv.
- [ ] All required metadata fields populated.
- [ ] Taxonomy codes (W*/H*/E*) valid and defined in /taxonomy.
- [ ] Venue VERIFIED against official proceedings or arXiv; link in PR description.
- [ ] If no peer-reviewed venue is confirmed, venue_status = preprint-unverified (NOT upgraded).
- [ ] key_limitations specific and honest (no marketing language).
- [ ] No fabricated DOI, venue, year, or author.
```

## Review standards
We request changes for: unverifiable venue claims, scope violations, incomplete metadata, or promotional limitations sections. Preprint→proceedings upgrades require a citable link.
