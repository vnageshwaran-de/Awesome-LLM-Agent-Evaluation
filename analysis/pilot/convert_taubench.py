#!/usr/bin/env python3
"""Convert a tau-bench results checkpoint JSON into the pilot run-JSON schema.

Usage:
  python3 convert_taubench.py <taubench_results.json> \
      --benchmark taubench-retail --model <model-string> --seed <k> \
      --wall-clock-s <seconds> --env-hours <hours> \
      --price-in <usd_per_Mtok> --price-out <usd_per_Mtok> --price-date YYYY-MM-DD \
      [--tokens-in N --tokens-out N]   # from provider dashboard (preferred)

If --tokens-in/--tokens-out are omitted, tokens are ESTIMATED from trajectory
character counts (chars/4) and the output is marked "token_basis": "estimated".
Dashboard-measured token counts are strongly preferred for the paper.
Writes runs/<benchmark>_<model>_seed<k>.json.
"""
import json, argparse, os, re

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ckpt")
    ap.add_argument("--benchmark", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--wall-clock-s", type=float, required=True)
    ap.add_argument("--env-hours", type=float, default=0.0)
    ap.add_argument("--price-in", type=float, required=True)
    ap.add_argument("--price-out", type=float, required=True)
    ap.add_argument("--price-date", required=True)
    ap.add_argument("--tokens-in", type=int)
    ap.add_argument("--tokens-out", type=int)
    ap.add_argument("--temperature", type=float, default=0.0)
    a = ap.parse_args()

    results = json.load(open(a.ckpt))
    outcomes, est_in, est_out = {}, 0, 0
    for r in results:
        tid = f"task_{r['task_id']:03d}"
        outcomes[tid] = 1 if float(r.get("reward", 0.0)) >= 1.0 else 0
        traj = r.get("traj") or r.get("messages") or []
        for m in traj:
            c = len(str(m.get("content") or ""))
            if m.get("role") == "assistant": est_out += c // 4
            else: est_in += c // 4

    basis = "measured" if a.tokens_in is not None else "estimated_chars_div_4"
    out = {
        "benchmark": a.benchmark, "model": a.model, "seed": a.seed,
        "outcomes": outcomes,
        "tokens_in": a.tokens_in if a.tokens_in is not None else est_in,
        "tokens_out": a.tokens_out if a.tokens_out is not None else est_out,
        "token_basis": basis,
        "wall_clock_s": a.wall_clock_s, "env_hours": a.env_hours,
        "price_in_per_mtok": a.price_in, "price_out_per_mtok": a.price_out,
        "price_date": a.price_date,
        "decoding": {"temperature": a.temperature},
        "source_checkpoint": os.path.basename(a.ckpt),
    }
    safe_model = re.sub(r"[^A-Za-z0-9._-]", "-", a.model.split("/")[-1])
    dst = os.path.join(os.path.dirname(os.path.abspath(__file__)), "runs",
                       f"{a.benchmark}_{safe_model}_seed{a.seed}.json")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    json.dump(out, open(dst, "w"), indent=1)
    n = len(outcomes); p = sum(outcomes.values())
    print(f"wrote {dst}  ({p}/{n} pass, tokens {basis})")

if __name__ == "__main__":
    main()
