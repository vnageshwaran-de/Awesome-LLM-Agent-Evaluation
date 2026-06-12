# Search Log (PRISMA-ScR identification stage)

Human-readable summary; the canonical machine-readable logs are
[`search_log.json`](search_log.json), [`prisma_manifest.json`](prisma_manifest.json),
and [`recall_gap_estimate.json`](recall_gap_estimate.json). Executed 2026-06-05;
window 2023-01-01 → 2026-06-30.

## Identification counts

| Source | Tier | Scope | Count | Status |
|---|---|---|---|---|
| **OpenAlex** (primary) | 1 | 6 title-search streams, preprints retained | **648** unique | reproducible harvest (CC0) |
| Crossref | 1b | 3 bibliographic queries, depth-capped | 219 in-scope | recall engine only (not summed) |
| **ScienceDirect** | 2 | TAK field-scoped, authenticated UI (2026-06-08) | **785** | `count_only_verified` (probe 0/10) |
| **IEEE Xplore** | 2 | Abstract/All-Metadata, authenticated UI | **962** | `count_only_verified` (probe 0/10) |
| **ACM Digital Library** | 2 | field codes degraded to all-field | **17,231** | `count_only_broad_expansion` (probe 0/10) |
| **Scopus** | 3 | TITLE-ABS-KEY, authenticated UI | **4,836** | `count_only_verified` (**probe 9/10**) |
| WoS / SpringerLink / Semantic Scholar | 3 | — | — | `UNRESOLVED:no_credentials` |

Only the Tier-1 OpenAlex union is summed into the PRISMA flow.

## Reconciled PRISMA-ScR flow (check: PASS)

```
identified 648  -> duplicates removed 205  -> screened 443
            -> excluded 243  -> assessed 200  -> +59 snowball
            -> included 259
reconciliation: 648-205=443  and  200+59=259
```

- Exclusion breakdown (of 243): **EC6 priority-cutoff 236**, EC2 prompt-only 4, EC1 general-NLP 2, EC4 model-centric 1 (EC3/EC5 = 0). Content-based exclusions are few (7) because streams are agent-scoped; the bounding mechanism was the pre-registered, citation-ranked cutoff at `target_included = 200` (fully logged).
- Snowballing: all **59** additions were **backward** (references of included works); forward citation screening added 0.
- Included in evidence map: **259**
- Hand-verified deep-dive subset (landscape matrix): **17**

## Recall-gap (RQ5, label = `estimate`)

- Probe set of 10 source-verified canonical benchmarks: OpenAlex **10/10 (1.00)**, probe gap **0.0**
  across all six probed sources. Crossref 4/10; ScienceDirect/IEEE/ACM **0/10** each (host citing
  works only). **Scopus 9/10** — the one independent index carrying the benchmark papers themselves;
  OpenAlex×Scopus 2×2: both=9, OA-only=1, Scopus-only=0 → adds zero canonical benchmarks OpenAlex lacked.
- Chapman capture–recapture: n_OA=259, n_CR=219, m=16 → N̂≈3364, implied OpenAlex
  recall ≈ **0.077**, reported as a **loose lower bound** (heterogeneous engines
  depress overlap → inflate N̂). Contradicted, reassuringly, by the 100% probe capture. Capture–recapture vs ScienceDirect: **declined** (m = 0; same-population assumption violated).
- Confidence framing: composition shares **directionally reliable**; absolute counts
  are **lower bounds**. Full analysis: [`recall_gap_estimate.json`](recall_gap_estimate.json).

## Integrity
Every included study, DOI, venue and citation count originates from a live OpenAlex
record; no records were fabricated. Recall outputs are labelled `estimate`, never
`verified`. Heuristic taxonomy flags require human verification (see `validation_report.md`).
