# §2.6 Full-text screening and inter-screener reliability — protocol draft

> Draft methods text for §2.6. Numbers in **[brackets]** are placeholders to be
> filled **after** the second human screener completes `screener2_blind.csv` and
> `compute_screening_kappa.py` is run. No reliability figure is asserted here
> until it has been reproduced from the two human screening sheets.

## Draft text

Records advancing past title/abstract screening (n = **[185]** candidate
records across retrieval Tiers 1–3 from ACM, IEEE, Springer, and Scopus) were
assessed at full text against the inclusion criteria. A record was included only
if it **proposes, formalizes, or analyzes a procedure for measuring an
LLM-driven agent taking sequential, state-altering actions over ≥ 2 dependent
steps** (IC1–IC3); records were excluded under the pre-registered exclusion
categories EC1–EC6 (e.g., non-LLM agents, single-system application papers
without a reusable evaluation procedure, surveys/position pieces, and
out-of-scope uses of the word "agent").

To estimate the reliability of these decisions, the full candidate pool was
**double-screened independently by two human screeners (S1 and S2), each blind
to the other's decisions**. S2 coded from a worksheet (`screener2_blind.csv`)
containing only the bibliographic fields (tier, source, title, link), with the
decision and rationale columns withheld. Inter-screener agreement was quantified
with Cohen's κ over the doubly-screened Include/Exclude decisions
(`compute_screening_kappa.py`): **κ = [TBD]** (percent agreement = **[TBD]%**,
n = **[TBD]** doubly-screened records), indicating **[TBD: Landis–Koch band]**
agreement. Disagreements were reconciled by discussion between S1 and S2; any
case left unresolved was adjudicated by a third senior author. Reliability is
reported from the **pre-reconciliation** decisions; the final corpus uses the
post-reconciliation consensus.

## Note on agent-assisted retrieval (for transparency)

An LLM assistant was used **only to retrieve abstracts and full texts and to
surface candidate rationales** for records flagged as uncertain or screened from
title alone. **All Include/Exclude decisions are made by the human screeners**;
no automated decision enters the corpus. The [14] records that required
full-text resolution (the 6 prior "Uncertain" and 8 title-only "Include" rows)
carry machine-surfaced evidence in their notes, but their final disposition is
set by the human double-screening described above.

## How to fill the placeholders

1. A second human screener completes `screener2_blind.csv` (Include / Exclude in
   `screener2_decision`), blind to `coauthor_screening_returned.csv`.
2. Run, from this folder:
   `python3 compute_screening_kappa.py`
   This reads S1 (`../coauthor_screening_returned.csv`, column `YOUR decision`)
   and S2 (`screener2_blind.csv`, column `screener2_decision`), prints κ, percent
   agreement, n, and the confusion counts, and writes `screening_reliability.csv`.
3. Copy κ, percent agreement, n, and the Landis–Koch band into the bracketed
   slots above. Report κ from the pre-reconciliation sheets only.
