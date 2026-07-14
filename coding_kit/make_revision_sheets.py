#!/usr/bin/env python3
"""Revision-round annotation sheets (generated 2026-07-11, seed=42).

Produces, for the AIR major-revision:
  1. audit_<Lexicon>_sheet.csv  -- 30-record precision-audit sheets for every
     broad-map lexicon not yet audited (R3 major comment 2). Existing audits
     (ScientificDiscovery, Collaboration, Planning) are in
     methodology/lexicon_precision_audit.csv and are NOT regenerated.
  2. setaside_validation_sheet.csv -- year-stratified random sample (n=55,
     2026 oversampled) of the 236 not-assessed records for human screening
     and coding (R2 major comment 1).

Rater instructions: fill `genuine_target` (audit sheets) with 1/0 after
reading title+abstract; fill `human_decision` (include/exclude) and the
attribute columns (1/0) on the set-aside sheet. Leave `notes` free-text.
"""
import csv, json, os, random

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
SEED = 42

AUDIT_LEXICONS = ["Reasoning", "ToolUse", "Coding", "Memory", "Recommendation",
                  "LongHorizonExecution", "WebInteraction"]
REPRO_LEXICONS = ["OpenSource", "DatasetReleased", "DockerSupport"]
N_PER_LEXICON = 30

def load_abstracts():
    path = os.path.join(ROOT, "methodology", "retrieval_manifest.csv")
    return {r["oa_id"]: (r.get("abstract") or "") for r in csv.DictReader(open(path))}

def main():
    random.seed(SEED)
    abstracts = load_abstracts()
    tax = json.load(open(os.path.join(ROOT, "data", "benchmark_taxonomy.json")))["benchmarks"]

    # ---- 1. precision-audit sheets --------------------------------------
    for group, lexes in (("capabilities", AUDIT_LEXICONS), ("reproducibility", REPRO_LEXICONS)):
        for lex in lexes:
            flagged = sorted((r for r in tax if r.get(group, {}).get(lex)),
                             key=lambda r: r["oa_id"])
            n = min(N_PER_LEXICON, len(flagged))
            sample = random.sample(flagged, n) if len(flagged) > n else flagged
            out = os.path.join(HERE, f"audit_{lex}_sheet.csv")
            with open(out, "w", newline="") as f:
                w = csv.writer(f)
                w.writerow(["lexicon", "idx", "oa_id", "title",
                            "abstract_first400", "genuine_target", "notes"])
                for i, r in enumerate(sample, 1):
                    w.writerow([lex, i, r["oa_id"], r["name"],
                                abstracts.get(r["oa_id"], "")[:400], "", ""])
            print(f"wrote {out} (n={n}, flagged={len(flagged)})")

    # ---- 2. set-aside validation sheet ----------------------------------
    dec = list(csv.DictReader(open(os.path.join(ROOT, "methodology", "screening_decisions.csv"))))
    setaside = [r for r in dec if r["decision"] == "not_assessed"]
    by_year = {}
    for r in setaside:
        by_year.setdefault(r["year"], []).append(r)
    # allocation: proportional with a floor of 5 per year; 2026 dominates anyway
    N = 55
    total = len(setaside)
    sample = []
    for y in sorted(by_year):
        pool = sorted(by_year[y], key=lambda r: r["oa_id"])
        k = max(5, round(N * len(pool) / total)) if len(pool) >= 5 else len(pool)
        sample += random.sample(pool, min(k, len(pool)))
    sample = sample[:N]
    attrs = ["Planning", "Reasoning", "ToolUse", "Coding", "Memory", "Collaboration",
             "ScientificDiscovery", "Recommendation", "LongHorizonExecution",
             "WebInteraction", "Interactive", "RealWorld", "Static",
             "OpenSource", "DatasetReleased", "DockerSupport"]
    out = os.path.join(HERE, "setaside_validation_sheet.csv")
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["idx", "oa_id", "year", "cited_by_count", "title",
                    "abstract_first400", "human_decision"] + attrs + ["notes"])
        for i, r in enumerate(sample, 1):
            w.writerow([i, r["oa_id"], r["year"], r["cited_by_count"], r["title"],
                        abstracts.get(r["oa_id"], "")[:400], ""] + [""] * len(attrs) + [""])
    years = sorted(set(r["year"] for r in sample))
    print(f"wrote {out} (n={len(sample)}, years={years})")

if __name__ == "__main__":
    main()
