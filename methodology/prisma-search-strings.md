# PRISMA-ScR Search Strings

Reproducible queries used in the *identification* stage. The canonical,
machine-readable record of all queries, per-stream counts, timestamps and
status notes is [`search_log.json`](search_log.json); this file is the
human-readable summary. Temporal window: **2023-01-01 → 2026-06-30**.

## Tier-1 — OpenAlex (primary, reproducible; CC0 metadata)
Six title-search streams over `https://api.openalex.org/works`, 2023–2026 window,
**preprints retained** (no `type` filter at search time), saturation rule + 200/stream cap:

```
title.search="agent benchmark"
title.search="agentic benchmark"
title.search="LLM agents evaluation"
title.search="agent evaluation benchmark"
title.search="autonomous agents benchmark"
title.search="language model agents benchmark"
  -> unioned and deduplicated to 648 unique records
```

## Tier-1b — Crossref (independent recall engine only)
```
query.bibliographic = {agent benchmark / LLM agent evaluation / ...}
 ; 2023-2026 ; depth-capped   -> 219 in-scope (feeds recall-gap estimate; not summed)
```

## Tier-2 — ScienceDirect (count-only, VERIFIED 2026-06-08)
Authenticated institutional session; field scoping honored (`count_only_verified`):
```
Title-Abstract-Keywords:
("large language model" OR LLM) AND (agent OR autonomous)
 AND (benchmark OR evaluation) ; 2023-2026   ->  785 (count only)
```
Probe check: 0/10 of the canonical probe benchmarks hosted (indexes citing works
only) — probe gap vs the expanded source union unchanged at 0.0.
Evidence: `sciencedirect_tier2.json`.

## Tier-2 — IEEE Xplore / ACM (count-only, VERIFIED 2026-06-08)
Authenticated institutional session; per-title probes one-at-a-time; no bulk export, no CAPTCHA bypass.
```
IEEE (field codes honored, count_only_verified, probe 0/10):
  (("Abstract":"Large Language Model" OR "Abstract":LLM)
   AND ("Abstract":Agent OR "Abstract":Autonomous)
   AND ("All Metadata":Evaluation OR "All Metadata":Benchmark))      -> 962
ACM (URL interface degraded field codes to all-field; broad_expansion, probe 0/10):
  [[All: "large language model"] OR [All: llm]] AND [[All: agent]
   OR [All: autonomous]] AND [[All: evaluation] OR [All: benchmark]] -> 17,231 (broad)
```
Both host only works citing the benchmarks (0/10), not the benchmark papers themselves.
Evidence: `ieee_acm_tier2.json`.

## Tier-3 — Scopus (count-only, VERIFIED 2026-06-08; DECISIVE probe)
```
TITLE-ABS-KEY(("large language model" OR LLM) AND (agent OR autonomous)
 AND (benchmark OR evaluation)) AND PUBYEAR>2022 AND PUBYEAR<2027     -> 4,836
```
Probe **9/10** (all but DataSciBench, a 2025 preprint); OpenAlex×Scopus 2×2: both=9,
OA-only=1, Scopus-only=0 → a 9/10-recall independent index adds zero canonical
benchmarks OpenAlex lacked, confirming the Crossref capture–recapture (~7.7%) is a
heterogeneity artifact. Evidence: `scopus_tier3.json`.
Web of Science / SpringerLink / Semantic Scholar remain `UNRESOLVED:no_credentials`.

## Secondary source
Backward/forward **snowballing** (Wohlin, 2014) over a canonical benchmark list
(AgentBench, SWE-bench, WebArena, GAIA, AppWorld, OSWorld, AgentBoard,
VisualWebArena, …), contributing **59 of the 259** included studies. This is the
primary recall mechanism for preprint-first and proceedings-indexed artifacts that
title search under-samples; its quantitative effect is bounded by the recall-gap
analysis (`recall_gap_estimate.json`).
