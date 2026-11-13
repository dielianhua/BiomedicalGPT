#!/bin/bash
# ============================================================================
# 06 · 推理 + 评测
#
# 用法：
#   bash 06_run_eval.sh model=/path/to/model                  # 跑 20 任务测试集
#   bash 06_run_eval.sh model=/path/to/model test=sci209      # 跑 SciFact 209
#   bash 06_run_eval.sh model=/path/to/model shot=2           # 2-shot（默认 0-shot）
#   bash 06_run_eval.sh all                                   # 跑 models/ 下所有
#
# 参数（key=value，可任意顺序）：
#   model   模型目录（必填，或 all）
#   test    test4800（默认）| sci209
#   shot    0（默认）| 2
#   tag     输出子目录名（默认取模型目录名）
#   max_tok 生成长度（默认 1024；sci209 自动用 128）
#   port    vLLM 端口（默认 8000）
#
# 产出：results/<tag>/<test>/preds.json + metrics.json
# ============================================================================
set -uo pipefail

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ROOT=$(dirname "$HERE")

MODEL=""; TEST="test4800"; SHOT=0; TAG=""; MAXTOK=""; PORT=8000
for kv in "$@"; do
  case "$kv" in
    model=*)   MODEL="${kv#*=}" ;;
    test=*)    TEST="${kv#*=}" ;;
    shot=*)    SHOT="${kv#*=}" ;;
    tag=*)     TAG="${kv#*=}" ;;
    max_tok=*) MAXTOK="${kv#*=}" ;;
    port=*)    PORT="${kv#*=}" ;;
    all)       MODEL="all" ;;
    *) echo "无法识别的参数: $kv"; exit 1 ;;
  esac
done

case "$TEST" in
  test4800) TEST_FILE="$ROOT/data/test/v1_test_4800.json"; [ -n "$MAXTOK" ] || MAXTOK=1024 ;;
  sci209)   TEST_FILE="$ROOT/data/test/test_scifact_209.json"; [ -n "$MAXTOK" ] || MAXTOK=128 ;;
  *) echo "未知 test: $TEST（test4800 / sci209）"; exit 1 ;;
esac
[ -f "$TEST_FILE" ] || { echo "!! 缺少测试集 $TEST_FILE"; exit 1; }

PY=${PY:-python}

run_one () {
  local mpath="$1" tag="$2"
  local out="$ROOT/results/$tag/$TEST"
  if [ -f "$out/metrics.json" ]; then echo "  [$tag] 已完成，跳过"; return 0; fi
  mkdir -p "$out"

  echo ""
  echo "==== $tag · $TEST · ${SHOT}-shot · MAXTOK=$MAXTOK ===="
  pkill -f "vllm.entrypoints.openai.api_server" 2>/dev/null
  sleep 8
  "$PY" -m vllm.entrypoints.openai.api_server \
    --model "$mpath" --served-model-name v2 \
    --max-model-len 8192 --port "$PORT" --gpu-memory-utilization 0.85 \
    --disable-log-requests > "$ROOT/results/vllm_$tag.log" 2>&1 &
  for _ in $(seq 1 180); do
    curl -s "http://localhost:$PORT/v1/models" >/dev/null 2>&1 && break
    sleep 5
  done
  curl -s "http://localhost:$PORT/v1/models" >/dev/null 2>&1 || {
    echo "!! 服务未就绪，见 results/vllm_$tag.log"; return 1; }

  local hist=(); [ "$SHOT" = "2" ] && hist=(--use-history)
  "$PY" "$HERE/03_infer.py" --test-json "$TEST_FILE" --out "$out/preds.json" \
     --model v2 --base_url "http://localhost:$PORT/v1" --key EMPTY \
     --max-tokens "$MAXTOK" --concurrency 32 "${hist[@]}"
  "$PY" "$HERE/04_eval.py" --input "$out/preds.json" --out "$out/metrics.json"
  pkill -f "vllm.entrypoints.openai.api_server" 2>/dev/null
  sleep 8

  "$PY" - "$out/metrics.json" "$tag" <<'PY'
import json, sys
m = json.load(open(sys.argv[1], encoding="utf-8"))
sf = m.get("per_source", {}).get("SciFact", {})
print("  [%s] macro %.2f | SciFact %.2f (n=%s)" % (
    sys.argv[2], m.get("macro", 0), sf.get("f1", 0), sf.get("n", "-")))
PY
}

if [ "$MODEL" = "all" ]; then
  shopt -s nullglob
  for d in "$ROOT"/models/*/; do
    [ -f "$d/config.json" ] || continue
    run_one "${d%/}" "$(basename "${d%/}")"
  done
else
  [ -n "$MODEL" ] || { echo "必须指定 model=<路径> 或 all"; exit 1; }
  [ -f "$MODEL/config.json" ] || { echo "!! 不是可加载的 HF 模型: $MODEL"; exit 1; }
  [ -n "$TAG" ] || TAG=$(basename "$MODEL")
  run_one "$MODEL" "$TAG"
fi

echo ""
echo "下一步：python 07_summarize.py"
