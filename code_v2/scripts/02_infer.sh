#!/bin/bash
# =============================================================================
# Serve a merged model with vLLM and dump predictions on a test file.
#
#   bash scripts/02_infer.sh ds10k_v1match data/test/v2_test_mixed9_4800.json preds/ds10k_v1match
#   bash scripts/02_infer.sh plain         data/test/v2_test_mixed9_4800.json preds/plain
#
# Leaf names of the three shipped models:
#   plain         -> models/Meta-Llama-3.1-8B-Instruct_v2_full_plain
#   p3            -> models/Meta-Llama-3.1-8B-Instruct_v2_full_p3
#   ds10k_v1match -> models/Meta-Llama-3.1-8B-Instruct_v2_p3_ds10k_v1match
#
# Decoding: greedy (T=0), max_tokens=1024, max_model_len=32768.
# =============================================================================
set -uo pipefail

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PKG=$(dirname "$HERE")
REPO=${REPO:-$(cd "$PKG/.." && pwd)}
BASENAME=Meta-Llama-3.1-8B-Instruct

LEAF=${1:?usage: 02_infer.sh <leaf> <test.json> <outdir>}
TEST=${2:?usage: 02_infer.sh <leaf> <test.json> <outdir>}
OUT=${3:-$PKG/preds/$LEAF}

MODEL=$REPO/models/${BASENAME}_${LEAF}
PORT=${PORT:-8000}
SERVED=${SERVED:-v2}
MAXLEN=${MAXLEN:-32768}
MAXTOK=${MAXTOK:-1024}
CONC=${CONC:-32}
LOG=${LOG:-$PKG/preds/${LEAF}_vllm.log}

[ -f "$MODEL/config.json" ] || { echo "!! model not found: $MODEL"; exit 1; }
mkdir -p "$OUT" "$(dirname "$LOG")"

pkill -f "vllm.entrypoints.openai.api_server" 2>/dev/null || true
sleep 5
echo ">>> serving $MODEL on :$PORT (log $LOG)"
python -m vllm.entrypoints.openai.api_server \
  --model "$MODEL" --served-model-name "$SERVED" \
  --max-model-len "$MAXLEN" --port "$PORT" \
  --gpu-memory-utilization 0.9 --disable-log-requests > "$LOG" 2>&1 &
PID=$!

ok=0
for _ in $(seq 1 180); do
  kill -0 "$PID" 2>/dev/null || { echo "!! server exited"; tail -n 30 "$LOG"; exit 1; }
  if curl -s "http://localhost:$PORT/v1/models" | grep -q "\"$SERVED\""; then ok=1; break; fi
  sleep 5
done
[ "$ok" = 1 ] || { echo "!! server not ready"; tail -n 30 "$LOG"; exit 1; }

echo ">>> generating ($(basename "$TEST"), max_tokens=$MAXTOK, concurrency=$CONC)"
python "$HERE/lib/gen_predictions.py" \
  --test-json "$TEST" --out "$OUT/preds.json" \
  --model "$SERVED" --base_url "http://localhost:$PORT/v1" --key EMPTY \
  --max-tokens "$MAXTOK" --concurrency "$CONC" || { pkill -f "vllm.entrypoints" ; exit 1; }

pkill -f "vllm.entrypoints.openai.api_server" 2>/dev/null || true
echo ">>> predictions: $OUT/preds.json"
