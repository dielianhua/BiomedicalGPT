#!/bin/tcsh
# =============================================================================
# ⚠ 该脚本的三个参数必须与论文里的 DS-10K / Random-10K / DS-20K / All 完全一致，
#   否则任何新基线（Random-matched / core-set / active learning）都不可比。
#
#   论文那批模型（从 runs/ 的 tensorboard 日志与 adapter_config.json 反推）：
#     * target_modules : 7 个投影层，不含 lm_head        -> 参数量 20,971,520
#     * num_epochs     : 3
#     * 每 epoch 2,500 次优化步（10,000 样本 / 有效 batch 4）-> 总共 7,500 步
#     * cutoff_len 2048 / lr 1e-4 / cosine / warmup 0.01 / r=8 / alpha=8
#
#   2026-10-27 那轮 random_matched_10k 之所以崩（NER 掉 25-30 分），就是这三处漂了：
#     1) target_modules 里被加进了 lm_head  -> 直接偏置输出分布，BIO 标签大量错标
#     2) batch_size 128 -> 每 epoch 只有 78 步，总共 156 步，优化步数少了 48 倍
#     3) num_epochs 变成 2
#   已全部改回。改动前备份见 11fintune_all_lang_med.sh.bak_lmhead
# =============================================================================
######!!!!!!!
num_epochs=3
#model="Mistral-7B-Instruct-v0.2"
#model="DeepSeek-R1-Distill-Qwen-7B"
#model="Llama-2-13b-hf"

NewName=MBioLLM
mkdir $NewName
mkdir evaluation
model="bloomz-3b"
#model="bloomz-1b7"
#model="bloomz-7b1"
#model=MMed-Llama-3-8B
model="Mistral-7B-Instruct-v0.2"
model="Meta-Llama-3.1-8B-Instruct"
#testfile=MedINST32/merged_dataset_all_small_v2_test.json
path='MedINST32/run_data/'
for file in "$path"/*; do
  # 检查是否为文件
  if [ -f "$file" ]; then
    # 使用basename获取文件名，然后使用参数替换去除后缀
    name=$(basename "$file")
    strategy="${name%.*}"
    filename=$path/$name
    echo $strategy, $filename
    #task="Product_Substitute_Identification,Multiclass_Product_Classification,Query_Product_Rank"
    task="TXTCLASS,RE,EE,NER"
    setting="IND_Diverse_Instruction"
#    setting="IND_Single_Instruction"

    #filename="ECInstruct/ECInstruct_train.json"
    num_val=0

    mkdir $NewName/$model/
    mkdir $NewName/$model/$strategy
    # set master_port = $4
    echo $model

    basemodel=$model
    modelname=best
    #modelname=checkpoint-849

    mkdir evaluation/$basemodel
    mkdir evaluation/$basemodel/$strategy/
    mkdir evaluation/$basemodel/$strategy/$modelname
    finale_modelpath=$NewName/$basemodel/$strategy/$modelname
    ###single###
    #output_path=evaluation/$basemodel/$strategy/$modelname/$task$setting".json"
    ####all####
    output_path=evaluation/$basemodel/$strategy/$modelname/
    base_model_path="../model/"$basemodel
    #prompt_template_name=mistral

    echo $finale_modelpath
    echo $output_path
    echo $base_model_path
    echo $base_model
    if [ "$model" = "Mistral-7B-Instruct-v0.2" ]; then
        base_model="../model/Mistral-7B-Instruct-v0.2"
        lora_target_modules='[q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj]'
        prompt_template_name="mistral"
    elif [ "$model" = "MMed-Llama-3-8B" ]; then
        base_model="../model/MMed-Llama-3-8B"
        lora_target_modules='[q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj]'  # 根据实际需求调整
        prompt_template_name="alpaca"  # 根据实际需求调整
    elif [ "$model" = "DeepSeek-R1-Distill-Qwen-7B" ]; then
        base_model="../model/DeepSeek-R1-Distill-Qwen-7B"
        lora_target_modules='[q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj]'  # 根据实际需求调整
        prompt_template_name="alpaca"  # 根据实际需求调整
    elif [ "$model" = "bloomz-7b1" ]; then
        base_model="../model/bloomz-7b1/"
        lora_target_modules='[q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj]'  # 根据实际需求调整
        prompt_template_name="alpaca"  # 根据实际需求调整
   elif [ "$model" = "Meta-Llama-3.1-8B-Instruct" ]; then
       base_model="../model/$model"
       lora_target_modules='[q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj]'
       prompt_template_name="alpaca"
    elif [ "$model" = "bloomz-3b" ]; then
        base_model="../model/bloomz-3b/"
        lora_target_modules='[q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj]'  # 根据实际需求调整
        prompt_template_name="alpaca"  # 根据实际需求调整
    elif [ "$model" = "bloomz-1b7" ]; then
        base_model="../model/bloomz-1b7/"
        lora_target_modules='[q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj]'  # 根据实际需求调整
    elif [ "$model" = "Llama-2-13b-hf" ]; then
        base_model="../model/Llama-2-13b-hf"
        lora_target_modules='[q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj]'  # 根据实际需求调整
        prompt_template_name="alpaca"  # 根据实际需求调整
    fi


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
#true'
#    echo "###inference###"
#    python inference_3task.py \
#        --base_model $base_model_path \
#        --lora_weights $finale_modelpath \
#        --task all \
#        --setting $setting \
#        --output_data_path $output_path \
#        --prompt_template $prompt_template_name \
#        --filename $testfile
#'
#    #    --lang $lang
#    echo "###evaluate_single###"
#    python evaluate_all_language.py \
#        --filename $filename \
#        --tasks $task \
#        --setting $setting \
#        --model $basemodel/$strategy/$modelname > evaluation/$basemodel/$strategy/$modelname/$modelname
#    #break

  fi
done

