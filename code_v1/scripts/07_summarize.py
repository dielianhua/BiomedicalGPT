#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""07 · 汇总 20 任务大表

扫描 results/*/test4800/metrics.json（20 任务）与 results/*/sci209/metrics.json
（SciFact 209），生成两张表：

    results/table_319.md   SciFact 按 319 计分，Average 用该口径的 macro
    results/table_209.md   SciFact 按 209 计分，Average = (19 任务 + SciFact209)/20

用法：
    python 07_summarize.py
    python 07_summarize.py --with-gpt4o 56.56   # 额外插入一个只有总分的列
"""
import argparse
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RES = os.path.join(ROOT, "results")

CATS = [("NER", "NCBI-disease"), ("NER", "BC5CDR"), ("NER", "AnEM"), ("NER", "BioNLP-2009"),
        ("NER", "BioNLP-2011-GE"), ("NER", "BioNLP-2011-ID"), ("NER", "BioNLP-2011-REL"),
        ("NER", "BioNLP-2013-CG"), ("NER", "BioNLP-2013-GE"), ("NER", "BioNLP-2013-GRO"),
        ("NER", "BioRED"), ("QA", "PubMedQA-labeled"), ("QA", "MedQA"), ("TE", "SciFact"),
        ("TXTCLASS", "MedDialog"), ("RE", "BC5CDR-RE"), ("RE", "BioInfer-RE"),
        ("COREF", "AnEM-COREF"), ("COREF", "MLEE-COREF"), ("EE", "MLEE-EE")]


def load(tag, sub):
    p = os.path.join(RES, tag, sub, "metrics.json")
    if not os.path.exists(p):
        return None
    return json.load(open(p, encoding="utf-8"))


def discover():
    """找出所有同时具备 20 任务结果的结果目录"""
    out = []
    if not os.path.isdir(RES):
        return out
    for tag in sorted(os.listdir(RES)):
        d = os.path.join(RES, tag)
        if not os.path.isdir(d):
            continue
        if load(tag, "test4800"):
            out.append(tag)
    return out


def build(tags, sf_from, title, note):
    L = ["# " + title + "\n", note + "\n",
         "| Category | Dataset | " + " | ".join(tags) + " |",
         "|---|---|" + "---:|" * len(tags)]
    b = {t: load(t, "test4800") for t in tags}
    s = {t: load(t, "sci209") for t in tags}
    for c, d in CATS:
        cells = []
        for t in tags:
            m = (s[t] if (d == "SciFact" and sf_from == "209") else b[t])
            v = m["per_source"].get(d, {}).get("f1") if m else None
            cells.append("%.2f" % v if v is not None else "—")
        L.append("| %s | %s | %s |" % (c, d, " | ".join(cells)))

    avgs = []
    for t in tags:
        if not b[t]:
            avgs.append("—"); continue
        if sf_from == "209":
            if not s[t]:
                avgs.append("—"); continue
            tot = sum(b[t]["per_source"].get(d, {}).get("f1", 0) for _, d in CATS if d != "SciFact")
            avgs.append("%.2f" % ((tot + s[t]["per_source"]["SciFact"]["f1"]) / 20))
        else:
            avgs.append("%.2f" % b[t]["macro"])
    L.append("| **Average** | — | " + " | ".join(avgs) + " |")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tags", nargs="*", default=None, help="指定列顺序（默认自动发现）")
    args = ap.parse_args()

    tags = args.tags or discover()
    if not tags:
        raise SystemExit("results/ 下没有找到任何 20 任务结果（results/<tag>/test4800/metrics.json）")

    t319 = build(tags, "319", "20 任务大表 · SciFact 按 319 条计分",
                 "SciFact 取 20 任务测试集中的 319 条；Average 为 20 任务等权。")
    t209 = build(tags, "209", "20 任务大表 · SciFact 按 209 条计分",
                 "SciFact 取 `sci209` 单独推理结果（209 条，剔除空 evidence）；"
                 "**Average = (19 任务 + SciFact209) / 20**。")

    p319 = os.path.join(RES, "table_319.md")
    p209 = os.path.join(RES, "table_209.md")
    open(p319, "w", encoding="utf-8").write(t319 + "\n")
    open(p209, "w", encoding="utf-8").write(t209 + "\n")
    print(t319)
    print()
    print(t209)
    print("\n已写入：\n  %s\n  %s" % (p319, p209))


if __name__ == "__main__":
    main()
