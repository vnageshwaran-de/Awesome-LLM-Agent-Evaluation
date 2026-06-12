#!/usr/bin/env python3
"""
Round-4 reviewer reanalysis. Reproduces the pipeline classifier (build_review.py)
and computes three things the reviewer asked for:
  #2  stream-only recall vs index-coverage recall for the canonical probe set
  #6  corrected ScientificDiscovery share (drop over-broad 'research'/'experiment')
  #1  year-stratified sensitivity of the multi-agent / open-source trend claims
Read-only: writes a JSON report, does not mutate the published artifacts.
"""
import csv, json, os
from collections import defaultdict

HERE = os.path.dirname(__file__)
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")

# ---- pipeline lexicons (verbatim from build_review.py) --------------------
PARADIGM_KEYWORDS = {
    "MultiAgent": ["multi-agent", "multi agent"],
}
REPRO_KEYWORDS = {
    "OpenSource": ["open-source", "open source", "github", "publicly available", "release"],
}
# ScientificDiscovery: original (buggy) vs corrected (minimal surgical fix)
SD_ORIG = ["scientif", "research", "discovery", "experiment", "data science", "ml engineering"]
SD_FIXED = ["scientif", "discovery", "data science", "ml engineering"]  # drop 'research','experiment'

def hit(text, words):
    t = text.lower()
    return any(w in t for w in words)

# ---- load data ------------------------------------------------------------
man = {}
for r in csv.DictReader(open(os.path.join(HERE, "retrieval_manifest.csv"))):
    man[r["oa_id"]] = r
dec = list(csv.DictReader(open(os.path.join(HERE, "screening_decisions.csv"))))
tax = json.load(open(os.path.join(DATA, "benchmark_taxonomy.json")))["benchmarks"]
taxby = {b["oa_id"]: b for b in tax}

def text_for(oa_id, title=""):
    m = man.get(oa_id)
    if m and m.get("abstract", "").strip():
        return f"{m['title']} {m['abstract']}"
    return title or (m["title"] if m else "")

report = {}

# ====================== #2  STREAM vs INDEX recall =========================
probe = json.load(open(os.path.join(HERE, "recall_gap_estimate.json")))["probe_set"]["members"]
stream_rows = []
n_stream = 0
for p in probe:
    oa = p["oa_id"]; name = p["benchmark"]
    m = man.get(oa)
    streams = m["streams"] if m else "(absent_from_manifest)"
    toks = [s for s in streams.split("|") if s]
    seedtoks = [s for s in toks if s.startswith("seed:")]
    qtoks = [s for s in toks if not s.startswith("seed:")]
    via_stream = len(qtoks) > 0
    n_stream += 1 if via_stream else 0
    stream_rows.append({
        "benchmark": name, "oa_id": oa,
        "via_query_stream": via_stream,
        "via_seed_only": (len(seedtoks) > 0 and not via_stream),
        "query_streams": qtoks, "seed_tags": seedtoks,
    })
report["item2_recall"] = {
    "index_coverage_recall": f"{len(probe)}/{len(probe)} (OpenAlex hosts the record)",
    "stream_only_recall": f"{n_stream}/{len(probe)}",
    "stream_only_fraction": round(n_stream/len(probe), 3),
    "per_benchmark": stream_rows,
    "note": "Index coverage = record exists in OpenAlex (seed fetch by name). "
            "Stream recall = retrieved by one of the six topical title-query streams.",
}

# ====================== #6  ScientificDiscovery artifact ===================
inc = list(taxby.keys())  # 259 included
def sd_share(keywords):
    by_year = defaultdict(lambda: [0, 0])  # [flagged, total]
    flagged_titles = []
    for oa in inc:
        b = taxby[oa]
        y = str(b["year"])
        txt = text_for(oa, b["name"])
        f = hit(txt, keywords)
        by_year[y][0] += 1 if f else 0
        by_year[y][1] += 1
        if f:
            flagged_titles.append(b["name"])
    tot_f = sum(v[0] for v in by_year.values())
    tot_n = sum(v[1] for v in by_year.values())
    return tot_f, tot_n, {y: {"flagged": v[0], "n": v[1], "share": round(v[0]/v[1], 3)}
                          for y, v in sorted(by_year.items())}, flagged_titles

of, on, oy, _ = sd_share(SD_ORIG)
ff, fn, fy, ftitles = sd_share(SD_FIXED)
report["item6_scientific_discovery"] = {
    "coder": "keyword_heuristic (machine); taxonomy flagged needs_human_verification=True",
    "original_keywords": SD_ORIG,
    "original_share": f"{of}/{on} = {round(of/on*100,1)}%",
    "corrected_keywords": SD_FIXED,
    "corrected_share": f"{ff}/{fn} = {round(ff/fn*100,1)}%",
    "corrected_by_year": fy,
    "corrected_flagged_titles": ftitles,
}

# ====================== #1  year-stratified trend ==========================
# included set: use taxonomy codes (MultiAgent paradigm, OpenSource repro)
# set-aside set: classify fresh from abstract/title
def code_included(oa, key):
    b = taxby[oa]
    if key == "MultiAgent":
        return bool(b["paradigm"].get("MultiAgent"))
    if key == "OpenSource":
        return bool(b["reproducibility"].get("OpenSource"))

def code_text(oa, title, key):
    txt = text_for(oa, title)
    kw = PARADIGM_KEYWORDS["MultiAgent"] if key == "MultiAgent" else REPRO_KEYWORDS["OpenSource"]
    return hit(txt, kw)

# build per-year populations
inc_by_year = defaultdict(list)
for oa in inc:
    inc_by_year[str(taxby[oa]["year"])].append(oa)

setaside = [r for r in dec if r["decision"] == "not_assessed"]
sa_by_year = defaultdict(list)
for r in setaside:
    sa_by_year[r["year"]].append((r["oa_id"], r["title"]))

def share(oalist_inc, oalist_sa, key):
    f = t = 0
    for oa in oalist_inc:
        f += 1 if code_included(oa, key) else 0; t += 1
    for oa, title in oalist_sa:
        f += 1 if code_text(oa, title, key) else 0; t += 1
    return (round(f/t, 3) if t else None), f, t

strat = {}
for y in ["2023", "2024", "2025", "2026"]:
    ma_inc, _, n_inc = share(inc_by_year.get(y, []), [], "MultiAgent")
    ma_all, _, n_all = share(inc_by_year.get(y, []), sa_by_year.get(y, []), "MultiAgent")
    os_inc, _, _ = share(inc_by_year.get(y, []), [], "OpenSource")
    os_all, _, _ = share(inc_by_year.get(y, []), sa_by_year.get(y, []), "OpenSource")
    strat[y] = {
        "n_included": n_inc, "n_with_setaside": n_all,
        "multiagent_share_included_only": ma_inc,
        "multiagent_share_with_setaside": ma_all,
        "opensource_share_included_only": os_inc,
        "opensource_share_with_setaside": os_all,
    }
report["item1_year_stratified"] = {
    "claim_under_test": "2026 multi-agent share ~0.43 (up), open-source share ~0.24 (down)",
    "method": "included codes from taxonomy; set-aside coded from abstract/title with same lexicon",
    "by_year": strat,
}

out = os.path.join(HERE, "round4_reanalysis.json")
json.dump(report, open(out, "w"), indent=2)
print(json.dumps(report, indent=2))
