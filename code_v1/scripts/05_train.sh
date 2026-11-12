#!/bin/bash
# ============================================================================
# 05 · LoRA 微调（Llama-3.1-8B-Instruct）
#
# 用法：
#   bash 05_train.sh 10k        # DS-10K
#   bash 05_train.sh 20k        # DS-20K
#   bash 05_train.sh all        # DS-All (27,673)
#
# 可覆盖的环境变量：
#   BASE_MODEL  基座模型目录（默认见下）
#   EPOCHS      训练轮数（默认 3）
#   LR          学习率（默认 1e-4）
#   LORA_R      LoRA rank（默认 8）
#
# 产出：
#   models/<TAG>_lora/best/           LoRA adapter
#   models/<TAG>/                     合并后的完整权重
# ============================================================================
set -euo pipefail

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ROOT=$(dirname "$HERE")
cd "$ROOT/scripts" || exit 1        # 必须在 scripts/ 下跑（依赖 ./utils）

TAG=${1:-10k}
case "$TAG" in
  10k) DATA="$ROOT/data/train/v1_DS_10k.json";  SUB="DS_10K" ;;
  20k) DATA="$ROOT/data/train/v1_DS_20k.json";  SUB="DS_20K" ;;
  all) DATA="$ROOT/data/train/v1_DS_27k.json";  SUB="DS_All" ;;
  *) echo "未知 tag: $TAG（10k / 20k / all）"; exit 1 ;;
esac
[ -f "$DATA" ] || { echo "!! 缺少训练数据 $DATA"; exit 1; }

BASE_MODEL=${BASE_MODEL:-/mnt/d/workspace/zjq/model/Meta-Llama-3.1-8B-Instruct}
EPOCHS=${EPOCHS:-3}
LR=${LR:-1e-4}
LORA_R=${LORA_R:-8}
OUT_LORA="$ROOT/models/${SUB}_lora"
OUT_MERGED="$ROOT/models/$SUB"

mkdir -p "$ROOT/models"

echo "==== 训练 $SUB ===="
echo "  数据     : $DATA"
echo "  基座     : $BASE_MODEL"
echo "  LoRA     : $OUT_LORA"
echo "  合并输出 : $OUT_MERGED"
python -c "import json;d=json.load(open('$DATA',encoding='utf-8'));print('  样本数   :',len(d))"

python finetune_newmed.py \
  --base_model "$BASE_MODEL" \
  --data_path "$DATA" \
  --filename "$DATA" \
  --output_dir "MBioLLM/$SUB" \
  --batch_size 4 \
  --micro_batch_size 1 \
  --num_epochs "$EPOCHS" \
  --cutoff_len 2048 \
  --val_set_size 0 \
  --learning_rate "$LR" \
  --lora_r "$LORA_R" \
  --lora_alpha 8 \
  --lora_dropout 0.05 \
  --lora_target_modules '[q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj]' \
  --train_on_inputs False \
  --add_eos_token False \
  --group_by_length False \
  --prompt_template_name alpaca \
  --lr_scheduler cosine \
  --optim adamw_torch \
  --warmup_ratio 0.1 \
  --task_single "TXTCLASS,RE,EE,NER" \
  --setting "IND_Diverse_Instruction"

echo "==== 合并 LoRA ===="
python merge_model.py "$BASE_MODEL" "MBioLLM/$SUB/best"
[ -d "models/$SUB" ] || { echo "!! 合并产物缺失 models/$SUB"; exit 1; }
echo "完成：$OUT_MERGED"
