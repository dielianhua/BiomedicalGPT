#stra=subset
export WANDB_DISABLED=true
stra=DS_thred_sort
num=20000

dataname=merged_train_100k_v4

data_path="$dataname".json
pt_data_path="$dataname"_small.pt
subset_pt_data_path=subset_"$dataname".pt
basemodel_name=Meta-Llama-3.1-8B-Instruct
model=../../../model/$basemodel_name
model2=model/$basemodel_name
pre_data="$dataname"_pre.json

subset_data="$dataname"_"$stra"_"$num".json
best=MBioLLM/$basemodel_name/"$dataname"_pre/best
best2=MBioLLM/$basemodel_name/"$dataname"_"$stra"_"$num"/best
newmodel=models/"$basemodel_name"_"$dataname"_pre

echo "1. Select Pre-Experienced Data"
python data_analysis.py \
    --data_path $data_path \
    --save_path $pt_data_path \
    --model_name_or_path $model \
    --max_length 512 \
    --prompt alpaca \
    --mod pre

echo "2.select"
python data_by_cluster.py \
    --pt_data_path $pt_data_path \
    --json_data_path $data_path \
    --json_save_path $pre_data \
    --sample_num 10 \
    --kmeans_num_clusters 100 \
    --low_th 25 \
    --up_th 75

echo "3. Train Pre-Experienced Model"
rm run_data/*
cp $pre_data run_data
sh fintune_all_lang_med_other_para.sh $basemodel_name
python merge_model.py $model2 $best


echo "4. Select Data"
rm $subset_pt_data_path
python data_analysis.py \
    --data_path $data_path \
    --save_path $subset_pt_data_path \
    --model_name_or_path $newmodel \
    --max_length 512 \
    --prompt alpaca \
    --mod subset
#
echo "5. score "

python subset_seletion/data_by_threshold.py \
    --pt_data_path $subset_pt_data_path \
    --json_data_path $data_path \
    --json_save_path $subset_data \
    --max_length 512 \
    --sample_number $num \
    --prompt alpaca \
    --model_name_or_path $newmodel


echo "6. Train  Model"

rm run_data/*
cp $subset_data run_data

sh 11fintune_all_lang_med_other_para.sh $basemodel_name

echo "7.merge model"


python merge_model.py $model2 $best2

echo "8.start server"

path=models
name=Meta-Llama-3.1-8B-Instruct_merged_train_100k_v4_DS_thred_sort_20000
echo $path/$name

python -m vllm.entrypoints.openai.api_server \
  --model $path/$name \
 --max-model-len  32768

echo "9.evaluate"

python evaluation_medinst32.py  --name result_"$name" --dir . --model $path/$name --key YOUR_SECRET_KEY  --base_url "http://localhost:8000/v1" >> logs/log_$name