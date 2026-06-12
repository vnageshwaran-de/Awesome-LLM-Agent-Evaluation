#!/usr/bin/env python3
"""Inter-screener reliability (Cohen's kappa) for full-text double-screening.

Two human screeners decide Include/Exclude on the candidate pool independently
and blind to each other. This script joins their two sheets on the candidate
title and reports Cohen's kappa + percent agreement on the doubly-screened
Include/Exclude decisions.

Usage:
    python3 compute_screening_kappa.py \
        [screener1.csv] [screener2.csv]

Defaults:
    screener1 = ../coauthor_screening_returned.csv   (column 'YOUR decision')
    screener2 = screener2_blind.csv                  (column 'screener2_decision')

Rules:
- Decisions are mapped Include->1, Exclude->0 (case-insensitive).
- Rows where EITHER screener is blank or still 'Uncertain' are excluded from
  kappa (counts are reported separately) - kappa needs a resolved binary pair.
- kappa = (po - pe)/(1 - pe); if pe == 1 (no variance) -> 'UNDEFINED:no_variance'.
- Landis & Koch (1977) bands: <0 poor, .00-.20 slight, .21-.40 fair,
  .41-.60 moderate, .61-.80 substantial, .81-1.00 almost perfect.
"""
import csv, sys, os
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))

def load(path, title_col, dec_col):
    out = {}
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        if title_col not in (r.fieldnames or []) or dec_col not in (r.fieldnames or []):
            sys.exit(f"ERROR: {path} missing '{title_col}' or '{dec_col}'; "
                     f"has {r.fieldnames}")
        for row in r:
            t = (row[title_col] or "").strip()
            if t:
                out[t] = (row[dec_col] or "").strip()
    return out

def norm(v):
    v = (v or "").strip().lower()
    if v == "include": return 1
    if v == "exclude": return 0
    return None  # blank / uncertain / other

def interp(k):
    if k < 0: return "poor"
    if k <= .20: return "slight"
    if k <= .40: return "fair"
    if k <= .60: return "moderate"
    if k <= .80: return "substantial"
    return "almost perfect"

def main():
    s1 = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "coauthor_screening_returned.csv")
    s2 = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "screener2_blind.csv")
    A = load(s1, "Candidate title", "YOUR decision")
    B = load(s2, "Candidate title", "screener2_decision")
    titles = sorted(set(A) & set(B))
    if not titles:
        sys.exit("ERROR: no shared candidate titles between the two sheets.")

    pairs, skipped = [], 0
    raw1, raw2 = Counter(), Counter()
    for t in titles:
        a, b = norm(A[t]), norm(B[t])
        raw1[A[t].strip() or "(blank)"] += 1
        raw2[B[t].strip() or "(blank)"] += 1
        if a is None or b is None:
            skipped += 1
            continue
        pairs.append((a, b))

    n = len(pairs)
    print(f"shared candidates: {len(titles)}")
    print(f"screener1 decisions: {dict(raw1)}")
    print(f"screener2 decisions: {dict(raw2)}")
    print(f"resolved Include/Exclude pairs scored: {n}  (skipped blank/uncertain: {skipped})")
    if n == 0:
        print("screener2 not yet coded -> kappa pending. Fill screener2_blind.csv and re-run.")
        return

    po = sum(1 for a, b in pairs if a == b) / n
    pa1 = sum(a for a, _ in pairs) / n
    pb1 = sum(b for _, b in pairs) / n
    pe = pa1 * pb1 + (1 - pa1) * (1 - pb1)
    # confusion
    c = Counter((a, b) for a, b in pairs)
    print(f"confusion  IncInc={c[(1,1)]}  IncExc(S1=I,S2=E)={c[(1,0)]}  "
          f"ExcInc(S1=E,S2=I)={c[(0,1)]}  ExcExc={c[(0,0)]}")
    print(f"percent agreement: {po:.3f}")
    if abs(1 - pe) < 1e-12:
        print("kappa: UNDEFINED:no_variance (one label absent in both screeners)")
    else:
        k = (po - pe) / (1 - pe)
        print(f"Cohen's kappa: {k:.3f}  ({interp(k)})")

    out = os.path.join(HERE, "screening_reliability.csv")
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["n_scored", "percent_agreement", "kappa", "interpretation",
                    "skipped_blank_or_uncertain"])
        if abs(1 - pe) < 1e-12:
            w.writerow([n, round(po, 3), "UNDEFINED:no_variance", "", skipped])
        else:
            w.writerow([n, round(po, 3), round(k, 3), interp(k), skipped])
    print(f"-> {out}")

if __name__ == "__main__":
    main()
