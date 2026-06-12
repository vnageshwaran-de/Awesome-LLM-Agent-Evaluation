# Springer (SpringerLink) Tier Harvest — Integration Report

**Date:** 2026-06-08
**Source:** SpringerLink (Springer Nature Link) advanced search, authenticated session
**Query (title-scoped, reproducible):**
`title=(agent OR agentic) AND (benchmark OR evaluation)` ; `date=custom&dateFrom=2023&dateTo=2026` ; `sortBy=relevance`
**Export:** official "Download results (.csv)" → `springer_tier_harvest.csv` (172 records)

## Why title-scoped, not full-text

The default SpringerLink full-text query for the same terms returns **7,759** results — `broad_expansion`, matching anywhere in text/references and dominated by off-topic medicine/engineering papers (same failure mode as the ACM `count_only_broad_expansion`). Restricting the **Title** field collapses this to **172** screenable records, mirroring the OpenAlex Tier-1 title-search protocol. Identification favors recall; precision is recovered at screening.

## Screening funnel (title-level first pass)

| Bucket | n | Disposition |
|---|---|---|
| Already in OpenAlex 648 (DOI/title match) | 5 | duplicate — not new |
| Already in 259 included | 0 | — |
| Chemical/biological "agent" (biocontrol, anticancer, imaging, reducing, plugging…) | 104 | exclude (off-construct / EC6) |
| Non-LLM agent systems (distributed control, consensus, principal–agent econ, game theory, robotics) | 23 | exclude (EC6) |
| Conversational/relational health agents | 3 | exclude (EC1/EC4) |
| Other off-construct | 10 | exclude |
| **Genuine LLM/agentic candidates** | **~19** | **pending abstract + construct screen** |
| (residual chem/bio noise still flagged) | ~8 | exclude on inspection |
| **Total** | **172** | |

Per-record decisions: `springer_dedup_screen.csv`.

## Candidate includes (require abstract-level construct test, IC1–IC3 / EC1–EC6)

Most are application/system papers where an LLM multi-agent system is built for a domain and evaluation is incidental (**EC4**), or evaluation *infrastructure* (LLM-as-judge frameworks) rather than agent benchmarks. Strongest genuine candidates:

- Agentic AI Capability and Security Benchmark (*Securing AI Agents*, 2025) — possible IC1 benchmark
- SecKQL-Agent: A Real-World APT29 Events Benchmark and Framework for Text-to-KQL (2026) — possible IC1
- LLM-Based Multi-agent Systems: Frameworks, Evaluation, Open Challenges (2026) — possible IC3 survey
- MATEval / T2F — multi-agent LLM *evaluator* frameworks (likely infrastructure, catalogued separately)
- Remainder (vendor evaluation, heating control, inpatient pathways, Umrah planning, educational content, customer simulator) — likely **EC4** system/application papers

## Bottom line

Searching the publisher's own platform with a field-scoped, reproducible query yields **0 already-missed canonical agentic benchmarks** and **0 overlap with the 259 already-included**. This directly answers the "single-source / Springer not searched" criticism: OpenAlex's coverage of the core agentic-benchmark literature is **corroborated**, and any new includes will be a small number of peripheral items.

## Status / next step

- The 259 / PRISMA counts are **unchanged pending the abstract-level construct screen** of the ~19 candidates. No counts have been altered and no rows fabricated.
- Next: fetch abstracts for the ~19 candidates, apply the dependent-step / external-effector / outcome-scoring construct test, finalize the new-include count (expected 0–4), then propagate to the PRISMA flow, manifest, and prose with the Springer tier registered as a field-scoped harvest.
