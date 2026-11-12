#!/bin/bash
# =============================================================================
# Train ONE model on ONE of the three training sets, then merge the LoRA adapter.
#
#   bash scripts/01_train.sh data/train/v2_plain_27k.json         plain
#   bash scripts/01_train.sh data/train/v2_p3_27k.json            p3
#   bash scripts/01_train.sh data/train/v2_ds10k_v1match_10k.json ds10k_v1match
#
# Recipe (identical for all three, matches the paper):
#   LoRA r=8 alpha=8 on 7 projection layers (no lm_head), batch 4 (micro 1),
#   3 epochs, cutoff_len 2048, lr 1e-4 cosine, warmup 0.01
#   => 10,000 samples = 7,500 steps; 27,673 samples = 20,754 steps
#
# Requires: conda env with torch + peft + transformers, GPU. Set REPO if the
# repository root is not the parent of this package.
# =============================================================================
set -uo pipefail

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PKG=$(dirname "$HERE")
REPO=${REPO:-$(cd "$PKG/.." && pwd)}
BASENAME=Meta-Llama-3.1-8B-Instruct
BASE=${BASE_MODEL:-$REPO/../model/$BASENAME}

DATA=${1:?usage: 01_train.sh <train.json> <leaf>}
LEAF=${2:?usage: 01_train.sh <train.json> <leaf>}

[ -f "$DATA" ] || { echo "!! training file not found: $DATA"; exit 1; }
[ -f "$BASE/config.json" ] || { echo "!! base model not found: $BASE"; exit 1; }

N=$(python -c "import json,sys;print(len(json.load(open(sys.argv[1],encoding='utf-8'))))" "$DATA")
echo ">>> leaf=$LEAF  samples=$N  base=$BASE"

# The trainer iterates over MedINST32/run_data/* and uses the file stem as the run name.
mkdir -p "$REPO/MedINST32/run_data"
find "$REPO/MedINST32/run_data" -maxdepth 1 -type f -delete
cp "$DATA" "$REPO/MedINST32/run_data/$LEAF.json"

echo ">>> [1/2] LoRA fine-tuning"
( cd "$REPO" && sh 11fintune_all_lang_med.sh ) || { echo "!! fine-tuning failed"; exit 1; }

CFG="$REPO/MBioLLM/$BASENAME/$LEAF/best/adapter_config.json"
[ -f "$CFG" ] || { echo "!! adapter not found: $CFG"; exit 1; }

python - "$CFG" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
t = set(d["target_modules"])
print("    LoRA r=%s alpha=%s epochs_target=3 targets(%d): %s" % (d["r"], d["lora_alpha"], len(t), sorted(t)))
if "lm_head" in t or len(t) != 7:
    sys.exit("!! target_modules mismatch (lm_head present, or count != 7)")
PY

echo ">>> [2/2] merge adapter into base"
( cd "$REPO" && python merge_model.py "$BASE" "MBioLLM/$BASENAME/$LEAF/best" ) || exit 1

echo ">>> done: $REPO/models/${BASENAME}_${LEAF}"
