#!/usr/bin/env bash
# Repeated-run trilemma pilot: tau-bench retail, 5 seeds, fixed 50-task subset.
#
# Prereqs (once):
#   git clone https://github.com/sierra-research/tau-bench.git && cd tau-bench
#   pip install -e .
#   export ANTHROPIC_API_KEY=...   # or OPENAI_API_KEY, per provider
#
# Then, from the tau-bench checkout:
#   bash /path/to/Awesome-LLM-Agent-Evaluation/analysis/pilot/run_all_taubench.sh
#
# Config — edit these four lines:
MODEL="${PILOT_MODEL:-gemini-2.5-pro}"
PROVIDER="${PILOT_PROVIDER:-gemini}"
USER_MODEL="${PILOT_USER_MODEL:-gemini-2.5-flash}"
USER_PROVIDER="${PILOT_USER_PROVIDER:-gemini}"
PRICE_IN="${PILOT_PRICE_IN:-CHANGE_ME}"   # USD per Mtok input, from provider pricing page on PRICE_DATE
PRICE_OUT="${PILOT_PRICE_OUT:-CHANGE_ME}" # USD per Mtok output
PRICE_DATE="$(date +%F)"
if [ "$PRICE_IN" = "CHANGE_ME" ] || [ "$PRICE_OUT" = "CHANGE_ME" ]; then
  echo "Set PILOT_PRICE_IN and PILOT_PRICE_OUT (USD per Mtok) from today's pricing page first."; exit 1
fi

set -euo pipefail
PILOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TASK_IDS=$(python3 -c "import json;print(' '.join(map(str,json.load(open('$PILOT_DIR/taubench_retail_subset.json'))['task_ids'])))")

for SEED in 1 2 3 4 5; do
  echo "=== seed $SEED ==="
  LOG_DIR="results_pilot_seed${SEED}"
  mkdir -p "$LOG_DIR"
  T0=$(date +%s)
  python run.py --env retail \
    --model "$MODEL" --model-provider "$PROVIDER" \
    --user-model "$USER_MODEL" --user-model-provider "$USER_PROVIDER" \
    --user-strategy llm \
    --temperature 0.0 --seed "$SEED" \
    --task-ids $TASK_IDS \
    --max-concurrency 5 \
    --log-dir "$LOG_DIR"
  T1=$(date +%s)
  CKPT=$(ls -t "$LOG_DIR"/*.json | head -1)
  python3 "$PILOT_DIR/convert_taubench.py" "$CKPT" \
    --benchmark taubench-retail --model "$MODEL" --seed "$SEED" \
    --wall-clock-s "$((T1-T0))" --env-hours 0.0 \
    --price-in "$PRICE_IN" --price-out "$PRICE_OUT" --price-date "$PRICE_DATE"
done

echo "All seeds done. Now: python3 $PILOT_DIR/analyze_pilot.py"
echo "NOTE: replace estimated token counts with dashboard-measured totals via"
echo "      convert_taubench.py --tokens-in/--tokens-out re-runs if available."
