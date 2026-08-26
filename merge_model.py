# #!/usr/bin/env python
# # coding=utf-8
import os
import shutil
import sys

from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
def merge(base_model, best_model):
    lora_adapter_path = best_model
    model_dir = "models/"+"_".join(lora_adapter_path.split("/")[1:3])
    if os.path.exists(model_dir):
        shutil.rmtree(model_dir)
    os.makedirs(model_dir, exist_ok=True)

    # 2. 加载基础模型和tokenizer
    print("加载基础模型...")

    base_model_path=base_model
    base_model = AutoModelForCausalLM.from_pretrained(base_model_path)
    tokenizer = AutoTokenizer.from_pretrained(base_model_path)

    # 3. 加载LoRA适配器
    print("加载LoRA适配器...")
    model = PeftModel.from_pretrained(base_model, lora_adapter_path)

    # 4. 合并模型
    print("合并模型...")
    merged_model = model.merge_and_unload()

    # 5. 保存合并后的模型（使用safetensors）
    print("保存模型...")
    merged_model.save_pretrained(
        model_dir,
        safe_serialization=True  # 使用安全格式
    )

    # 6. 保存tokenizer
    tokenizer.save_pretrained(model_dir)

    print(f"模型已保存到 {model_dir}，包含文件：{os.listdir(model_dir)}")

if __name__ == "__main__":
    base_model = sys.argv[1]
    best_model = sys.argv[2]
    print(base_model, best_model)
    merge(base_model, best_model)
