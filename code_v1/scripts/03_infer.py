# -*- coding: utf-8 -*-
"""
按原始评测脚本（evaluation_medinst32.py 的 predict()）的方式生成预测：
  messages = [{"role":"user","content": instruction + "\\n" + input}]   # chat 接口，非 alpaca 模板
  max_tokens=1024, temperature=0

用法：
  python gen_orig_style.py --test-json out/test_mix3/v2_test_mix3.json \
      --out out/mix3_v4full/preds.json --model v2 --base_url http://localhost:8000/v1 --key EMPTY
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed


def build_messages(x, use_history):
    """按论文评测方式构造 messages。

    v1_test_4800.json 的 `history` 是每个任务的 2-shot 示例：
        [[q1, a1], [q2, a2]]
    论文评测用的是 in-context 设定，之前只喂 instruction+input（0-shot），
    会系统性低估模型（尤其零样本模型，实测低 30 分左右）。
    """
    cur = (x.get("instruction") or "") + "\n" + (x.get("input") or "")
    if not use_history:
        return [{"role": "user", "content": cur}]
    msgs = []
    for pair in (x.get("history") or []):
        if not isinstance(pair, (list, tuple)) or len(pair) < 2:
            continue
        msgs.append({"role": "user", "content": str(pair[0])})
        msgs.append({"role": "assistant", "content": str(pair[1])})
    msgs.append({"role": "user", "content": cur})
    return msgs


def call(base_url, key, model, messages, max_tokens, timeout):
    body = json.dumps({
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.0,
    }).encode("utf-8")
    req = urllib.request.Request(
        base_url.rstrip("/") + "/chat/completions", data=body,
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + key})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read().decode("utf-8"))
    return d["choices"][0]["message"]["content"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test-json", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="v2")
    ap.add_argument("--base_url", default="http://localhost:8000/v1")
    ap.add_argument("--key", default="EMPTY")
    ap.add_argument("--max-tokens", type=int, default=1024)
    ap.add_argument("--concurrency", type=int, default=32)
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--use-history", action="store_true",
                    help="使用测试集的 history 字段作为 2-shot in-context 示例（论文评测方式）")
    args = ap.parse_args()

    rows = json.load(open(args.test_json, encoding="utf-8"))
    msgs = [build_messages(x, args.use_history) for x in rows]
    n_shot = len(msgs[0]) // 2 if args.use_history else 0
    print("测试样本 %d 条（%s）" % (len(rows), os.path.basename(args.test_json)))
    if args.use_history:
        print("prompt 构造：%d-shot in-context（使用 history 字段）+ instruction/input" % n_shot)
    else:
        print("prompt 构造：instruction + '\\n' + input（0-shot）")
    n_hist = sum(1 for x in rows if x.get("history"))
    print("  带 history 的样本：%d / %d" % (n_hist, len(rows)))

    out = [None] * len(rows)
    fail = 0
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futs = {ex.submit(call, args.base_url, args.key, args.model, m,
                          args.max_tokens, args.timeout): i
                for i, m in enumerate(msgs)}
        for k, fu in enumerate(as_completed(futs), 1):
            i = futs[fu]
            try:
                out[i] = fu.result()
            except Exception:
                out[i] = ""
                fail += 1
            if k % 200 == 0 or k == len(rows):
                print("  进度 %d/%d  失败 %d  用时 %.0fs" % (k, len(rows), fail, time.time() - t0),
                      flush=True)

    res = []
    for x, p in zip(rows, out):
        # 兼容两种测试文件：有 source 字段的，或只有 original_file 的
        src = x.get("source") or re.sub(
            r"_(train|test|dev)\.json$", "", str(x.get("original_file") or ""))
        res.append({
            "source": src,
            "task": x.get("task"),
            "template_id": x.get("template_id"),
            "instruction_style": x.get("instruction_style"),
            "instruction": x.get("instruction"),
            "input": x.get("input"),
            "prediction": p,
            "gold": x.get("output"),
            "gold_legacy": x.get("output_legacy") or x.get("output"),
        })
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    json.dump(res, open(args.out, "w", encoding="utf-8"), ensure_ascii=False)
    print("完成：%d 条，请求失败 %d 条 -> %s" % (len(res), fail, args.out))


if __name__ == "__main__":
    main()
