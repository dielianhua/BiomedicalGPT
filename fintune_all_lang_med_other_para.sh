#!/bin/tcsh
export WANDB_MODE=disabled
num_epochs=3

NewName=MBioLLM
mkdir $NewName
mkdir evaluation
model="Meta-Llama-3.1-8B-Instruct"
model=$1
path='run_data/'
for file in "$path"/*; do
  # 检查是否为文件
  if [ -f "$file" ]; then
    # 使用basename获取文件名，然后使用参数替换去除后缀
    name=$(basename "$file")
    strategy="${name%.*}"
    filename=$path/$name
    echo $strategy, $filename
    task="TXTCLASS,RE,EE,NER"
    setting="IND_Diverse_Instruction"
    num_val=0

    mkdir $NewName/$model/
    mkdir $NewName/$model/$strategy
    echo $model

    basemodel=$model
    modelname=best

    mkdir evaluation/$basemodel
    mkdir evaluation/$basemodel/$strategy/
    mkdir evaluation/$basemodel/$strategy/$modelname
    finale_modelpath=$NewName/$basemodel/$strategy/$modelname

    output_path=evaluation/$basemodel/$strategy/$modelname/
    base_model_path="../model/"$basemodel

    echo $finale_modelpath
    echo $output_path
    echo $base_model_path
    echo $base_model

    base_model="../model/$model"
    lora_target_modules='[q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj]'
    prompt_template_name="alpaca"



    python finetune_newmed.py \
        --base_model $base_model \
        --output_dir $NewName/$model/$strategy \
        --batch_size 4 \
        --micro_batch_size 1 \
        --num_epochs $num_epochs \
        --cutoff_len 2048 \
        --val_set_size $num_val \
        --learning_rate 1e-4 \
        --lora_r 8 \
        --lora_alpha 8 \
        --lora_dropout 0.05 \
        --lora_target_modules "$lora_target_modules" \
        --train_on_inputs False \
        --add_eos_token False \
        --group_by_length False \
        --prompt_template_name $prompt_template_name \
        --lr_scheduler 'cosine' \
        --optim "adamw_torch" \
        --warmup_ratio 0.1 \
        --task_single $task \
        --filename $filename \
        --setting $setting \
  fi
done

