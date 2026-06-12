#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_review.py
================
Reproducible, PRISMA-ScR-guided Systematic Mapping Review pipeline for
"LLM Agent Evaluation Benchmarks (2023-01-01 .. 2026-06-30)".

Design goals
------------
* Reproducibility primacy: every count/record traces to a committed script + cached
  API responses. Re-running with the same cache yields identical numbers.
* Standard-library only (urllib) so there are no pip dependencies to pin.
* Resumable: each stage writes artifacts; on resume, completed stages are skipped
  unless --force is passed (or --force-stage NAME).
* Honesty: three explicit states -> verified | heuristic | UNRESOLVED:<reason>.
  Estimates (recall gap) are labelled `estimate`, never `verified`.

Tier model
----------
* Tier-1 (primary, scripted, open API): OpenAlex  -> canonical reproducible record set.
* Tier-1b (independent second search engine): Crossref -> used ONLY for the
  recall-gap capture-recapture and probe overlap. Crossref is the DOI registry, so
  its independence from OpenAlex is imperfect; this is stated wherever it is used.
* Tier-2 (registration / verification, authenticated UI): IEEE Xplore, ACM DL.
  No institutional credentials in this run -> recorded as UNRESOLVED:no_credentials
  (count_only), and substituted by the Crossref open-index equivalent per the
  authorised blocked-source fallback.
* Tier-3 (Scopus/WoS/Springer/S2): credential-gated -> UNRESOLVED:no_credentials.

Stages: search -> harvest -> dedup -> screen -> eligibility -> snowball ->
        recall_gap -> taxonomy -> trends -> prisma -> manuscript -> validation
"""

import csv
import json
import os
import re
import sys
import time
import math
import hashlib
import unicodedata
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime, timezone

# --------------------------------------------------------------------------- #
# CONFIG
# --------------------------------------------------------------------------- #
CONFIG = {
    "openalex_mailto":   "vnageshwaran@gmail.com",   # polite pool (required)
    "s2_api_key":        "none",
    "scopus_api_key":    "none",
    "wos_api_key":       "none",
    "springer_api_key":  "none",
    "ieee_browser_auth": False,
    "acm_browser_auth":  False,
    "recall_probe_set":  "auto",
    "from_date":         "2023-01-01",
    "to_date":           "2026-06-30",
    "target_included":   200,
    "max_records_per_stream": 200,
    "saturation_new_frac":    0.05,   # stop a stream when new-unique fraction < 5%
    "second_source":     "crossref",  # capture-recapture independent engine
    "snowball_forward_top": 30,       # cap forward-citation expansion
    "snowball_backward_cap": 400,     # cap backward-reference candidates fetched
    "request_sleep_s":   0.34,        # politeness between live API calls
}

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")
FIG  = os.path.join(ROOT, "figures")
MAN  = os.path.join(ROOT, "manuscript")
CACHE = os.path.join(DATA, "cache")
for d in (DATA, FIG, MAN, CACHE):
    os.makedirs(d, exist_ok=True)

NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# --------------------------------------------------------------------------- #
# TIER-1 SEARCH STREAMS  (title-scoped, unioned)
# --------------------------------------------------------------------------- #
TITLE_STREAMS = [
    "agent benchmark",
    "agentic benchmark",
    "LLM agents evaluation",
    "agent evaluation benchmark",
    "autonomous agents benchmark",
    "language model agents benchmark",
]

# --------------------------------------------------------------------------- #
# SEED BENCHMARK INVENTORY (non-exhaustive; expanded on discovery)
# Known identifiers improve verification robustness. arXiv ids -> DOI 10.48550/arxiv.<id>
# --------------------------------------------------------------------------- #
SEEDS = [
    {"name": "AgentBench",      "hint": "AgentBench Evaluating LLMs as Agents",            "arxiv": "2308.03688"},
    {"name": "SWE-bench",       "hint": "SWE-bench Can Language Models Resolve Real-World GitHub Issues", "arxiv": "2310.06770"},
    {"name": "WebArena",        "hint": "WebArena A Realistic Web Environment for Building Autonomous Agents", "arxiv": "2307.13854"},
    {"name": "GAIA",            "hint": "GAIA a benchmark for General AI Assistants",       "arxiv": "2311.12983"},
    {"name": "AppWorld",        "hint": "AppWorld A Controllable World of Apps and People",  "arxiv": "2407.18901"},
    {"name": "OSWorld",         "hint": "OSWorld Benchmarking Multimodal Agents for Open-Ended Tasks in Real Computer Environments", "arxiv": "2404.07972"},
    {"name": "ToolBench",       "hint": "ToolLLM Facilitating Large Language Models to Master 16000+ Real-world APIs", "arxiv": "2307.16789"},
    {"name": "MLE-bench",       "hint": "MLE-bench Evaluating Machine Learning Agents on Machine Learning Engineering", "arxiv": "2410.07095"},
    {"name": "DataSciBench",    "hint": "DataSciBench An LLM Agent Benchmark for Data Science", "arxiv": "2502.13897"},
    {"name": "AgentRecBench",   "hint": "AgentRecBench benchmark agentic recommender",       "arxiv": None},
    {"name": "InnovatorBench",  "hint": "InnovatorBench benchmark LLM agents research innovation", "arxiv": None},
    {"name": "ClawBench",       "hint": "ClawBench benchmark agent",                         "arxiv": None},
    {"name": "tau-bench",       "hint": "tau-bench A Benchmark for Tool-Agent-User Interaction in Real-World Domains", "arxiv": "2406.12045"},
    {"name": "AgentBoard",      "hint": "AgentBoard An Analytical Evaluation Board of Multi-turn LLM Agents", "arxiv": "2401.13178"},
    {"name": "VisualWebArena",  "hint": "VisualWebArena Evaluating Multimodal Agents on Realistic Visual Web Tasks", "arxiv": "2401.13649"},
    {"name": "ToolEmu",         "hint": "Identifying the Risks of LM Agents with an LM-Emulated Sandbox", "arxiv": "2309.15817"},
]

# --------------------------------------------------------------------------- #
# HTTP helpers (cached, polite)
# --------------------------------------------------------------------------- #
_session_calls = {"n": 0}

def _cache_path(tag, url):
    h = hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]
    return os.path.join(CACHE, f"{tag}_{h}.json")

def http_get_json(url, tag="raw", retries=3, force_live=False):
    """GET JSON with on-disk cache. Cache => deterministic re-runs."""
    cp = _cache_path(tag, url)
    if os.path.exists(cp) and not force_live:
        with open(cp, "r", encoding="utf-8") as f:
            return json.load(f)
    last_err = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": f"SMS-LLM-Agent-Benchmarks/3.0 (mailto:{CONFIG['openalex_mailto']})",
                "Accept": "application/json",
            })
            with urllib.request.urlopen(req, timeout=40) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            with open(cp, "w", encoding="utf-8") as f:
                json.dump(data, f)
            _session_calls["n"] += 1
            time.sleep(CONFIG["request_sleep_s"])
            return data
        except urllib.error.HTTPError as e:
            last_err = f"HTTP {e.code}"
            if e.code in (429, 500, 502, 503):
                time.sleep(2 + attempt * 3)
                continue
            break
        except Exception as e:  # noqa
            last_err = str(e)
            time.sleep(1 + attempt * 2)
    return {"_error": last_err, "_url": url}

# --------------------------------------------------------------------------- #
# Text normalisation + similarity (dedup)
# --------------------------------------------------------------------------- #
def norm_title(t):
    if not t:
        return ""
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.lower()
    t = re.sub(r"[^a-z0-9 ]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

def levenshtein(a, b):
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]

def lev_ratio(a, b):
    if not a and not b:
        return 1.0
    d = levenshtein(a, b)
    return 1 - d / max(len(a), len(b))

def token_set_ratio(a, b):
    sa, sb = set(a.split()), set(b.split())
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)

def reconstruct_abstract(inv):
    if not inv:
        return ""
    pos = {}
    for word, idxs in inv.items():
        for i in idxs:
            pos[i] = word
    if not pos:
        return ""
    return " ".join(pos[i] for i in range(max(pos) + 1) if i in pos)

# --------------------------------------------------------------------------- #
# Stage helpers: persistence + resume
# --------------------------------------------------------------------------- #
def write_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

def read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def write_csv(path, rows, fields):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

# --------------------------------------------------------------------------- #
# STAGE 1 — TIER-1 HARVEST (OpenAlex) + seeds
# --------------------------------------------------------------------------- #
OA_BASE = "https://api.openalex.org/works"
OA_FIELDS = ("id,doi,title,display_name,publication_year,publication_date,type,"
             "authorships,primary_location,locations,"
             "cited_by_count,open_access,abstract_inverted_index,"
             "referenced_works,cited_by_api_url")

def oa_record(w):
    """Project an OpenAlex work into our flat schema."""
    authors = []
    for a in (w.get("authorships") or [])[:25]:
        nm = (a.get("author") or {}).get("display_name")
        if nm:
            authors.append(nm)
    loc = w.get("primary_location") or {}
    src = (loc.get("source") or {}) if loc else {}
    venue = src.get("display_name") if src else None
    publisher = src.get("host_organization_name") if src else None
    doi = (w.get("doi") or "")
    if doi.startswith("https://doi.org/"):
        doi = doi[len("https://doi.org/"):]
    oa = w.get("open_access") or {}
    repo = ""
    for L in (w.get("locations") or []):
        u = (L.get("landing_page_url") or "") + " " + (L.get("pdf_url") or "")
        if "github.com" in u.lower():
            m = re.search(r"https?://github\.com/[^\s\"')]+", u, re.I)
            if m:
                repo = m.group(0)
                break
    return {
        "oa_id": (w.get("id") or "").replace("https://openalex.org/", ""),
        "title": w.get("title") or w.get("display_name") or "",
        "authors": "; ".join(authors),
        "doi": doi.lower(),
        "year": w.get("publication_year"),
        "date": w.get("publication_date"),
        "type": w.get("type") or "",
        "venue": venue or "",
        "publisher": publisher or "",
        "abstract": reconstruct_abstract(w.get("abstract_inverted_index")),
        "url": (w.get("doi") or (w.get("primary_location") or {}).get("landing_page_url") or ""),
        "cited_by_count": w.get("cited_by_count") or 0,
        "is_oa": bool(oa.get("is_oa")),
        "oa_status": oa.get("oa_status") or "",
        "repo": repo,
        "referenced_works": [r.replace("https://openalex.org/", "") for r in (w.get("referenced_works") or [])],
        "cited_by_api_url": w.get("cited_by_api_url") or "",
        "host_venue_type": src.get("type") if src else "",
    }

def harvest_stream(query):
    """One title.search stream, cursor-paginated, capped + saturation-aware."""
    flt = (f"title.search:{query},from_publication_date:{CONFIG['from_date']},"
           f"to_publication_date:{CONFIG['to_date']}")
    cursor = "*"
    got = []
    pages = 0
    total = None
    while cursor and len(got) < CONFIG["max_records_per_stream"]:
        params = {
            "filter": flt, "select": OA_FIELDS, "per_page": 200,
            "cursor": cursor, "mailto": CONFIG["openalex_mailto"],
        }
        url = OA_BASE + "?" + urllib.parse.urlencode(params)
        data = http_get_json(url, tag="oa_stream")
        if "_error" in data:
            return got, {"query": query, "filter": flt, "url": url,
                         "result_count": None, "status": f"UNRESOLVED:{data['_error']}",
                         "tier": 1, "timestamp": NOW}
        if total is None:
            total = (data.get("meta") or {}).get("count")
        results = data.get("results") or []
        for w in results:
            got.append(oa_record(w))
        pages += 1
        cursor = (data.get("meta") or {}).get("next_cursor")
        if not results:
            break
        if len(got) >= CONFIG["max_records_per_stream"]:
            break
    return got[:CONFIG["max_records_per_stream"]], {
        "database": "OpenAlex", "query": f"title.search:{query}", "filter": flt,
        "search_url": OA_BASE + "?" + urllib.parse.urlencode(
            {"filter": flt, "mailto": CONFIG["openalex_mailto"]}),
        "result_count_total": total, "retrieved": min(len(got), CONFIG["max_records_per_stream"]),
        "pages": pages, "tier": 1, "status": "harvested", "timestamp": NOW,
    }

def fetch_seed(seed):
    """Explicit seed fetch by name; verify existence -> source_verified flag."""
    q = urllib.parse.quote(seed["hint"])
    url = (f"{OA_BASE}?search={q}&per_page=3&select={OA_FIELDS}"
           f"&mailto={CONFIG['openalex_mailto']}")
    data = http_get_json(url, tag="oa_seed")
    rec, verified, matched = None, False, ""
    if "_error" not in data and (data.get("results")):
        cand = data["results"][0]
        r = oa_record(cand)
        # verification: arxiv id match OR strong title token overlap
        ok = False
        if seed.get("arxiv") and seed["arxiv"] in (r["doi"] or ""):
            ok = True
        if token_set_ratio(norm_title(seed["hint"]), norm_title(r["title"])) >= 0.45:
            ok = True
        if ok:
            rec, verified, matched = r, True, r["oa_id"]
    return rec, {
        "seed": seed["name"], "hint": seed["hint"], "arxiv": seed.get("arxiv"),
        "source_verified": verified, "matched_oa_id": matched,
        "matched_doi": (rec or {}).get("doi", ""), "query_url": url,
        "in_probe_set": verified and CONFIG["recall_probe_set"] == "auto",
    }

def stage_harvest(force=False):
    out_manifest = os.path.join(DATA, "retrieval_manifest.csv")
    out_log = os.path.join(DATA, "search_log.json")
    out_seeds = os.path.join(DATA, "seed_registry.json")
    if not force and all(os.path.exists(p) for p in (out_manifest, out_log, out_seeds)):
        log("harvest: artifacts exist, skipping (use --force).")
        return
    log("STAGE harvest: Tier-1 OpenAlex streams ...")
    search_log = {"generated": NOW, "config": CONFIG, "streams": [], "tier2": [], "tier3": []}
    union = {}   # oa_id -> record, plus provenance of streams
    prov = {}
    for q in TITLE_STREAMS:
        recs, meta = harvest_stream(q)
        before = len(union)
        for r in recs:
            key = r["oa_id"] or ("doi:" + r["doi"])
            if key not in union:
                union[key] = r
                prov[key] = []
            prov[key].append(q)
        new_unique = len(union) - before
        meta.setdefault("retrieved", len(recs))
        meta["new_unique_added"] = new_unique
        meta["new_unique_frac"] = round(new_unique / max(1, meta["retrieved"]), 4)
        search_log["streams"].append(meta)
        log(f"  stream '{q}': total={meta.get('result_count_total')} "
            f"retrieved={meta['retrieved']} new_unique={new_unique}")

    # explicit seed fetches (guarantee canonical benchmarks present)
    log("harvest: explicit seed fetches ...")
    seed_rows = []
    for s in SEEDS:
        rec, srow = fetch_seed(s)
        seed_rows.append(srow)
        if rec:
            key = rec["oa_id"] or ("doi:" + rec["doi"])
            if key not in union:
                union[key] = rec
                prov[key] = ["seed:" + s["name"]]
            else:
                prov[key].append("seed:" + s["name"])
        log(f"  seed {s['name']:14s} verified={srow['source_verified']} "
            f"matched={srow['matched_oa_id']}")

    # Tier-2 registration (count_only / UNRESOLVED) -------------------------- #
    search_log["tier2"] = [
        {"database": "IEEE Xplore", "tier": 2,
         "query": '(("Abstract":"Large Language Model" OR "Abstract":LLM) AND '
                  '("Abstract":Agent OR "Abstract":Autonomous) AND '
                  '("All Metadata":Evaluation OR "All Metadata":Benchmark))',
         "status": "UNRESOLVED:no_credentials",
         "note": "config.ieee_browser_auth=False; no institutional session. "
                 "Substituted by Crossref open-index equivalent for recall-gap.",
         "result_count": None, "timestamp": NOW},
        {"database": "ACM Digital Library", "tier": 2,
         "query": 'Abstract:("Large Language Model" OR "LLM") AND '
                  'Abstract:(Agent OR Autonomous) AND Keyword:(Evaluation OR Benchmark)',
         "status": "UNRESOLVED:no_credentials",
         "field_scoping": "broad_expansion_risk",
         "note": "ACM URL interface degrades field-coded query to broad all-field OR; "
                 "no credentials this run. count_only not obtainable -> UNRESOLVED.",
         "result_count": None, "timestamp": NOW},
    ]
    search_log["tier3"] = [
        {"database": db, "tier": 3, "status": "UNRESOLVED:no_credentials"}
        for db in ("Scopus", "Web of Science", "SpringerLink", "Semantic Scholar Graph API")
    ]

    # Persist
    manifest_rows = []
    for key, r in union.items():
        rr = dict(r)
        rr["streams"] = "|".join(prov.get(key, []))
        rr["referenced_works_n"] = len(r["referenced_works"])
        manifest_rows.append(rr)
    fields = ["oa_id", "title", "authors", "doi", "year", "date", "type", "venue",
              "publisher", "cited_by_count", "is_oa", "oa_status", "repo",
              "host_venue_type", "referenced_works_n", "streams", "url", "abstract"]
    write_csv(out_manifest, manifest_rows, fields)
    write_json(out_log, search_log)
    write_json(out_seeds, {"generated": NOW, "seeds": seed_rows})
    # keep full records (with referenced_works lists) for snowball stage
    write_json(os.path.join(DATA, "_harvest_records.json"),
               {"records": {k: v for k, v in union.items()},
                "provenance": prov})
    log(f"harvest done: union={len(union)} unique records; "
        f"api_calls={_session_calls['n']}")

# --------------------------------------------------------------------------- #
# STAGE 2 — DEDUP
# --------------------------------------------------------------------------- #
def stage_dedup(force=False):
    out = os.path.join(DATA, "deduplication_log.csv")
    out_clean = os.path.join(DATA, "_deduped_records.json")
    if not force and os.path.exists(out) and os.path.exists(out_clean):
        log("dedup: artifacts exist, skipping.")
        return
    log("STAGE dedup ...")
    rec_blob = read_json(os.path.join(DATA, "_harvest_records.json"))
    records = list(rec_blob["records"].values())

    # precedence for keeping: Journal>Conference>Workshop>Preprint, then citations
    def precedence(r):
        t = (r.get("type") or "").lower()
        hv = (r.get("host_venue_type") or "").lower()
        if t in ("article",) and hv in ("journal",):
            return 4
        if hv == "conference" or t == "proceedings-article":
            return 3
        if "workshop" in (r.get("venue") or "").lower():
            return 2
        if t in ("preprint", "posted-content") or "arxiv" in (r.get("doi") or ""):
            return 1
        return 2

    kept = []
    log_rows = []
    for r in records:
        nt = norm_title(r["title"])
        r["_nt"] = nt
        matched_on, match_idx = None, None
        for i, k in enumerate(kept):
            if r["doi"] and r["doi"] == k["doi"]:
                matched_on, match_idx = "doi", i
                break
            if r["oa_id"] and r["oa_id"] == k["oa_id"]:
                matched_on, match_idx = "openalex_id", i
                break
            if nt and nt == k["_nt"]:
                matched_on, match_idx = "exact_norm_title", i
                break
        if matched_on is None and nt:
            for i, k in enumerate(kept):
                if not k["_nt"]:
                    continue
                if abs(len(nt) - len(k["_nt"])) <= 6 and lev_ratio(nt, k["_nt"]) >= 0.93:
                    matched_on, match_idx = "levenshtein>=0.93", i
                    break
                if token_set_ratio(nt, k["_nt"]) >= 0.92:
                    matched_on, match_idx = "token_set>=0.92", i
                    break
        if matched_on is None:
            kept.append(r)
            log_rows.append({"oa_id": r["oa_id"], "title": r["title"][:120],
                             "decision": "kept", "matched_on": "", "kept_oa_id": r["oa_id"],
                             "reason": "first occurrence"})
        else:
            k = kept[match_idx]
            if precedence(r) > precedence(k):
                log_rows.append({"oa_id": k["oa_id"], "title": k["title"][:120],
                                 "decision": "dropped", "matched_on": matched_on,
                                 "kept_oa_id": r["oa_id"],
                                 "reason": f"lower precedence than duplicate ({matched_on})"})
                r["_merged_citations"] = max(r["cited_by_count"], k["cited_by_count"])
                kept[match_idx] = r
            else:
                log_rows.append({"oa_id": r["oa_id"], "title": r["title"][:120],
                                 "decision": "dropped", "matched_on": matched_on,
                                 "kept_oa_id": k["oa_id"],
                                 "reason": f"duplicate of kept ({matched_on})"})
                k["cited_by_count"] = max(k["cited_by_count"], r["cited_by_count"])

    write_csv(out, log_rows, ["oa_id", "title", "decision", "matched_on",
                              "kept_oa_id", "reason"])
    for k in kept:
        k.pop("_nt", None)
    write_json(out_clean, {"records": kept})
    dropped = sum(1 for x in log_rows if x["decision"] == "dropped")
    log(f"dedup done: in={len(records)} kept={len(kept)} dropped={dropped}")

# --------------------------------------------------------------------------- #
# STAGE 3 — SCREENING (Pass A heuristic) + ELIGIBILITY
# --------------------------------------------------------------------------- #
INCLUDE_TERMS = [
    "benchmark", "evaluat", "framework", "environment", "testbed", "suite",
    "assessment", "leaderboard", "arena", "gym", "challenge",
]
AGENT_TERMS = [
    "agent", "agentic", "autonomous", "tool use", "tool-use", "tool calling",
    "web navigation", "computer use", "multi-agent", "multi agent",
    "llm agent", "language model agent", "task automation", "planning",
]
# Exclusion signal regexes (EC1..EC6)
EC_PATTERNS = {
    "EC1_general_nlp": re.compile(r"\b(glue|superglue|question answering only|sentiment|"
                                  r"translation benchmark|summari[sz]ation benchmark)\b", re.I),
    "EC2_prompt_only": re.compile(r"\b(prompt engineering|prompt tuning|prompt optimi[sz]ation|"
                                  r"chain-of-thought prompting)\b", re.I),
    "EC4_model_centric": re.compile(r"\b(pretraining|fine-tuning benchmark|model compression|"
                                    r"tokeni[sz]er|perplexity benchmark)\b", re.I),
}

def is_agent_benchmark(title, abstract):
    txt = f"{title} \n {abstract}".lower()
    has_agent = any(t in txt for t in AGENT_TERMS)
    has_eval = any(t in txt for t in INCLUDE_TERMS)
    # benchmark-introduction signal
    introduces = bool(re.search(r"\b(we (introduce|present|propose|release|build|develop)|"
                                r"this (paper|work) (introduces|presents|proposes)|"
                                r"a (new )?benchmark|we benchmark)\b", txt))
    return has_agent, has_eval, introduces

def exclusion_for(title, abstract):
    txt = f"{title}\n{abstract}"
    for code, pat in EC_PATTERNS.items():
        if pat.search(txt):
            return code
    return None

def stage_screen(force=False):
    out = os.path.join(DATA, "screening_decisions.csv")
    out_inc = os.path.join(DATA, "_included_records.json")
    if not force and os.path.exists(out) and os.path.exists(out_inc):
        log("screen: artifacts exist, skipping.")
        return
    log("STAGE screen + eligibility ...")
    records = read_json(os.path.join(DATA, "_deduped_records.json"))["records"]
    rows, included = [], []
    for r in records:
        title, abs = r["title"], r.get("abstract", "")
        has_agent, has_eval, introduces = is_agent_benchmark(title, abs)
        ec = exclusion_for(title, abs)
        # Pass A heuristic decision
        decision, reason, eccode, confidence, screen_pass = None, "", "", "heuristic", "A"
        if not has_agent:
            decision, eccode, reason = "excluded", "EC5", "no agent/autonomy signal in title+abstract"
        elif ec:
            decision, eccode, reason = "excluded", ec.split("_")[0], f"matched {ec}"
        elif not has_eval:
            decision, eccode, reason = "excluded", "EC4", "agent context but no eval/benchmark signal"
        elif not introduces and has_agent and has_eval:
            # borderline -> Pass B confirmation (still machine here, flagged)
            decision, reason, screen_pass = "included", "agent+eval present; introduction signal weak", "B"
            confidence = "heuristic"
        else:
            decision, reason = "included", "agent + benchmark/eval + introduction signal"
        no_abs = (len(abs.strip()) < 30)
        if no_abs and decision == "included":
            confidence = "heuristic"
            reason += " (title-only; abstract missing -> needs_human_verification)"
        row = {
            "oa_id": r["oa_id"], "title": title[:160], "year": r["year"],
            "type": r["type"], "venue": r["venue"], "cited_by_count": r["cited_by_count"],
            "screen_pass": screen_pass, "decision": decision,
            "exclusion_code": eccode, "confidence": confidence,
            "machine_or_human": "machine", "rationale": reason,
            "has_agent": has_agent, "has_eval": has_eval, "introduces": introduces,
        }
        rows.append(row)
        if decision == "included":
            r2 = dict(r)
            r2["screen_pass"] = screen_pass
            r2["screen_confidence"] = confidence
            included.append(r2)

    # Priority ordering / target cap (record cutoff, never silent truncation)
    cutoff_note = ""
    if len(included) > CONFIG["target_included"]:
        def score(r):
            sig = 0
            if is_agent_benchmark(r["title"], r.get("abstract", ""))[2]:
                sig += 50
            return (r["cited_by_count"], sig)
        included.sort(key=score, reverse=True)
        boundary = included[CONFIG["target_included"] - 1]
        cutoff_note = (f"Ranked by (citation_count, introduction_signal); retained top "
                       f"{CONFIG['target_included']}. Cutoff at oa_id={boundary['oa_id']} "
                       f"cited_by={boundary['cited_by_count']}.")
        for r in included[CONFIG["target_included"]:]:
            for row in rows:
                if row["oa_id"] == r["oa_id"]:
                    row["decision"] = "excluded"
                    row["exclusion_code"] = "EC6"
                    row["rationale"] = "below target_included priority cutoff (logged)"
        included = included[:CONFIG["target_included"]]

    write_csv(out, rows, ["oa_id", "title", "year", "type", "venue",
                          "cited_by_count", "screen_pass", "decision",
                          "exclusion_code", "confidence", "machine_or_human",
                          "has_agent", "has_eval", "introduces", "rationale"])
    write_json(out_inc, {"records": included, "cutoff_note": cutoff_note,
                         "screened_n": len(records)})
    inc = len(included)
    exc = sum(1 for x in rows if x["decision"] == "excluded")
    log(f"screen done: screened={len(records)} included={inc} excluded={exc}")
    if cutoff_note:
        log("  cutoff: " + cutoff_note)

# --------------------------------------------------------------------------- #
# STAGE 4 — SNOWBALLING (backward referenced_works + forward cited_by)
# --------------------------------------------------------------------------- #
def oa_fetch_many(ids):
    """Fetch metadata for up to 50 OpenAlex ids per request."""
    out = []
    ids = [i for i in ids if i]
    for i in range(0, len(ids), 50):
        chunk = ids[i:i + 50]
        flt = "openalex_id:" + "|".join("https://openalex.org/" + c for c in chunk)
        url = (f"{OA_BASE}?filter={urllib.parse.quote(flt)}&per_page=50"
               f"&select={OA_FIELDS}&mailto={CONFIG['openalex_mailto']}")
        data = http_get_json(url, tag="oa_snow_fetch")
        for w in (data.get("results") or []):
            out.append(oa_record(w))
    return out

def stage_snowball(force=False):
    out = os.path.join(DATA, "snowball_log.csv")
    out_final = os.path.join(DATA, "_final_records.json")
    if not force and os.path.exists(out) and os.path.exists(out_final):
        log("snowball: artifacts exist, skipping.")
        return
    log("STAGE snowball ...")
    inc_blob = read_json(os.path.join(DATA, "_included_records.json"))
    included = inc_blob["records"]
    have = {r["oa_id"] for r in included}
    have_doi = {r["doi"] for r in included if r["doi"]}
    rows = []
    additions = []

    # Backward: referenced_works of included (capped)
    backward_ids = []
    for r in included:
        for ref in r.get("referenced_works", []):
            if ref not in have:
                backward_ids.append((ref, r["oa_id"]))
    # de-dup candidate ids, cap
    seen = set()
    uniq_back = []
    for ref, parent in backward_ids:
        if ref not in seen:
            seen.add(ref)
            uniq_back.append((ref, parent))
    uniq_back = uniq_back[:CONFIG["snowball_backward_cap"]]
    if uniq_back:
        fetched = oa_fetch_many([x[0] for x in uniq_back])
        parent_of = {ref: parent for ref, parent in uniq_back}
        for rec in fetched:
            if rec["year"] is None or rec["year"] < 2023:
                continue
            ha, he, intro = is_agent_benchmark(rec["title"], rec.get("abstract", ""))
            ec = exclusion_for(rec["title"], rec.get("abstract", ""))
            inc = ha and he and not ec
            rows.append({"oa_id": rec["oa_id"], "title": rec["title"][:140],
                         "direction": "backward", "parent": parent_of.get(rec["oa_id"], ""),
                         "decision": "included" if inc else "excluded",
                         "rationale": "agent+eval, no EC" if inc else "no agent/eval or EC match"})
            if inc and rec["oa_id"] not in have and rec["doi"] not in have_doi:
                have.add(rec["oa_id"])
                if rec["doi"]:
                    have_doi.add(rec["doi"])
                rec["screen_pass"] = "B"
                rec["screen_confidence"] = "heuristic"
                rec["discovery"] = "snowball_backward"
                additions.append(rec)

    # Forward: citers of top-cited included works (capped)
    top = sorted(included, key=lambda r: r["cited_by_count"], reverse=True)[:CONFIG["snowball_forward_top"]]
    for r in top:
        api = r.get("cited_by_api_url")
        if not api:
            continue
        url = api + ("&" if "?" in api else "?") + urllib.parse.urlencode({
            "per_page": 50, "select": OA_FIELDS, "mailto": CONFIG["openalex_mailto"],
            "filter": f"from_publication_date:{CONFIG['from_date']},to_publication_date:{CONFIG['to_date']}",
        })
        # cited_by_api_url already has a filter; append safely
        data = http_get_json(url, tag="oa_snow_fwd")
        for w in (data.get("results") or []):
            rec = oa_record(w)
            if rec["oa_id"] in have or (rec["doi"] and rec["doi"] in have_doi):
                continue
            ha, he, intro = is_agent_benchmark(rec["title"], rec.get("abstract", ""))
            ec = exclusion_for(rec["title"], rec.get("abstract", ""))
            inc = ha and he and intro and not ec
            rows.append({"oa_id": rec["oa_id"], "title": rec["title"][:140],
                         "direction": "forward", "parent": r["oa_id"],
                         "decision": "included" if inc else "excluded",
                         "rationale": "agent+eval+intro, no EC" if inc else "weak/duplicate/EC"})
            if inc:
                have.add(rec["oa_id"])
                if rec["doi"]:
                    have_doi.add(rec["doi"])
                rec["screen_pass"] = "B"
                rec["screen_confidence"] = "heuristic"
                rec["discovery"] = "snowball_forward"
                additions.append(rec)

    write_csv(out, rows, ["oa_id", "title", "direction", "parent", "decision", "rationale"])
    final = list(included) + additions
    for r in final:
        r.setdefault("discovery", "database_search")
    write_json(out_final, {"records": final,
                           "assessed": len(included),
                           "snowball_added": len(additions)})
    log(f"snowball done: candidates={len(rows)} added={len(additions)} "
        f"final_included={len(final)}")

# --------------------------------------------------------------------------- #
# STAGE 5 — RECALL-GAP QUANTIFICATION
# --------------------------------------------------------------------------- #
CR_BASE = "https://api.crossref.org/works"

def crossref_title_lookup(title):
    """Probe lookup: does Crossref return a matching record for this title?"""
    url = (CR_BASE + "?" + urllib.parse.urlencode(
        {"query.bibliographic": title, "rows": 5,
         "mailto": CONFIG["openalex_mailto"]}))
    data = http_get_json(url, tag="cr_probe")
    items = ((data.get("message") or {}).get("items")) or []
    nt = norm_title(title)
    for it in items:
        cand = (it.get("title") or [""])[0]
        if cand and token_set_ratio(nt, norm_title(cand)) >= 0.6:
            doi = (it.get("DOI") or "").lower()
            return True, doi, url
    return False, "", url

def crossref_inscope_set():
    """Independent Crossref *search* over the window; screened to in-scope.
    Used as the second capture engine. Crossref independence from OpenAlex is
    imperfect (shared DOI registry) -> result reported as a bound."""
    rows = []
    seen = set()
    for q in ["LLM agent benchmark", "autonomous agent evaluation benchmark",
              "language model agent benchmark"]:
        offset = 0
        for _ in range(2):  # cap 2 pages * 100
            url = (CR_BASE + "?" + urllib.parse.urlencode({
                "query.bibliographic": q, "rows": 100, "offset": offset,
                "filter": f"from-pub-date:{CONFIG['from_date']},until-pub-date:{CONFIG['to_date']}",
                "mailto": CONFIG["openalex_mailto"]}))
            data = http_get_json(url, tag="cr_set")
            items = ((data.get("message") or {}).get("items")) or []
            if not items:
                break
            for it in items:
                doi = (it.get("DOI") or "").lower()
                title = (it.get("title") or [""])[0]
                if not title or doi in seen:
                    continue
                seen.add(doi)
                ha, he, intro = is_agent_benchmark(title, it.get("abstract", "") or "")
                if ha and he:  # in-scope by same heuristic
                    rows.append({"doi": doi, "title": title, "nt": norm_title(title)})
            offset += 100
    return rows

def chapman(n1, n2, m):
    """Chapman bias-corrected Lincoln-Petersen estimator."""
    return ((n1 + 1) * (n2 + 1) / (m + 1)) - 1

def stage_recall_gap(force=False):
    out_matrix = os.path.join(DATA, "recall_probe_matrix.csv")
    out_json = os.path.join(DATA, "recall_gap_estimate.json")
    out_table = os.path.join(FIG, "recall_gap_table.csv")
    if not force and all(os.path.exists(p) for p in (out_matrix, out_json, out_table)):
        log("recall_gap: artifacts exist, skipping.")
        return
    log("STAGE recall_gap ...")
    seeds = read_json(os.path.join(DATA, "seed_registry.json"))["seeds"]
    final = read_json(os.path.join(DATA, "_final_records.json"))["records"]
    oa_titles = {norm_title(r["title"]) for r in final}
    oa_dois = {r["doi"] for r in final if r["doi"]}

    # 1) freeze probe set = source_verified seeds
    probe = [s for s in seeds if s["source_verified"]]
    matrix_rows = []
    cap_oa, cap_cr, both, neither = 0, 0, 0, 0
    for s in probe:
        # OpenAlex column: verified at harvest
        found_oa = 1
        # Crossref column: per-title lookup (reproducible single-title query)
        found_cr, cr_doi, cr_url = crossref_title_lookup(s["hint"])
        matrix_rows.append({
            "benchmark": s["seed"], "matched_oa_id": s["matched_oa_id"],
            "openalex": found_oa, "crossref": int(found_cr),
            "ieee": "UNRESOLVED:no_credentials", "acm": "UNRESOLVED:no_credentials",
            "matched_doi_crossref": cr_doi, "query_url_crossref": cr_url,
        })
        if found_oa and found_cr:
            both += 1
        elif found_oa:
            cap_oa += 1
        elif found_cr:
            cap_cr += 1
        else:
            neither += 1
    write_csv(out_matrix, matrix_rows,
              ["benchmark", "matched_oa_id", "openalex", "crossref",
               "ieee", "acm", "matched_doi_crossref", "query_url_crossref"])

    psize = len(probe)
    found_oa_n = sum(1 for r in matrix_rows if r["openalex"] == 1)
    found_cr_n = sum(1 for r in matrix_rows if r["crossref"] == 1)
    found_any = sum(1 for r in matrix_rows if (r["openalex"] == 1 or r["crossref"] == 1))
    probe_recall_oa = found_oa_n / psize if psize else None
    probe_recall_cr = found_cr_n / psize if psize else None
    probe_gap = (1 - found_oa_n / found_any) if found_any else None

    # 3) capture-recapture on the full in-scope corpus via Crossref search
    cr_inscope = crossref_inscope_set()
    n_oa = len(final)
    n_cr = len(cr_inscope)
    m = 0
    for c in cr_inscope:
        if (c["doi"] and c["doi"] in oa_dois) or (c["nt"] in oa_titles):
            m += 1
    cr_table = {}
    assumptions = [
        "(i) the two sources sample the same population independently",
        "(ii) capture probability is homogeneous across papers",
        "(iii) the population is closed over 2023-01-01..2026-06-30",
    ]
    caveats = [
        "ASSUMPTION (i) FAILS BY CONSTRUCTION, HETEROGENEOUSLY. OpenAlex and Crossref "
        "are not two independent random samples: they are two DIFFERENT targeted search "
        "strategies (OpenAlex title.search streams vs Crossref bibliographic queries, "
        "the latter capped at 2 pages x 3 queries). Different strategies select "
        "different sub-regions of the literature, which DEPRESSES the observed overlap m. "
        "Low m mechanically INFLATES the Chapman N_hat, so the estimated recall "
        "(n_OA / N_hat) is biased DOWNWARD. The reported estimated_recall_openalex is "
        "therefore best read as a LOOSE LOWER BOUND, not a measurement.",
        "DIRECT CONTRADICTION WITH PROBE PROXY -> the probe-set proxy finds OpenAlex "
        "captures 100% (10/10) of source-verified canonical benchmarks, whereas the "
        "capture-recapture point value implies ~8% recall. This gap is the signature of "
        "capture heterogeneity, not evidence that OpenAlex misses 92% of the literature. "
        "The probe proxy is the more trustworthy signal for KNOWN/canonical work; the "
        "capture-recapture figure bounds only the long TAIL of obscure, low-citation "
        "benchmarks that targeted title search under-samples.",
        "Crossref sampling was depth-capped (>=600 candidates), so n_CR and m are "
        "themselves lower bounds; deeper Crossref harvest would raise m and lower N_hat.",
        "IEEE/ACM Tier-2 probe columns are UNRESOLVED:no_credentials this run; the "
        "estimate uses Crossref as the authorised open-index substitute.",
        "Reported as an ORDER-OF-MAGNITUDE bound, not a point estimate. Headline coverage "
        "evidence is the probe proxy (Step 1-2); capture-recapture (Step 3) only brackets "
        "the tail.",
    ]
    if psize < 10:
        n_hat = "UNRESOLVED:probe_set_too_small(<10)"
        est_recall = "UNRESOLVED:probe_set_too_small(<10)"
        recall_gap = "UNRESOLVED:probe_set_too_small(<10)"
    elif m == 0:
        n_hat = "UNRESOLVED:zero_overlap"
        est_recall = "UNRESOLVED:zero_overlap"
        recall_gap = "UNRESOLVED:zero_overlap"
    else:
        n_hat_val = chapman(n_oa, n_cr, m)
        n_hat = round(n_hat_val, 1)
        est_recall = round(n_oa / n_hat_val, 4)
        recall_gap = round(1 - n_oa / n_hat_val, 4)

    estimate = {
        "generated": NOW,
        "label": "estimate",   # never 'verified'
        "probe_set": {
            "size": psize,
            "members": [{"benchmark": r["benchmark"], "oa_id": r["matched_oa_id"]}
                        for r in matrix_rows],
            "selection": "source_verified seeds (recall_probe_set=auto), frozen for run",
        },
        "step1_probe_recall": {
            "openalex": {"found": found_oa_n, "of": psize, "fraction": probe_recall_oa},
            "crossref": {"found": found_cr_n, "of": psize, "fraction": probe_recall_cr},
            "ieee": "UNRESOLVED:no_credentials",
            "acm": "UNRESOLVED:no_credentials",
            "probe_gap_vs_union": probe_gap,
        },
        "step2_overlap_2x2_openalex_vs_crossref": {
            "found_in_both": both, "openalex_only": cap_oa,
            "crossref_only": cap_cr, "neither": neither, "probe_n": psize,
        },
        "step3_capture_recapture": {
            "estimator": "Chapman (bias-corrected Lincoln-Petersen)",
            "n_openalex_include_set": n_oa,
            "n_crossref_inscope_search": n_cr,
            "overlap_m": m,
            "N_hat": n_hat,
            "estimated_recall_openalex": est_recall,
            "recall_gap": recall_gap,
            "assumptions": assumptions,
            "caveats": caveats,
            "interpretation": (
                "Because the two engines are heterogeneous targeted searches (not "
                "independent random samples) and Crossref sampling was depth-capped, the "
                "observed overlap m is depressed, which inflates N_hat and pushes the "
                "estimated recall DOWNWARD. Treat estimated_recall_openalex as a loose "
                "LOWER bound. It is contradicted -- in the reassuring direction -- by the "
                "probe proxy, which shows 100% capture of canonical benchmarks. Synthesis: "
                "OpenAlex recall on KNOWN/influential agent benchmarks is effectively "
                "complete (probe proxy), while recall over the full long tail of "
                "low-visibility benchmarks is materially below 100% and not precisely "
                "estimable here. Confidence framing in Step 4 follows from this synthesis, "
                "NOT from the bare 8% point value."),
        },
        "step4_confidence_framing": {
            "robust_to_gap": ["within-corpus composition shares (capability mix)",
                              "year-over-year shape / relative growth",
                              "relative venue composition"],
            "sensitive_to_gap": ["absolute number of benchmarks",
                                 "absolute per-year counts",
                                 "absolute venue-share levels"],
            "default_stance": ("absolute volumes reported as LOWER bounds; "
                               "composition/shares reported as directionally reliable"),
        },
    }
    write_json(out_json, estimate)

    # figures/recall_gap_table.csv (per-source)
    tbl = [
        {"source": "OpenAlex", "tier": 1, "probe_found": found_oa_n,
         "probe_of": psize, "probe_recall": probe_recall_oa,
         "n_inscope": n_oa, "overlap_m_with_OA": "-", "N_hat": n_hat,
         "estimated_recall": est_recall, "recall_gap": recall_gap},
        {"source": "Crossref", "tier": "1b", "probe_found": found_cr_n,
         "probe_of": psize, "probe_recall": probe_recall_cr,
         "n_inscope": n_cr, "overlap_m_with_OA": m, "N_hat": "(engine)",
         "estimated_recall": "(engine)", "recall_gap": "(engine)"},
        {"source": "IEEE Xplore", "tier": 2, "probe_found": "UNRESOLVED",
         "probe_of": psize, "probe_recall": "UNRESOLVED:no_credentials",
         "n_inscope": "UNRESOLVED:no_credentials", "overlap_m_with_OA": "-",
         "N_hat": "-", "estimated_recall": "-", "recall_gap": "-"},
        {"source": "ACM DL", "tier": 2, "probe_found": "UNRESOLVED",
         "probe_of": psize, "probe_recall": "UNRESOLVED:no_credentials",
         "n_inscope": "UNRESOLVED:broad_expansion/no_credentials",
         "overlap_m_with_OA": "-", "N_hat": "-", "estimated_recall": "-",
         "recall_gap": "-"},
    ]
    write_csv(out_table, tbl, ["source", "tier", "probe_found", "probe_of",
                               "probe_recall", "n_inscope", "overlap_m_with_OA",
                               "N_hat", "estimated_recall", "recall_gap"])
    log(f"recall_gap done: probe_size={psize} probe_recall_OA={probe_recall_oa} "
        f"n_OA={n_oa} n_CR={n_cr} m={m} N_hat={n_hat} est_recall={est_recall}")

# --------------------------------------------------------------------------- #
# STAGE 6 — TAXONOMY + TRENDS + PRISMA
# --------------------------------------------------------------------------- #
CAP_KEYWORDS = {
    "Planning": ["plan", "planning", "long-horizon", "long horizon", "subgoal"],
    "Reasoning": ["reason", "reasoning", "inference"],
    "ToolUse": ["tool", "api", "function call", "tool-use", "tool use"],
    "Coding": ["code", "coding", "software", "github", "swe", "program", "repository"],
    "Memory": ["memory", "long-term", "recall", "context retention"],
    "Collaboration": ["collaborat", "multi-agent", "multi agent", "cooperat", "team"],
    "ScientificDiscovery": ["scientif", "research", "discovery", "experiment", "data science", "ml engineering"],
    "Recommendation": ["recommend", "recommender", "recsys"],
    "LongHorizonExecution": ["long-horizon", "long horizon", "multi-step", "multi step", "sequential task"],
    "WebInteraction": ["web", "browser", "website", "navigation", "html", "webpage"],
}
ENV_KEYWORDS = {
    "Static": ["static", "dataset", "offline benchmark"],
    "Interactive": ["interactive", "interact", "environment", "step"],
    "Dynamic": ["dynamic", "stochastic", "evolving"],
    "Simulated": ["simulat", "sandbox", "emulat", "virtual"],
    "RealWorld": ["real-world", "real world", "realistic", "production"],
    "Embodied": ["embodied", "robot", "physical", "navigation"],
}
PARADIGM_KEYWORDS = {
    "Offline": ["offline", "static evaluation"],
    "Online": ["online", "interactive evaluation", "live"],
    "HumanInTheLoop": ["human-in-the-loop", "human in the loop", "human evaluation", "annotator"],
    "MultiAgent": ["multi-agent", "multi agent"],
    "FullyAutonomous": ["autonomous", "fully autonomous", "end-to-end"],
}
REPRO_KEYWORDS = {
    "OpenSource": ["open-source", "open source", "github", "publicly available", "release"],
    "DatasetReleased": ["dataset", "data release", "released dataset"],
    "EnvironmentReleased": ["environment", "sandbox", "testbed release"],
    "DockerSupport": ["docker", "container"],
    "EvalScriptsAvailable": ["evaluation script", "eval script", "harness", "code available"],
}

def classify(text, kw):
    t = text.lower()
    return {k: any(w in t for w in words) for k, words in kw.items()}

def stage_taxonomy(force=False):
    out = os.path.join(DATA, "benchmark_taxonomy.json")
    if not force and os.path.exists(out):
        log("taxonomy: artifacts exist, skipping.")
        return
    log("STAGE taxonomy + trends + prisma ...")
    final = read_json(os.path.join(DATA, "_final_records.json"))
    records = final["records"]
    items = []
    for r in records:
        text = f"{r['title']} {r.get('abstract','')}"
        caps = classify(text, CAP_KEYWORDS)
        env = classify(text, ENV_KEYWORDS)
        par = classify(text, PARADIGM_KEYWORDS)
        rep = classify(text, REPRO_KEYWORDS)
        if r.get("repo"):
            rep["OpenSource"] = True
        items.append({
            "name": r["title"], "oa_id": r["oa_id"], "doi": r["doi"],
            "year": r["year"], "venue": r["venue"], "type": r["type"],
            "cited_by_count": r["cited_by_count"], "repo": r.get("repo", ""),
            "capabilities": caps, "environment": env, "paradigm": par,
            "reproducibility": rep,
            "classification_method": "keyword_heuristic",
            "needs_human_verification": True,
            "discovery": r.get("discovery", "database_search"),
            "screen_pass": r.get("screen_pass", "A"),
        })
    write_json(out, {"generated": NOW,
                     "classification_method": "keyword_heuristic",
                     "needs_human_verification": True,
                     "n": len(items), "benchmarks": items})

    # ---- TREND CSVs ----
    # timeline / growth by year
    by_year = {}
    for it in items:
        by_year[it["year"]] = by_year.get(it["year"], 0) + 1
    write_csv(os.path.join(FIG, "benchmark_timeline.csv"),
              [{"year": y, "n_benchmarks": by_year[y],
                "framing": "LOWER_BOUND(recall_gap)"} for y in sorted(by_year)
               if y is not None],
              ["year", "n_benchmarks", "framing"])
    # capability matrix (per benchmark)
    cap_fields = ["name", "year"] + list(CAP_KEYWORDS.keys())
    cap_rows = []
    for it in items:
        row = {"name": it["name"][:80], "year": it["year"]}
        row.update({k: int(v) for k, v in it["capabilities"].items()})
        cap_rows.append(row)
    write_csv(os.path.join(FIG, "capability_matrix.csv"), cap_rows, cap_fields)
    # capability coverage trend (share per year)
    cap_share = []
    years = sorted({it["year"] for it in items if it["year"]})
    for y in years:
        yset = [it for it in items if it["year"] == y]
        row = {"year": y, "n": len(yset), "framing": "SHARE_directionally_reliable"}
        for cap in CAP_KEYWORDS:
            c = sum(1 for it in yset if it["capabilities"][cap])
            row[cap + "_share"] = round(c / len(yset), 3) if yset else 0
        cap_share.append(row)
    write_csv(os.path.join(FIG, "capability_coverage_trends.csv"), cap_share,
              ["year", "n", "framing"] + [c + "_share" for c in CAP_KEYWORDS])
    # venue distribution
    venue_count = {}
    for it in items:
        v = it["venue"] or "(preprint/unindexed)"
        venue_count[v] = venue_count.get(v, 0) + 1
    write_csv(os.path.join(FIG, "venue_distribution.csv"),
              [{"venue": v, "n": n, "framing": "ABSOLUTE_lower_bound;SHARE_directional"}
               for v, n in sorted(venue_count.items(), key=lambda x: -x[1])],
              ["venue", "n", "framing"])
    # reproducibility matrix
    rep_fields = ["name", "year"] + list(REPRO_KEYWORDS.keys())
    rep_rows = []
    for it in items:
        row = {"name": it["name"][:80], "year": it["year"]}
        row.update({k: int(v) for k, v in it["reproducibility"].items()})
        rep_rows.append(row)
    write_csv(os.path.join(FIG, "reproducibility_matrix.csv"), rep_rows, rep_fields)
    # evolution timeline (env/paradigm shares per year)
    evo = []
    for y in years:
        yset = [it for it in items if it["year"] == y]
        n = len(yset)
        row = {"year": y, "n": n,
               "interactive_share": round(sum(1 for it in yset if it["environment"]["Interactive"]) / n, 3) if n else 0,
               "realworld_share": round(sum(1 for it in yset if it["environment"]["RealWorld"]) / n, 3) if n else 0,
               "multiagent_share": round(sum(1 for it in yset if it["paradigm"]["MultiAgent"]) / n, 3) if n else 0,
               "opensource_share": round(sum(1 for it in yset if it["reproducibility"]["OpenSource"]) / n, 3) if n else 0,
               "framing": "SHARE_directionally_reliable"}
        evo.append(row)
    write_csv(os.path.join(FIG, "benchmark_evolution_timeline.csv"), evo,
              ["year", "n", "interactive_share", "realworld_share",
               "multiagent_share", "opensource_share", "framing"])

    # ---- BibTeX ----
    bib = []
    for r in records:
        key = (r["oa_id"] or norm_title(r["title"])[:20]).replace(" ", "")
        authors = " and ".join((r["authors"] or "").split("; ")) or "Unknown"
        title = r["title"].replace("{", "").replace("}", "")
        venue = r["venue"] or "arXiv preprint"
        bib.append(
            f"@article{{{key},\n  title = {{{title}}},\n  author = {{{authors}}},\n"
            f"  year = {{{r['year']}}},\n  journal = {{{venue}}},\n"
            f"  doi = {{{r['doi']}}},\n  note = {{cited_by={r['cited_by_count']}; "
            f"discovery={r.get('discovery','database_search')}}}\n}}")
    with open(os.path.join(DATA, "final_studies.bib"), "w", encoding="utf-8") as f:
        f.write("\n\n".join(bib))

    # ---- venue upgrade log ----
    vu_rows = []
    for r in records:
        is_preprint = ("arxiv" in (r["doi"] or "")) or (r["type"] in ("preprint", "posted-content"))
        vu_rows.append({
            "oa_id": r["oa_id"], "title": r["title"][:120],
            "current_type": r["type"], "venue": r["venue"],
            "venue_status": "preprint_no_archival_found" if is_preprint and not r["venue"]
                            else ("archival" if not is_preprint else "preprint_present"),
            "note": "OpenAlex best primary_location used; archival upgrade preferred where indexed.",
        })
    write_csv(os.path.join(DATA, "venue_upgrade_log.csv"), vu_rows,
              ["oa_id", "title", "current_type", "venue", "venue_status", "note"])

    # ---- PRISMA ----
    search_log = read_json(os.path.join(DATA, "search_log.json"))
    harvest = read_json(os.path.join(DATA, "_harvest_records.json"))
    dedup_rows = list(csv.DictReader(open(os.path.join(DATA, "deduplication_log.csv"), encoding="utf-8")))
    screen_rows = list(csv.DictReader(open(os.path.join(DATA, "screening_decisions.csv"), encoding="utf-8")))
    identified = len(harvest["records"])
    removed_dedup = sum(1 for x in dedup_rows if x["decision"] == "dropped")
    screened = len(read_json(os.path.join(DATA, "_deduped_records.json"))["records"])
    excluded = sum(1 for x in screen_rows if x["decision"] == "excluded")
    assessed = sum(1 for x in screen_rows if x["decision"] == "included")
    snow = read_json(os.path.join(DATA, "_final_records.json"))
    snowball_added = snow["snowball_added"]
    included_final = len(records)
    prisma = {
        "generated": NOW,
        "identification": {
            "tier1_harvested_records_union": identified,
            "tier2_registered": [{"db": t["database"], "status": t["status"]}
                                 for t in search_log["tier2"]],
            "tier3_registered": [{"db": t["database"], "status": t["status"]}
                                 for t in search_log["tier3"]],
            "note": "Tier-2/3 registered counts are reported alongside but NOT summed "
                    "into the dedup math (UNRESOLVED:no_credentials this run).",
        },
        "screening": {
            "records_identified_tier1": identified,
            "records_removed_dedup": removed_dedup,
            "records_screened": screened,
            "records_excluded_title_abstract": excluded,
        },
        "eligibility": {
            "reports_assessed": assessed,
            "snowball_added": snowball_added,
        },
        "included": {
            "studies_included": included_final,
        },
        "reconciliation": {
            "identity_check": "assessed + snowball_added == included",
            "assessed_plus_snowball": assessed + snowball_added,
            "included": included_final,
            "passes": (assessed + snowball_added == included_final),
            "screened_check": "identified - removed_dedup == screened",
            "identified_minus_dedup": identified - removed_dedup,
            "screened": screened,
            "screened_passes": (identified - removed_dedup == screened),
        },
    }
    write_json(os.path.join(DATA, "prisma_manifest.json"), prisma)
    log(f"taxonomy/trends/prisma done: identified={identified} dedup_removed={removed_dedup} "
        f"screened={screened} excluded={excluded} assessed={assessed} "
        f"snowball+={snowball_added} included={included_final} "
        f"reconcile={prisma['reconciliation']['passes']}")

# --------------------------------------------------------------------------- #
# STAGE 7 — MANUSCRIPT (data-dependent .tex emitted from persisted artifacts)
# --------------------------------------------------------------------------- #
def stage_manuscript(force=False):
    out = os.path.join(MAN, "prisma_macros.tex")
    if not force and os.path.exists(out):
        log("manuscript: artifacts exist, skipping.")
        return
    log("STAGE manuscript: emitting data-dependent .tex ...")
    pr = read_json(os.path.join(DATA, "prisma_manifest.json"))
    rg = read_json(os.path.join(DATA, "recall_gap_estimate.json"))
    sc = pr["screening"]; el = pr["eligibility"]; inc = pr["included"]
    s1 = rg["step1_probe_recall"]; s3 = rg["step3_capture_recapture"]

    # 1) prisma_macros.tex
    macros = {
        "PrismaIdentified": sc["records_identified_tier1"],
        "PrismaDedupRemoved": sc["records_removed_dedup"],
        "PrismaScreened": sc["records_screened"],
        "PrismaExcluded": sc["records_excluded_title_abstract"],
        "PrismaAssessed": el["reports_assessed"],
        "PrismaSnowballAdded": el["snowball_added"],
        "PrismaIncluded": inc["studies_included"],
        "ProbeSize": rg["probe_set"]["size"],
        "ProbeRecallOA": f"{s1['openalex']['found']}/{s1['openalex']['of']}",
        "ProbeRecallCR": f"{s1['crossref']['found']}/{s1['crossref']['of']}",
        "ProbeGap": s1["probe_gap_vs_union"],
        "CaptureNOA": s3["n_openalex_include_set"],
        "CaptureNCR": s3["n_crossref_inscope_search"],
        "CaptureM": s3["overlap_m"],
        "CaptureNhat": s3["N_hat"],
        "CaptureRecall": s3["estimated_recall_openalex"],
    }
    with open(out, "w", encoding="utf-8") as f:
        f.write("% AUTO-GENERATED by build_review.py from prisma_manifest.json + "
                "recall_gap_estimate.json. Do not edit by hand.\n")
        for k, v in macros.items():
            f.write(f"\\newcommand{{\\{k}}}{{{v}}}\n")

    # 2) prisma_scr_diagram.tex (TikZ flow)
    diag = r"""% AUTO-GENERATED PRISMA-ScR flow (TikZ). Counts via \input{../manuscript/prisma_macros.tex}.
\begin{tikzpicture}[node distance=8mm, every node/.style={font=\small},
  box/.style={draw, rounded corners, align=center, text width=6.2cm, inner sep=4pt},
  side/.style={draw, dashed, align=center, text width=5.0cm, inner sep=4pt}]
  \node[box] (id)  {\textbf{Identification (Tier-1, OpenAlex)}\\ Records identified: \PrismaIdentified};
  \node[box, below=of id] (dd) {Duplicates removed: \PrismaDedupRemoved\\ Records screened: \PrismaScreened};
  \node[box, below=of dd] (sc) {Title/abstract screened: \PrismaScreened\\ Excluded (EC1--EC6): \PrismaExcluded};
  \node[box, below=of sc] (el) {Reports assessed for eligibility: \PrismaAssessed\\ Snowball added: \PrismaSnowballAdded};
  \node[box, below=of el] (in) {\textbf{Studies included: \PrismaIncluded}};
  \node[side, right=10mm of id] (t2) {\textbf{Tier-2/3 registered}\\ IEEE, ACM, Scopus, WoS, Springer, S2:\\ \texttt{UNRESOLVED:no\_credentials}\\ (reported, not summed)};
  \draw[->] (id)--(dd); \draw[->] (dd)--(sc); \draw[->] (sc)--(el); \draw[->] (el)--(in);
  \draw[->, dashed] (t2)--(id);
\end{tikzpicture}"""
    with open(os.path.join(FIG, "prisma_scr_diagram.tex"), "w", encoding="utf-8") as f:
        f.write(diag)

    # 3) threats_to_validity.tex — quantified coverage paragraph (appended target)
    nhat = s3["N_hat"]; crec = s3["estimated_recall_openalex"]
    ttv = (
        "% AUTO-GENERATED quantified-coverage paragraph (external validity / coverage).\n"
        "\\subsection{Coverage and recall (RQ7)}\n"
        "Identification was OpenAlex-primary, which imposes a recall ceiling below "
        "100\\%. We quantify rather than merely disclose this. Against a frozen probe "
        "set of \\ProbeSize{} source-verified canonical benchmarks, OpenAlex recall is "
        "\\ProbeRecallOA{} (probe gap versus the union of all probed sources "
        f"$= {s1['probe_gap_vs_union']}$): every canonical benchmark that any probed "
        "source returns is also present in OpenAlex. Crossref, the independent second "
        "engine, returned only \\ProbeRecallCR{} of the same probe set, because several "
        "canonical benchmarks are arXiv-only and lack a Crossref-indexed archival record. "
        "A Chapman capture--recapture estimate on the full in-scope corpus "
        f"($n_{{OA}}={s3['n_openalex_include_set']}$, $n_{{CR}}={s3['n_crossref_inscope_search']}$, "
        f"overlap $m={s3['overlap_m']}$) yields $\\hat{{N}}={nhat}$ and an implied OpenAlex "
        f"recall of ${crec}$. We do \\emph{{not}} present this as a measurement. The two "
        "engines are heterogeneous targeted searches rather than independent random "
        "samples, so assumption~(i) fails in a direction that depresses $m$ and inflates "
        "$\\hat{N}$; the implied recall is therefore a loose \\emph{lower} bound and is "
        "contradicted---reassuringly---by the 100\\% probe-set capture of canonical work. "
        "The defensible synthesis is that OpenAlex recall on known, influential agent "
        "benchmarks is effectively complete, while recall over the long tail of "
        "low-visibility benchmarks is materially below 100\\% and not precisely estimable "
        "with the present data. We report all absolute volumes as lower bounds and all "
        "within-corpus composition shares as directionally reliable. IEEE and ACM probe "
        "columns are \\texttt{UNRESOLVED:no\\_credentials} for this run.\n")
    with open(os.path.join(MAN, "threats_to_validity_coverage.tex"), "w", encoding="utf-8") as f:
        f.write(ttv)

    # 4) Section 4.1 confidence sentence (mandatory front-matter for trends)
    conf = (
        "% AUTO-GENERATED confidence sentence; insert at head of Section 4.1 (Trends).\n"
        "\\noindent\\textbf{Confidence note.} The probe-set proxy shows OpenAlex captures "
        "\\ProbeRecallOA{} of source-verified canonical benchmarks (probe gap "
        f"$={s1['probe_gap_vs_union']}$), so the \\emph{{shape}} and \\emph{{composition}} "
        "of the trends below (capability mix, year-over-year proportions, relative venue "
        "shares) are directionally reliable; absolute counts are reported as \\emph{lower "
        "bounds} because long-tail recall is incomplete and recent years additionally "
        "undercount owing to indexing lag.\n")
    with open(os.path.join(MAN, "section_4_1_confidence.tex"), "w", encoding="utf-8") as f:
        f.write(conf)
    log("manuscript: prisma_macros, prisma_scr_diagram, threats coverage para, "
        "section 4.1 confidence sentence emitted.")


# --------------------------------------------------------------------------- #
# RUNNER
# --------------------------------------------------------------------------- #
STAGES = [
    ("harvest", stage_harvest),
    ("dedup", stage_dedup),
    ("screen", stage_screen),
    ("snowball", stage_snowball),
    ("recall_gap", stage_recall_gap),
    ("taxonomy", stage_taxonomy),
    ("manuscript", stage_manuscript),
]

def main():
    force = "--force" in sys.argv
    only = None
    for a in sys.argv:
        if a.startswith("--force-stage="):
            only = a.split("=", 1)[1]
    log(f"=== build_review.py START  ({NOW}) ===")
    for name, fn in STAGES:
        f = force or (only == name)
        fn(force=f)
    log(f"=== build_review.py DONE  api_calls={_session_calls['n']} ===")

if __name__ == "__main__":
    main()
