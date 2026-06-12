# PRISMA finalization — what's automated vs. what needs your data

Status as of 2026-06-05. Identification counts already in place: IEEE 268, ACM 15,
SpringerLink 417. `\nBench` = 17.

## Task 1 — arXiv identification count  (automatable; currently blocked by arXiv rate-limit)

The documented query was executed against `export.arxiv.org/api/query`. The API is
returning **HTTP 503 / "Rate exceeded"** because the request IP is temporarily
throttled. This is transient (clears in a few minutes). To finish:

1. Open the query URL (it's in `PROJECT_CONTEXT.md` §5) in a browser and read
   the integer inside `<opensearch:totalResults>...</opensearch:totalResults>`.
2. Run, from this `methodology/` folder:

       python3 finalize_prisma.py --arxiv <THAT_NUMBER>

   This writes the count to `screening-worksheet.xlsx` → Search Log!D7 (total
   recomputes to 700 + arXiv) and sets `\nArXiv` + `\nIdentified` in
   `prisma_flow.tex`. Then recompile:

       cd ../../AIR_submission/figures && pdflatex prisma_flow.tex

## Task 2 — screening-stage counts  (REQUIRES your record-by-record screening)

These cannot be computed or invented — they come from you and your co-author
actually screening the ~700+ deduplicated records. In `screening-worksheet.xlsx`:

- **Screening sheet** — one row per deduplicated record; fill `TA decision`
  (Advance/Exclude), `FT decision` (Include/…), and `Exclusion reason` (EC1–EC6).
- **PRISMA Counts sheet** auto-computes screened / excluded / assessed / EC1–EC6 /
  included, with a CHECK cell that flags arithmetic mismatch.

Then copy those computed values into the figure, e.g.:

    python3 finalize_prisma.py --arxiv <N> --dup <D> --exclscreen <X> \
        --assessed <A> --ec EC1 EC2 EC3 EC4 EC5 EC6 --snow <S> --included <I>

(or edit the `\newcommand` macros at the top of `prisma_flow.tex` by hand), then
`pdflatex prisma_flow.tex`. The script prints an arithmetic OK/MISMATCH check.

## Task 3 — Cohen's kappa  (REQUIRES your two raters' agreement counts)

In the **Inter-rater Kappa** sheet, fill the four 2×2 cells for each calculator
from the two raters' independent decisions:

- (A) Title/abstract screening — Include/Exclude agreement (cells B7,C7,B8,C8).
- (B) Taxonomy coding — Agree/Disagree per W/H/E code (cells B18,C18,B19,C19).

κ, Po, Pe, and the Landis–Koch band compute automatically. Report κ(A) in the
"Screening and coding reliability" narrative and κ(B) with the landscape matrix.

> Tasks 2 and 3 depend on primary screening data that only the authors can
> produce. Fabricating these numbers would be research misconduct, so they are
> intentionally left blank for you to fill.
