#!/bin/bash
# ONE-CLICK PILOT RUNNER (macOS). Double-click this file in Finder, or run:
#   bash START_PILOT.command
# It sets up tau-bench if needed, asks for your Gemini key if not set,
# runs 5 seeds x 50 tasks, and produces pilot_results.json.
set -e
PILOT_DIR="$(cd "$(dirname "$0")" && pwd)"
CODE_DIR="$(cd "$PILOT_DIR/../../.." && pwd)"   # .../vnageshwaran/code
TB="$CODE_DIR/tau-bench"

echo "==============================================="
echo " AIR revision - repeated-run pilot (tau-bench)"
echo " Prices baked in from ai.google.dev, 2026-07-11:"
echo "   gemini-3.5-flash  \$1.50/M in, \$9.00/M out (agent + user sim)"
echo "==============================================="

# 1. tau-bench checkout
if [ ! -d "$TB" ]; then
  echo "[1/5] Cloning tau-bench..."
  git clone https://github.com/sierra-research/tau-bench.git "$TB"
else
  echo "[1/5] tau-bench found."
fi
cd "$TB"

# 2. venv + install
if [ ! -d .venv ]; then
  echo "[2/5] Creating Python environment..."
  python3 -m venv .venv
fi
source .venv/bin/activate
python -c "import tau_bench" 2>/dev/null || { echo "    installing tau-bench..."; pip -q install -e .; }
echo "[2/5] Environment ready."

# 3. API key
while true; do
  if [ -z "${GEMINI_API_KEY:-}" ]; then
    echo "[3/5] Paste your Gemini API key (input hidden), then press Enter:"
    read -rs GEMINI_API_KEY
  fi
  # strip whitespace/control chars
  GEMINI_API_KEY=$(printf '%s' "$GEMINI_API_KEY" | tr -d '[:space:][:cntrl:]')
  # reject only obvious non-keys (terminal prompts, paths, emails)
  case "$GEMINI_API_KEY" in
    *@*|*/*|*%*|"") ok=0 ;;
    *) if [ ${#GEMINI_API_KEY} -ge 20 ] && [ ${#GEMINI_API_KEY} -le 100 ]; then ok=1; else ok=0; fi ;;
  esac
  if [ "$ok" = "1" ]; then break; fi
  echo "  That looks like a terminal prompt or path, not an API key."
  echo "  Copy the key with the copy button at https://aistudio.google.com/apikey and paste again."
  GEMINI_API_KEY=""
done
export GEMINI_API_KEY
echo "[3/5] Key accepted (${#GEMINI_API_KEY} chars) - the canary call below is the real test."

# 4. run all seeds (skips seeds whose result JSON already exists)
echo "[4/5] Running 5 seeds x 50 tasks SLOWLY (concurrency 1) to stay under"
echo "      Google's Tier-1 spend limiter (\$10 per rolling 10 minutes)."
echo "      Expect ~40-70 min per seed plus a 10-min cooldown between seeds."
TASK_IDS=$(python3 -c "import json;print(' '.join(map(str,json.load(open('$PILOT_DIR/taubench_retail_subset.json'))['task_ids'])))")
# Quota canary: one tiny paid-tier call must succeed before burning seeds.
python3 - <<'PYEOF'
import os, urllib.request, urllib.error, json, sys
key = os.environ["GEMINI_API_KEY"]
req = urllib.request.Request(
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key=" + key,
    data=json.dumps({"contents":[{"parts":[{"text":"Reply with OK"}]}]}).encode(),
    headers={"Content-Type":"application/json"})
try:
    urllib.request.urlopen(req, timeout=60).read()
    print("  quota canary: OK")
except urllib.error.HTTPError as e:
    body = e.read().decode(errors="replace")[:800]
    print("  QUOTA CANARY FAILED:", e)
    print("  --- error detail from Google (identifies WHICH limit) ---")
    print("  " + body.replace("\n", "\n  "))
    print("  ----------------------------------------------------------")
    print("  If it mentions FreeTier / PerDay: this key's PROJECT is free tier")
    print("  or its daily quota is spent. Make sure the key belongs to the")
    print("  Tier-1 project (AI Studio -> API keys shows the project per key).")
    sys.exit(1)
except Exception as e:
    print("  QUOTA CANARY FAILED:", e); sys.exit(1)
PYEOF

for SEED in 1 2 3 4 5; do
  RUNJSON="$PILOT_DIR/runs/taubench-retail_gemini-3.5-flash_seed${SEED}.json"
  # skip only if the existing run JSON is HEALTHY (nonzero tokens)
  if [ -f "$RUNJSON" ] && python3 -c "import json,sys;sys.exit(0 if json.load(open('$RUNJSON'))['tokens_in']>10000 else 1)"; then
    echo "  seed $SEED already done (healthy), skipping."; continue
  fi
  echo "  === seed $SEED starting $(date '+%H:%M') ==="
  LOG_DIR="results_pilot_seed${SEED}_$(date +%s)"; mkdir -p "$LOG_DIR"
  T0=$(date +%s)
  python run.py --env retail \
    --model gemini-3.5-flash --model-provider gemini \
    --user-model gemini-3.5-flash --user-model-provider gemini \
    --user-strategy llm --temperature 0.0 --seed "$SEED" \
    --task-ids $TASK_IDS --max-concurrency 1 --log-dir "$LOG_DIR"
  T1=$(date +%s)
  CKPT=$(ls -t "$LOG_DIR"/*.json | head -1)
  python3 "$PILOT_DIR/convert_taubench.py" "$CKPT" \
    --benchmark taubench-retail --model gemini-3.5-flash --seed "$SEED" \
    --wall-clock-s "$((T1-T0))" --env-hours 0.0 \
    --price-in 1.50 --price-out 9.00 --price-date 2026-07-11
  echo "  cooling down 10 min (Tier-1 spend window)..."; sleep 600
  # abort if this seed came back empty (quota died mid-run)
  if ! python3 -c "import json,sys;sys.exit(0 if json.load(open('$RUNJSON'))['tokens_in']>10000 else 1)"; then
    echo "  Seed $SEED produced (near-)empty trajectories -> quota/rate-limit failure."
    echo "  Stopping so remaining seeds are not wasted. Fix billing, re-run this script."
    exit 1
  fi
done

# 5. aggregate
echo "[5/5] Aggregating..."
python3 "$PILOT_DIR/analyze_pilot.py"
echo ""
echo "DONE. Results: $PILOT_DIR/pilot_results.json"
echo "Tell Claude the pilot is finished."
