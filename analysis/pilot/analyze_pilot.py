#!/usr/bin/env python3
"""Analysis for the repeated-run trilemma pilot (see PROTOCOL.md).

Input: runs/<bench>_<model>_seed<k>.json, each:
  {"benchmark": str, "model": str, "seed": int,
   "outcomes": {task_id: 0|1, ...},
   "tokens_in": int, "tokens_out": int,
   "wall_clock_s": float, "env_hours": float,
   "price_in_per_mtok": float, "price_out_per_mtok": float,
   "price_date": "YYYY-MM-DD", "decoding": {...}}

Output: pilot_results.json + a printed summary table.
Deterministic; requires only the Python stdlib + math.
"""
import json, glob, math, itertools, os
from collections import defaultdict

Z975, Z80 = 1.959964, 0.841621

def wilson(p, n, z=Z975):
    if n == 0: return (0.0, 1.0)
    c = (p + z*z/(2*n)) / (1 + z*z/n)
    h = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / (1 + z*z/n)
    return (max(0.0, c-h), min(1.0, c+h))

def t_ci_mean(xs, tcrit=2.776):  # t_{0.975,4} for 5 seeds
    n = len(xs); m = sum(xs)/n
    if n < 2: return (m, m, m, 0.0)
    sd = math.sqrt(sum((x-m)**2 for x in xs)/(n-1))
    h = tcrit*sd/math.sqrt(n)
    return (m, m-h, m+h, sd)

def seeds_needed(sd_diff, d_targets=(1.0, 0.5, 0.3)):
    # n for 80% power, two-sided alpha=.05, paired t on standardized diff
    return {f"d={d}": math.ceil(((Z975+Z80)/d)**2 + 2) for d in d_targets}

def main():
    runs = defaultdict(list)
    for f in sorted(glob.glob(os.path.join(os.path.dirname(__file__), "runs", "*.json"))):
        r = json.load(open(f)); runs[(r["benchmark"], r["model"])].append(r)
    out = {}
    for (bench, model), rs in sorted(runs.items()):
        rs.sort(key=lambda r: r["seed"])
        rates = [sum(r["outcomes"].values())/len(r["outcomes"]) for r in rs]
        n_tasks = len(rs[0]["outcomes"])
        m, lo, hi, sd = t_ci_mean(rates)
        dev = [abs(x-m) for x in rates]
        # pass^k over seeds: fraction of tasks solved in ALL k seeds (k=1..K)
        ids = list(rs[0]["outcomes"].keys())
        passk = {}
        for k in range(1, len(rs)+1):
            passk[f"pass^{k}"] = round(sum(
                1 for t in ids if all(r["outcomes"][t] for r in rs[:k]))/n_tasks, 4)
        cost = sum(r["tokens_in"]/1e6*r["price_in_per_mtok"]
                   + r["tokens_out"]/1e6*r["price_out_per_mtok"] for r in rs)
        succ = sum(sum(r["outcomes"].values()) for r in rs)
        out[f"{bench}|{model}"] = {
            "n_tasks": n_tasks, "n_seeds": len(rs),
            "seed_rates": [round(x,4) for x in rates],
            "mean": round(m,4), "sd": round(sd,4),
            "ci95_mean": [round(lo,4), round(hi,4)],
            "wilson_ci_per_seed": [ [round(v,4) for v in wilson(x, n_tasks)] for x in rates],
            "single_run_abs_dev": {"max": round(max(dev),4), "mean": round(sum(dev)/len(dev),4)},
            **passk,
            "seeds_for_80pct_power": seeds_needed(sd),
            "cost_record": {
                "model": model,
                "decoding": rs[0].get("decoding", {}),
                "price_date": rs[0].get("price_date"),
                "tokens_in_total": sum(r["tokens_in"] for r in rs),
                "tokens_out_total": sum(r["tokens_out"] for r in rs),
                "wall_clock_s_total": round(sum(r["wall_clock_s"] for r in rs),1),
                "env_hours_total": round(sum(r["env_hours"] for r in rs),3),
                "usd_total": round(cost,2),
                "usd_per_task": round(cost/(n_tasks*len(rs)),4),
                "usd_per_success": round(cost/succ,4) if succ else None,
            }}
    # rank churn across model pairs on same benchmark
    by_bench = defaultdict(list)
    for k in out: by_bench[k.split("|")[0]].append(k)
    for bench, keys in by_bench.items():
        for a, b in itertools.combinations(keys, 2):
            ra, rb = out[a]["seed_rates"], out[b]["seed_rates"]
            pairs = [(x, y) for x in ra for y in rb]
            churn = sum(1 for x, y in pairs if (x > y) != (out[a]["mean"] > out[b]["mean"]))/len(pairs)
            out.setdefault("rank_churn", {})[f"{a} vs {b}"] = round(churn, 3)
    dst = os.path.join(os.path.dirname(__file__), "pilot_results.json")
    json.dump(out, open(dst, "w"), indent=1)
    print(json.dumps(out, indent=1))
    print("wrote", dst)

if __name__ == "__main__":
    main()
