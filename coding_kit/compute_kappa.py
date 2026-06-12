#!/usr/bin/env python3
"""Cohen's kappa per taxonomy attribute from two filled rater sheets.

Usage: python3 compute_kappa.py rater_A_sheet.csv rater_B_sheet.csv
Writes taxonomy_reliability.csv and prints a summary.

Rules:
- Rows where either rater set uncodable=1 are excluded (count reported).
- kappa = (po - pe) / (1 - pe); if pe == 1 (no variance in either rater),
  kappa is reported as 'UNDEFINED:no_variance' with percent agreement only.
- Interpretation bands (Landis & Koch 1977): <0 poor, .00-.20 slight,
  .21-.40 fair, .41-.60 moderate, .61-.80 substantial, .81-1.00 almost perfect.
"""
import csv, sys, os

ATTRS = (["Planning","Reasoning","ToolUse","Coding","Memory","Collaboration",
          "ScientificDiscovery","Recommendation","LongHorizonExecution","WebInteraction"]
       + ["Static","Interactive","Dynamic","Simulated","RealWorld","Embodied"]
       + ["Offline","Online","HumanInTheLoop","MultiAgent","FullyAutonomous"]
       + ["OpenSource","DatasetReleased","EnvironmentReleased","DockerSupport",
          "EvalScriptsAvailable"])

def load(path):
    with open(path, encoding="utf-8") as f:
        return {r["oa_id"]: r for r in csv.DictReader(f)}

def interp(k):
    if k < 0: return "poor"
    if k <= .20: return "slight"
    if k <= .40: return "fair"
    if k <= .60: return "moderate"
    if k <= .80: return "substantial"
    return "almost perfect"

def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    A, B = load(sys.argv[1]), load(sys.argv[2])
    ids = sorted(set(A) & set(B))
    if not ids:
        sys.exit("ERROR: no overlapping oa_id rows between sheets.")
    usable, excluded = [], 0
    for i in ids:
        if (A[i].get("uncodable","").strip() == "1" or
                B[i].get("uncodable","").strip() == "1"):
            excluded += 1
            continue
        usable.append(i)
    rows = []
    for attr in ATTRS:
        pairs = []
        for i in usable:
            a, b = A[i].get(attr,"").strip(), B[i].get(attr,"").strip()
            if a in ("0","1") and b in ("0","1"):
                pairs.append((int(a), int(b)))
        n = len(pairs)
        if n == 0:
            rows.append({"attribute": attr, "n": 0, "percent_agreement": "",
                         "kappa": "UNRESOLVED:no_coded_pairs", "interpretation": ""})
            continue
        po = sum(1 for a, b in pairs if a == b) / n
        pa1 = sum(a for a, _ in pairs) / n
        pb1 = sum(b for _, b in pairs) / n
        pe = pa1 * pb1 + (1 - pa1) * (1 - pb1)
        if abs(1 - pe) < 1e-12:
            rows.append({"attribute": attr, "n": n,
                         "percent_agreement": round(po, 3),
                         "kappa": "UNDEFINED:no_variance", "interpretation": ""})
        else:
            k = (po - pe) / (1 - pe)
            rows.append({"attribute": attr, "n": n,
                         "percent_agreement": round(po, 3),
                         "kappa": round(k, 3), "interpretation": interp(k)})
    out = os.path.join(os.path.dirname(os.path.abspath(sys.argv[1])),
                       "taxonomy_reliability.csv")
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["attribute","n","percent_agreement",
                                          "kappa","interpretation"])
        w.writeheader(); w.writerows(rows)
    ks = [r["kappa"] for r in rows if isinstance(r["kappa"], float)]
    print(f"rows: {len(ids)}  usable: {len(usable)}  excluded(uncodable): {excluded}")
    if ks:
        print(f"mean kappa over {len(ks)} defined attributes: {sum(ks)/len(ks):.3f}")
    for r in rows:
        print(f"  {r['attribute']:22s} n={r['n']:<3} agree={r['percent_agreement']} "
              f"kappa={r['kappa']} {r['interpretation']}")
    print(f"-> {out}")

if __name__ == "__main__":
    main()
