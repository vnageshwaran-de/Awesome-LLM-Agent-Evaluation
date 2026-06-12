#!/usr/bin/env python3
"""Generate blind dual-coding sheets: stratified random sample (n=50, by year,
seed=42) of included studies. Emits rater_A_sheet.csv and rater_B_sheet.csv
(identical rows, blank attribute cells, NO machine labels -> blind coding)."""
import csv, json, os, random

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
SEED, N = 42, 50

ATTRS = (["Planning","Reasoning","ToolUse","Coding","Memory","Collaboration",
          "ScientificDiscovery","Recommendation","LongHorizonExecution","WebInteraction"]
       + ["Static","Interactive","Dynamic","Simulated","RealWorld","Embodied"]
       + ["Offline","Online","HumanInTheLoop","MultiAgent","FullyAutonomous"]
       + ["OpenSource","DatasetReleased","EnvironmentReleased","DockerSupport",
          "EvalScriptsAvailable"])

def main():
    recs = json.load(open(os.path.join(DATA, "_final_records.json")))["records"]
    random.seed(SEED)
    by_year = {}
    for r in recs:
        by_year.setdefault(r.get("year") or 0, []).append(r)
    total = len(recs)
    sample = []
    for y in sorted(by_year):
        pool = sorted(by_year[y], key=lambda r: r["oa_id"])  # deterministic order
        k = max(1, round(N * len(pool) / total))
        sample += random.sample(pool, min(k, len(pool)))
    sample = sample[:N]
    rows = []
    for r in sample:
        row = {"oa_id": r["oa_id"], "title": r["title"], "year": r["year"],
               "doi": r["doi"], "url": r.get("url",""), "repo": r.get("repo",""),
               "abstract_first200": (r.get("abstract","") or "")[:200],
               "uncodable": "", "notes": ""}
        for a in ATTRS:
            row[a] = ""
        rows.append(row)
    fields = (["oa_id","title","year","doi","url","repo","abstract_first200"]
              + ATTRS + ["uncodable","notes"])
    for sheet in ("rater_A_sheet.csv", "rater_B_sheet.csv"):
        with open(os.path.join(HERE, sheet), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)
    print(f"wrote {len(rows)}-row blind sheets (seed={SEED}, stratified by year)")

if __name__ == "__main__":
    main()
