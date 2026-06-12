#!/usr/bin/env python3
"""Per-tag Cohen's kappa for the W/H/E dual-coding matrix.

compute_kappa.py handles File 2's binary rater sheets (one column per
attribute). It CANNOT score File 1 (matrix_dualcoding_instrument.csv), whose
codes are free-text phrases with embedded tag codes, e.g.
    "Web/environment perception (W4, core); Planning (W1); Multi-turn (W2)"
This script extracts the tag codes from `rater_A_code` and `rater_B_code`,
turns each row into a set of present tags, and computes Cohen's kappa per tag
across the benchmarks of that tag's axis.

Usage:
    python3 compute_matrix_kappa.py [matrix_dualcoding_instrument.csv]

Writes matrix_tag_reliability.csv (axis, tag, n, n_present_A, n_present_B,
percent_agreement, kappa, interpretation) next to the input and prints a
summary.

Conventions mirror compute_kappa.py:
- kappa = (po - pe) / (1 - pe).
- If pe == 1 (a tag is all-0 or all-1 in both raters -> no variance), kappa is
  reported as 'UNDEFINED:no_variance' with percent agreement only.
- Landis & Koch (1977) bands: <0 poor, .00-.20 slight, .21-.40 fair,
  .41-.60 moderate, .61-.80 substantial, .81-1.00 almost perfect.
"""
import csv, sys, os, re

# Tag universe per axis. Order = report order. Longer/letter forms (E2a..E2d)
# are listed before E1 only for readability; matching uses explicit alternation
# so there is no prefix ambiguity.
AXIS_TAGS = {
    "W": ["W1", "W2", "W3", "W4", "W5", "W6"],
    "H": ["H1", "H2", "H3"],
    "E": ["E1", "E2a", "E2b", "E2c", "E2d"],
}
# Match E2a/E2b/E2c/E2d before bare E1/E2; \b handles separators like ()/ +,
TAG_RE = re.compile(r"E2[abcd]|E1|W[1-6]|H[1-3]")

def axis_of(attribute):
    """First non-space char of the attribute cell is the axis letter (W/H/E)."""
    a = attribute.strip()
    return a[0] if a and a[0] in "WHE" else None

def tags_in(text):
    return set(TAG_RE.findall(text or ""))

def interp(k):
    if k < 0: return "poor"
    if k <= .20: return "slight"
    if k <= .40: return "fair"
    if k <= .60: return "moderate"
    if k <= .80: return "substantial"
    return "almost perfect"

def kappa(pairs):
    """pairs: list of (a01, b01). Returns (po, kappa_or_None)."""
    n = len(pairs)
    po = sum(1 for a, b in pairs if a == b) / n
    pa1 = sum(a for a, _ in pairs) / n
    pb1 = sum(b for _, b in pairs) / n
    pe = pa1 * pb1 + (1 - pa1) * (1 - pb1)
    if abs(1 - pe) < 1e-12:
        return po, None
    return po, (po - pe) / (1 - pe)

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "matrix_dualcoding_instrument.csv")
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        need = {"benchmark_name", "attribute", "rater_A_code", "rater_B_code"}
        if not need.issubset(reader.fieldnames or []):
            sys.exit(f"ERROR: expected columns {sorted(need)}; got {reader.fieldnames}")
        # rows[axis] = list of (A_tagset, B_tagset) for each benchmark in that axis
        rows = {"W": [], "H": [], "E": []}
        for r in reader:
            ax = axis_of(r["attribute"])
            if ax is None:
                continue
            rows[ax].append((tags_in(r["rater_A_code"]), tags_in(r["rater_B_code"])))

    out_rows = []
    for ax in ("W", "H", "E"):
        axis_rows = rows[ax]
        for tag in AXIS_TAGS[ax]:
            pairs = [(1 if tag in A else 0, 1 if tag in B else 0) for A, B in axis_rows]
            n = len(pairs)
            if n == 0:
                continue
            na = sum(a for a, _ in pairs)
            nb = sum(b for _, b in pairs)
            po, k = kappa(pairs)
            out_rows.append({
                "axis": ax, "tag": tag, "n": n,
                "n_present_A": na, "n_present_B": nb,
                "percent_agreement": round(po, 3),
                "kappa": ("UNDEFINED:no_variance" if k is None else round(k, 3)),
                "interpretation": ("" if k is None else interp(k)),
            })

    out = os.path.join(os.path.dirname(os.path.abspath(path)), "matrix_tag_reliability.csv")
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["axis", "tag", "n", "n_present_A",
                                          "n_present_B", "percent_agreement",
                                          "kappa", "interpretation"])
        w.writeheader(); w.writerows(out_rows)

    defined = [r["kappa"] for r in out_rows if isinstance(r["kappa"], float)]
    print(f"benchmarks per axis: W={len(rows['W'])} H={len(rows['H'])} E={len(rows['E'])}")
    print(f"tags scored: {len(out_rows)}  (defined kappa: {len(defined)})")
    if defined:
        print(f"mean kappa over defined tags: {sum(defined)/len(defined):.3f}")
    for r in out_rows:
        print(f"  {r['axis']} {r['tag']:4s} n={r['n']:<3} "
              f"A={r['n_present_A']:<2} B={r['n_present_B']:<2} "
              f"agree={r['percent_agreement']} kappa={r['kappa']} {r['interpretation']}")
    print(f"-> {out}")

if __name__ == "__main__":
    main()
