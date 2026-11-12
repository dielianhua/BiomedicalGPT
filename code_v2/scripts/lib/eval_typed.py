# -*- coding: utf-8 -*-
"""
v2 数据集：typed-schema 评测器。

因为 output 已从 5 种遗留格式统一为 schema v2.0 JSON，旧评测器不再适用。
本脚本在 schema 空间直接算指标，口径明确、跨任务可比：

  entities  : micro P/R/F1，匹配条件是 (归一化 text, label)；bio 任务的 label 为 null，只比 text
  relations : micro P/R/F1，匹配条件是 (归一化 head, relation, 归一化 tail)
  mentions  : micro P/R/F1，匹配条件是归一化 string
  label     : accuracy
  answer    : exact match（归一化后）

输入：json 列表，每条含 {source, task, prediction, gold}（gold 为 schema v2.0 JSON 串）
输出：per-source 指标 + 总表

用法：
  python eval_typed.py --input out/preds.json
"""

import argparse
import collections
import json
import math
import re

TASK_METRIC = {
    "NER": "entities", "RE": "relations", "EE": "relations",
    "COREF": "mentions", "QA": "answer", "TE": "label", "TXTCLASS": "label",
}

# 指标要按记录的 format 字段选，不能只按 task 选：
# PubMedQA 与 MedQA 同属 QA，但前者输出 {"label":...}、后者输出 {"answer":...}。
# 按 task 映射会把 PubMedQA 的 gold 读成空，导致其恒为满分并污染宏平均。
FORMAT_METRIC = {
    "bio": "entities", "span": "entities", "rel": "relations", "event": "events",
    "mention": "mentions", "label": "label", "text": "answer",
}


def norm(s):
    return re.sub(r"\s+", " ", str(s or "").strip().lower())


def extract_json(text):
    """从模型输出里抠出第一个完整 JSON 对象，容忍 ```json 包裹和前后缀文字。"""
    if isinstance(text, dict):
        return text
    s = str(text or "")
    s = re.sub(r"^```(?:json)?|```$", "", s.strip(), flags=re.M).strip()
    for i, ch in enumerate(s):
        if ch != "{":
            continue
        depth = 0
        for j in range(i, len(s)):
            if s[j] == "{":
                depth += 1
            elif s[j] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(s[i:j + 1])
                    except Exception:
                        break
    return None


def gold_record(x):
    g = x.get("gold")
    return extract_json(g) if isinstance(g, str) else g


def key_entities(rec):
    if not isinstance(rec, dict):
        return set()
    return {(norm(e.get("text")), norm(e.get("label"))) for e in rec.get("entities") or []
            if e.get("text")}


def key_relations(rec):
    if not isinstance(rec, dict):
        return set()
    return {(norm(r.get("head")), norm(r.get("relation")), norm(r.get("tail")))
            for r in rec.get("relations") or [] if r.get("head")}


def key_mentions(rec):
    if not isinstance(rec, dict):
        return set()
    return {norm(m) for m in rec.get("mentions") or [] if m}


def key_events(rec):
    if not isinstance(rec, dict):
        return set()
    return {(norm(e.get("type")), norm(e.get("trigger")), norm(e.get("theme")))
            for e in rec.get("events") or [] if e.get("type")}


def prf(tp, npred, ngold):
    if npred == 0 and ngold == 0:
        return 1.0, 1.0, 1.0
    p = tp / npred if npred else 0.0
    r = tp / ngold if ngold else 0.0
    f = 2 * p * r / (p + r) if (p + r) else 0.0
    return p, r, f


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    rows = json.load(open(args.input, encoding="utf-8"))
    acc = collections.defaultdict(lambda: collections.Counter())
    bad_json = collections.Counter()

    for x in rows:
        src = x.get("source", "?")
        task = x.get("task", "NER")
        pred = extract_json(x.get("prediction"))
        gold = gold_record(x)
        if pred is None:
            bad_json[src] += 1
            pred = {}
        # 优先按 format 选指标；取不到再回退到 task 映射
        fmt = (gold or {}).get("format") or (pred or {}).get("format")
        m = FORMAT_METRIC.get(fmt) or TASK_METRIC.get(task, "label")

        if m == "entities":
            P, G = key_entities(pred), key_entities(gold)
            a = acc[src]
            a["tp"] += len(P & G); a["npred"] += len(P); a["ngold"] += len(G); a["n"] += 1
        elif m == "relations":
            P, G = key_relations(pred), key_relations(gold)
            a = acc[src]
            a["tp"] += len(P & G); a["npred"] += len(P); a["ngold"] += len(G); a["n"] += 1
        elif m == "events":
            P, G = key_events(pred), key_events(gold)
            a = acc[src]
            a["tp"] += len(P & G); a["npred"] += len(P); a["ngold"] += len(G); a["n"] += 1
        elif m == "mentions":
            P, G = key_mentions(pred), key_mentions(gold)
            a = acc[src]
            a["tp"] += len(P & G); a["npred"] += len(P); a["ngold"] += len(G); a["n"] += 1
        elif m == "label":
            a = acc[src]
            a["n"] += 1
            a["correct"] += int(norm((pred or {}).get("label")) == norm((gold or {}).get("label")))
        else:
            a = acc[src]
            a["n"] += 1
            a["correct"] += int(norm((pred or {}).get("answer")) == norm((gold or {}).get("answer")))

    print("%-28s %-8s %6s %8s %8s %8s" % ("source", "metric", "n", "P", "R", "F1/Acc"))
    vals, detail = [], {}
    mtype = {}
    for src in sorted(acc):
        a = acc[src]
        if a["npred"] or a["ngold"]:
            p, r, f = prf(a["tp"], a["npred"], a["ngold"])
            met = "micro-F1"
        else:
            p = r = f = a["correct"] / max(1, a["n"])
            met = "acc/EM"
        vals.append(f)
        mtype[src] = met
        detail[src] = {"metric": met, "n": a["n"], "p": 100 * p, "r": 100 * r,
                       "f1": 100 * f, "tp": a["tp"], "npred": a["npred"], "ngold": a["ngold"]}
        print("%-28s %-8s %6d %8.2f %8.2f %8.2f" % (src, met, a["n"], 100 * p, 100 * r, 100 * f))

    print("\n%-28s %-8s %6s %8s %8s %8s" % ("MACRO", "", "", "", "", ""))
    macro = 100 * sum(vals) / max(1, len(vals))
    print("%d 个任务宏平均：%.2f  （口径混合，仅供内部对比，正文不要写成 average F1）"
          % (len(vals), macro))

    # 分组均值：抽取类 micro-F1 与 判别/问答类的 acc/EM 不能混着当一个数（回应 R1.4）
    print("\n按口径分组（正文应分组报告，不要只报一个混口径宏平均）：")
    groups = {"抽取类 micro-F1": [s for s in detail if mtype[s] == "micro-F1"],
              "判别/问答 acc-EM": [s for s in detail if mtype[s] != "micro-F1"]}
    group_out = {}
    for g, ss in groups.items():
        if not ss:
            continue
        gm = sum(detail[s]["f1"] for s in ss) / len(ss)
        group_out[g] = {"n_tasks": len(ss), "mean": gm}
        print("  %-20s n=%-2d 均值 %6.2f" % (g, len(ss), gm))

    if bad_json:
        print("\nJSON 解析失败的样本（按来源）：", dict(bad_json))
        print("  这本身就是一项指标：JSON 输出成功率 = %.2f%%"
              % (100 * (1 - sum(bad_json.values()) / max(1, len(rows)))))

    if args.out:
        json.dump({"per_source": detail, "macro": macro, "macro_definition": "mixed-metric",
                   "grouped": group_out,
                   "json_ok_rate": 100 * (1 - sum(bad_json.values()) / max(1, len(rows))),
                   "bad_json": dict(bad_json)},
                  open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print("->", args.out)


if __name__ == "__main__":
    main()
