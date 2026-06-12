# Multi-Source Title-Scoped Harvest — Status (2026-06-08)

Full screened harvest of the credential-gated / previously-broad-expansion sources, using the **same title-scoped protocol** as the OpenAlex Tier-1 (broad title query → dedup → screen). Authenticated browser sessions; official CSV export where available. **No counts fabricated; the 259/PRISMA totals are unchanged pending abstract-level construct screening.**

## Reproducible queries

- **SpringerLink** (advanced search, Title field): `title=(agent OR agentic) AND (benchmark OR evaluation)`, 2023–2026. Full-text default returns 7,759 (broad-expansion); title-scoped = **172**.
- **IEEE Xplore**: `("Document Title":agent OR "Document Title":agentic) AND ("Document Title":benchmark OR "Document Title":evaluation)`, 2023–2026 = **182**.
- **ACM DL**: `[Title:(agent OR agentic)] AND [Title:(benchmark OR evaluation)]`, 2023–2026. Broad-expansion default was 17,231; **Title-coded re-scope = 228** (verified on screen; full-text collection of 846,507). Top hits are genuine agent benchmarks (e.g., "Automatically Benchmarking LLM Code Agents," AAMAS '26). Record extraction + dedup/screen pending — magnitude expected similar to IEEE given AAMAS indexing.

## Results

| Source | Title-scoped | Dup vs OpenAlex 648 | Off-construct excl. | LLM/agentic candidates | Genuine NEW agentic benchmarks (est.) |
|---|---|---|---|---|---|
| SpringerLink | 172 | 5 | ~140 (chem/bio, non-LLM agent systems, conv. health) | ~19 (mostly EC4 app/system) | **0–4** |
| IEEE Xplore | 182 | 23 | 56 (RL/control, chem, conv., ABM, remote-sensing) | 103 | **~15–25** (25 named-benchmark titles not in OpenAlex; ≥15 pass construct on title) |
| ACM DL | 226 (re-scoped from 17,231) | 28 | 138 (fair-division/econ-theory 94, MARL/RL 14, gesture/embodied-HCI 12, conversational 9, ABM 7, robotics 2) | 55 | **~15–25** (21 named-benchmark titles not in OpenAlex) |

**Combined (pre abstract-construct-screen):** ~30–50 genuine NEW agentic-benchmark candidates across IEEE+ACM (Springer adds ~0–4). Cross-source dedup still needed (e.g., "LLM Agents for Interactive Workflow Provenance" appears in both IEEE SC25-W and ACM). Per-record decisions: `acm_dedup_screen.csv`; raw: `acm_raw.txt`.

Per-record decisions: `springer_dedup_screen.csv`, `ieee_dedup_screen.csv`. Raw harvests: `springer_tier_harvest.csv`, `ieee_p1_titles.txt`, `ieee_p2.csv`.

## Interpretation (honest, two-sided)

1. **Springer confirms coverage.** The publisher's own platform, field-scoped, adds **no canonical benchmark** and **0 overlap with the 259**. Directly answers "Springer not searched."

2. **IEEE reveals a real long-tail gap.** ~15–25 genuine LLM-agent benchmarks (mostly 2025–2026 IEEE *conference* papers: FinMCP-Bench, MAIA, ITBench, FOCAL, IEBench, AgentQE-Bench, DSGBench, PillagerBench, OmniCharacter++, UINavBench, CoSQA+, MEWA, ChemPaperBench, etc.) are **not** in the OpenAlex-primary set. None is a *canonical* benchmark (no SWE-bench/WebArena-class items were missed), so the paper's **core claim survives** — the probe set's canonical-core completeness (10/10) still holds. But this **substantiates, with real titles, the paper's own "long tail incompletely captured / absolute counts are lower bounds" limitation**, and the corpus can be materially strengthened by folding these in.

   This means the reviewer's coverage concern is *partly vindicated for the conference long tail* — exactly where OpenAlex title-streams under-sample IEEE proceedings. Best handled by **expanding the corpus**, not just rebutting.

## What remains (substantial — needs author construct-judgment; nothing fabricated)

1. **Abstract-level construct screen** of the IEEE (~103) + Springer (~19) candidates against IC1–IC3 / EC1–EC6 (distinguish genuine agent *benchmarks* from EC4 application/system papers). Requires reading abstracts; many borderline calls are author judgment.
2. **ACM DL** harvest (re-scoped) + same dedup/screen.
3. **Corpus integration**: assign verified new includes, recompute the PRISMA flow (identification/dedup/screen/included), and update `prisma_manifest.json`.
4. **Downstream propagation**: re-code the evidence map over the new N, regenerate Tables 3–4 + Fig. 2 distributions, reconsider whether any new benchmark belongs in the 17-row landscape matrix, and update the abstract/intro/methodology/limitations prose and counts.
5. **Re-verify** reproducibility (pipeline rerun) and the coverage section against the new multi-source design.

## Bottom line for the manuscript

The single-source criticism is now answerable with evidence: **five indices searched (OpenAlex, Crossref, Scopus, Springer, IEEE)**, canonical-core completeness re-confirmed, and the long tail explicitly expanded rather than asserted as a lower bound. This is a **major-revision-grade strengthening**, not a cosmetic one.
