import torch
import json
import numpy as np
import argparse
from tqdm import tqdm

PROMPT_DICT = {
    "prompt_input": (
        "Below is an instruction that describes a task, paired with an input that provides further context. "
        "Write a response that appropriately completes the request.\n\n"
        "### Instruction:\n{instruction}\n\n### Input:\n{input}\n\n### Response:"
    ),
    "prompt_no_input": (
        "Below is an instruction that describes a task. "
        "Write a response that appropriately completes the request.\n\n"
        "### Instruction:\n{instruction}\n\n### Response:"
    ),
}

# 定义固定的输出顺序
FILE_ORDER = [
    "NCBI-disease_train.json",
    "BC5CDR_train.json",
    "BioNLP-2011-GE_train.json",
    "BioNLP-2013-GRO_train.json",
    "MedDialog_train.json",
    "AnEM-RE_train.json",
    "BC5CDR-RE_train.json",
    "BioInfer-RE_train.json",
    "MLEE-EE_train.json"
]


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pt_data_path", type=str, default='')
    parser.add_argument("--json_data_path", type=str, default='')
    parser.add_argument("--json_save_path", type=str, default='')
    parser.add_argument("--model_name_or_path", type=str, default='')
    parser.add_argument("--max_length", type=int, default=4096)
    parser.add_argument("--sample_rate", type=float, default=0.1)
    parser.add_argument("--sample_number", type=int, default=2000, help="固定输出总数为2000")
    parser.add_argument("--prompt", type=str, default='alpaca', help='wiz, alpaca')
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    # 确保总数固定为2000

    print(f"设置输出数据总数为: {args.sample_number}")

    # 计算关键阈值
    threshold_small = args.sample_number / 10  # 小文件判断阈值（200）
    min_per_large = args.sample_number / 20  # 大文件最低采样数量（100）
    print(f"小文件判断阈值 (sample_number/10): {threshold_small}")
    print(f"大文件最低采样数量 (sample_number/20): {min_per_large}")

    from transformers import LlamaTokenizer, LlamaForCausalLM, AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        args.model_name_or_path,
        cache_dir='../cache',
        use_fast=True
    )

    pt_data = torch.load(args.pt_data_path, map_location=torch.device('cpu'))
    with open(args.json_data_path, "r") as f:
        json_data = json.load(f)

    # 1. 统计每个original_file对应的数据量
    original_counts = {file: 0 for file in FILE_ORDER}  # 按固定顺序初始化
    for item in json_data:
        file_name = item['original_file']
        if file_name in original_counts:
            original_counts[file_name] += 1
        else:
            # 处理可能存在的不在固定列表中的文件
            original_counts[file_name] = 1

    # 输出原始文件数量和每个文件的数据量（按指定顺序）
    total_original_files = len(original_counts)
    print(f"原始文件总数: {total_original_files}")
    print("每个原始文件的数据量:")
    for file in FILE_ORDER:
        print(f"  {file}: {original_counts[file]}")
    # 输出不在固定列表中的文件（如果有）
    extra_files = [f for f in original_counts if f not in FILE_ORDER]
    for file in extra_files:
        print(f"  {file}: {original_counts[file]}")

    # 2. 区分小文件和大文件
    small_files = [f for f in original_counts if original_counts[f] < threshold_small]
    large_files = [f for f in original_counts if original_counts[f] >= threshold_small]
    mean_diff_dict = {}  # 存储所有样本的mean_diff值
    print(f"\n小文件数量: {len(small_files)}")
    print(f"大文件数量: {len(large_files)}")

    # 3. 收集小文件索引（全部保留）
    small_file_indices = []
    file_sample_counts = {file: 0 for file in FILE_ORDER + extra_files}  # 初始化采样计数

    for i, item in enumerate(json_data):
        file_name = item['original_file']
        if file_name in small_files:
            small_file_indices.append(i)
            file_sample_counts[file_name] += 1  # 小文件全部保留
            mean_diff_dict[i] = 0.0

    small_files_total = len(small_file_indices)
    print(f"从小文件中采样的数据量: {small_files_total}")

    # 计算需要从大文件中采样的总数量
    needed_from_large = max(0, args.sample_number - small_files_total)
    print(f"需要从大文件中采样的总数据量: {needed_from_large}")

    # 4. 按大文件分组处理，收集每个大文件的候选样本
    original_list = ["MLEE-EE_train.json", "AnEM-RE_train.json", "BioNLP-2013-GRO_train.json","AnEM-COREF_train.json"]
    file_candidates = {f: [] for f in large_files}  # 存储每个大文件的候选样本 (mean_diff, index)

    for i in tqdm(range(len(json_data))):
        item = json_data[i]
        file_name = item['original_file']
        if file_name not in large_files:
            continue  # 只处理大文件

        pt_data_i = pt_data[i]
        loss_1_list = pt_data_i['token_loss'][1]
        loss_2_list = pt_data_i['token_loss'][2]

        instruct_i = item['instruction']
        output_i = item['output']
        original_i = file_name

        direct_answer_text = '### Response:' + output_i
        if args.prompt == 'wiz':
            whole_text = instruct_i + '\n\n### Response:' + output_i
        elif args.prompt == 'alpaca':
            input_i = item['input']
            if input_i == '':
                temp_dict = {'instruction': instruct_i}
                promt_to_use = PROMPT_DICT["prompt_no_input"].format_map(temp_dict)
                whole_text = promt_to_use + output_i
                instruct_i = promt_to_use
            else:
                temp_dict = {'instruction': instruct_i, 'input': input_i}
                promt_to_use = PROMPT_DICT["prompt_input"].format_map(temp_dict)
                whole_text = promt_to_use + output_i
                instruct_i = promt_to_use

        # Tokenize输入文本
        instruct_i_input_ids = tokenizer.encode(instruct_i, return_tensors="pt", truncation=True,
                                                max_length=args.max_length).to('cpu')
        instruct_i_len = instruct_i_input_ids.shape[1]

        def get_loss_part_text(tokenizer, text, target_span, max_length, loss_list_):
            input_ids = tokenizer.encode(text, return_tensors="pt", truncation=True, max_length=max_length).to('cpu')
            start_index = text.rfind(target_span)
            text_temp = text[:start_index]
            token_id_temp = tokenizer.encode(text_temp)
            start_token = len(token_id_temp)
            end_token_real = input_ids.shape[1]

            loss_list = loss_list_[start_token - 1:end_token_real - 1]
            return end_token_real - start_token, input_ids[0][start_token:end_token_real], np.array(loss_list)

        if args.max_length - instruct_i_len > 0:
            len_1, token_ids_1, loss_list_1 = get_loss_part_text(tokenizer, direct_answer_text, output_i,
                                                                 args.max_length - instruct_i_len + 4, loss_1_list)
            len_2, token_ids_2, loss_list_2 = get_loss_part_text(tokenizer, whole_text, output_i, args.max_length,
                                                                 loss_2_list)

            if len_1 <= 0 or len_2 <= 0:
                continue

            if instruct_i_len + len_1 > args.max_length:
                if original_i not in original_list:
                    continue


            # 生效口径：instruction 条件下的平均损失（mean_2）。
            # 原始 IFD 的 mean_2 - mean_1 在此流程中被覆盖，不使用。
            mean_2 = loss_list_2.mean()
            mean_diff = mean_2
            file_candidates[file_name].append((mean_diff, i))  # 按文件分组存储
            mean_diff_dict[i] = mean_diff

        else:
            if original_i not in original_list:
                continue

    # 5. 对每个大文件进行处理：按分数排序并补全至最低数量
    large_file_samples = []  # 存储所有大文件的最终样本索引
    min_per_large_int = int(min_per_large)  # 转为整数便于处理

    for file in large_files:
        candidates = file_candidates[file]
        if not candidates:
            print(f"警告: 大文件 {file} 没有符合条件的候选样本")
            continue

        # 按分数排序（从小到大，与原有逻辑一致）
        candidates_sorted = sorted(candidates)
        # 取最优样本（最后N个）
        initial_samples = [idx for (rate, idx) in candidates_sorted[-min_per_large_int:]]  # 至少取最低数量

        # 如果候选样本不足最低数量，则全部保留
        if len(candidates) < min_per_large_int:
            initial_samples = [idx for (rate, idx) in candidates_sorted]

        # 记录该文件的采样数量
        file_sample_counts[file] = len(initial_samples)
        large_file_samples.extend(initial_samples)

    # 6. 处理大文件样本总量：确保不超过需要的数量
    # 计算当前大文件样本总数
    current_large_total = len(large_file_samples)
    print(f"大文件初始采样总数: {current_large_total}")

    if current_large_total > needed_from_large:
        # 超过需要的数量，按分数重新排序后取前needed_from_large个
        # 重新计算所有大文件样本的分数
        all_large_with_rate = []
        for idx in large_file_samples:
            # 找到对应的分数（需要重新匹配，或在步骤5中保留分数信息）
            # 优化：在步骤5中保留(rate, idx)而不仅是idx
            # 重新构建带分数的列表
            file_name = json_data[idx]['original_file']
            # 从候选列表中找到对应的rate
            for rate, i in file_candidates[file_name]:
                if i == idx:
                    all_large_with_rate.append((rate, idx))
                    break

        # 排序后取前needed_from_large个
        all_large_sorted = sorted(all_large_with_rate)
        final_large_samples = [idx for (rate, idx) in all_large_sorted[-needed_from_large:]]

        # 更新大文件采样计数
        for file in large_files:
            file_sample_counts[file] = 0  # 重置
        for idx in final_large_samples:
            file_name = json_data[idx]['original_file']
            file_sample_counts[file_name] += 1

        print(f"大文件样本超过需求，调整后数量: {len(final_large_samples)}")
    else:
        # 未超过需求，全部保留
        final_large_samples = large_file_samples
        print(f"大文件样本未超过需求，保留数量: {len(final_large_samples)}")

    # 7. 合并小文件和大文件样本
    all_selected_indices = small_file_indices + final_large_samples
    # 去重并排序（保持原始顺序）
    seen = set()
    all_selected_indices = [idx for idx in all_selected_indices if not (idx in seen or seen.add(idx))]
    all_selected_indices.sort()

    # 8. 最终校验总数，确保为sample_number（必要时微调）
    final_total = len(all_selected_indices)
    if final_total != args.sample_number:
        print(f"警告: 最终数量({final_total})与目标({args.sample_number})不符，进行微调...")
        # 若不足则补充最优样本，若超出则删除最差样本
        if final_total < args.sample_number:
            # 从所有候选大文件样本中补充
            additional_needed = args.sample_number - final_total
            all_candidates = []
            for file in large_files:
                all_candidates.extend(file_candidates[file])
            # 排除已选中的
            all_candidates = [(r, i) for (r, i) in all_candidates if i not in all_selected_indices]
            all_candidates_sorted = sorted(all_candidates)
            additional_samples = [i for (r, i) in all_candidates_sorted[-additional_needed:]]
            all_selected_indices.extend(additional_samples)
            # 更新计数
            for r, i in all_candidates_sorted[-additional_needed:]:
                mean_diff_dict[i] = r
            for idx in additional_samples:
                file_name = json_data[idx]['original_file']
                file_sample_counts[file_name] += 1
        else:
            # 超出则删除最差样本
            excess = final_total - args.sample_number
            # 计算所有选中样本的分数
            selected_with_rate = []
            for idx in all_selected_indices:
                file_name = json_data[idx]['original_file']
                for rate, i in file_candidates.get(file_name, []):
                    if i == idx:
                        selected_with_rate.append((rate, idx))
                        break
            # 排序后删除前面的excess个（最差的）
            selected_with_rate_sorted = sorted(selected_with_rate)
            to_remove = [idx for (r, idx) in selected_with_rate_sorted[:excess]]
            all_selected_indices = [idx for idx in all_selected_indices if idx not in to_remove]
            # 更新计数
            for idx in to_remove:
                file_name = json_data[idx]['original_file']
                file_sample_counts[file_name] -= 1
        # 重新排序
        all_selected_indices = sorted(all_selected_indices)

    # 9. 按指定顺序输出每个文件的采样数量统计
    print("\n每个文件的采样数量:")
    for file in FILE_ORDER:
        print(f"  {file}: {file_sample_counts[file]}")
    # 输出不在固定列表中的文件（如果有）
    for file in extra_files:
        print(f"  {file}: {file_sample_counts[file]}")

    # 10. 保存最终结果
    # 修改保存结果部分：

    sorted_indices = sorted(all_selected_indices,
                            key=lambda idx: mean_diff_dict.get(idx, 0.0),
                            reverse=False)

    new_data = []
    for idx in sorted_indices:
        item = json_data[idx].copy()
        item['mean_diff'] = float(mean_diff_dict.get(idx, 0.0))
        new_data.append(item)

    print(f'\n最终筛选数据总量: {len(new_data)}')

    # 打印分数统计
    if mean_diff_dict:
        scores = [mean_diff_dict.get(idx, 0.0) for idx in sorted_indices]
        print(f"分数统计:")
        print(f"  平均值: {np.mean(scores):.4f}")
        print(f"  中位数: {np.median(scores):.4f}")
        print(f"  最大值: {np.max(scores):.4f}")
        print(f"  最小值: {np.min(scores):.4f}")

        # 前10个最高分的样本
        print(f"  前10个最高分样本:")
        for i, idx in enumerate(sorted_indices[:10]):
            score = mean_diff_dict.get(idx, 0.0)
            file_name = json_data[idx]['original_file']
            print(f"    第{i + 1}名: 文件={file_name}, 分数={score:.4f}")

    with open(args.json_save_path, "w") as fw:
        json.dump(new_data, fw, indent=4)


if __name__ == '__main__':
    main()
