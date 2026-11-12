# -*- coding: utf-8 -*-
"""
v2 数据集：用 vLLM OpenAI 接口在 unseen-template 测试集上生成预测。

关键点：训练用的是 LLaMA-Factory 风格的 alpaca 模板（templates/alpaca.json 的
prompt_no_options，且**总是包含 ### Input: 段**）。因此这里必须：
  1. 用同一份模板文件拼 prompt（不硬编码，避免漂移）
  2. 走 /v1/completions（原始文本续写），不走 /v1/chat/completions
     —— 训练时模型看到的是裸文本，套 chat template 会与训练分布不一致

用法：
  python gen_predictions.py --test-json out/test_unseen/v2_test_terse.json \\
      --out out/preds_terse.json --model models/Meta-Llama-3.1-8B-Instruct_v2_train
  python gen_predictions.py --test-json ... --dry-run      # 只打印前 2 条 prompt
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "..", "templates", "alpaca.json")


def load_template(path):
    if not os.path.exists(path):
        raise SystemExit("找不到模板文件 %s" % os.path.abspath(path))
    t = json.load(open(path, encoding="utf-8"))
    return t["prompt_no_options"], t.get("response_split", "### Response:")


def build_prompt(tpl, instruction, inp):
    # 与 Prompter.generate_prompt 的 no_options 分支完全一致
    return tpl.format(instruction=instruction, input=inp or "")


def list_models(base_url, key):
    """列出服务端实际暴露的模型名。名字不匹配时 vLLM 只回 404，很难看出原因。"""
    req = urllib.request.Request(base_url.rstrip("/") + "/models",
                                 headers={"Authorization": "Bearer %s" % key})
    with urllib.request.urlopen(req, timeout=30) as r:
        payload = json.loads(r.read().decode("utf-8"))
    return [m.get("id") for m in payload.get("data", [])]


def call(base_url, key, model, prompt, max_tokens, timeout, stop):
    """只用标准库 urllib，避免 requests 缺失。"""
    body = json.dumps({"model": model, "prompt": prompt, "max_tokens": max_tokens,
                       "temperature": 0.0, "top_p": 1.0, "stop": stop}).encode("utf-8")
    req = urllib.request.Request(
        base_url.rstrip("/") + "/completions", data=body,
        headers={"Authorization": "Bearer %s" % key,
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        payload = json.loads(r.read().decode("utf-8"))
    return payload["choices"][0]["text"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test-json", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--base_url", default="http://localhost:8000/v1")
    ap.add_argument("--key", default="EMPTY")
    ap.add_argument("--model", required=False, default="")
    ap.add_argument("--max-tokens", type=int, default=512)
    ap.add_argument("--concurrency", type=int, default=32)
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--limit", type=int, default=0, help="只跑前 N 条（调试用）")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    tpl, resp_split = load_template(TEMPLATE)
    items = json.load(open(args.test_json, encoding="utf-8"))
    if args.limit:
        items = items[:args.limit]
    print("测试样本 %d 条（%s）" % (len(items), os.path.basename(args.test_json)))

    prompts = [build_prompt(tpl, it["instruction"], it.get("input")) for it in items]

    if args.dry_run:
        for i in range(min(2, len(prompts))):
            print("\n----- PROMPT %d -----\n%s" % (i, prompts[i][:900]))
            print("----- GOLD -----\n%s" % str(items[i]["output"])[:200])
        raise SystemExit(0)

    if not args.model:
        raise SystemExit("非 dry-run 必须给 --model")

    # 预检：确认服务端确实暴露了这个模型名。名字不匹配时只会得到 404，
    # 白白跑完几千条请求才发现。
    try:
        avail = list_models(args.base_url, args.key)
    except Exception as e:
        raise SystemExit("连不上 %s/models：%r" % (args.base_url, e))
    print("服务端可用模型：%s" % avail)
    if args.model not in avail:
        raise SystemExit(
            "请求的模型名 %r 不在服务端列表里。\n"
            "  要么起服务时加 --served-model-name，要么 --model 传上面列出的名字。" % args.model)

    stop = ["\n\n###", resp_split]
    preds = [None] * len(items)
    fails = 0
    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futs = {ex.submit(call, args.base_url, args.key, args.model, p,
                          args.max_tokens, args.timeout, stop): i
                for i, p in enumerate(prompts)}
        for n, fu in enumerate(as_completed(futs), 1):
            i = futs[fu]
            try:
                preds[i] = fu.result()
            except Exception as e:
                preds[i] = ""
                fails += 1
                if fails <= 3:
                    print("  第 %d 条失败: %r" % (i, e))
            if n % 200 == 0:
                print("  进度 %d/%d" % (n, len(items)))

    # 全军覆没通常是配置问题（模型名、端口、max_len），直接停下，别写垃圾结果
    if fails == len(items) and len(items) > 0:
        raise SystemExit("全部 %d 条请求失败，不写输出。先查服务日志。" % fails)

    rows = []
    for it, p in zip(items, preds):
        rows.append({
            "source": it.get("source"),
            "task": it.get("task"),
            "template_id": it.get("template_id"),
            "prediction": p,
            "gold": it["output"],
            "gold_legacy": it.get("output_legacy", ""),
            "input": it.get("input", ""),
        })
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False)
    print("\n完成：%d 条，请求失败 %d 条 -> %s" % (len(rows), fails, args.out))
    if fails:
        print("（失败条目已置空串，评测时会算作 JSON 解析失败，请检查服务是否过载）")


if __name__ == "__main__":
    main()
