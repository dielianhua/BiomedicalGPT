# -*- coding: utf-8 -*-
"""
把 schema v2.0（typed JSON）的预测转回**论文原始字符串格式**，再用 eval_original.py 打分。

为什么需要：
  eval_typed.py 算的是 schema 空间的 micro P/R/F1（entities / relations / mentions / label / answer），
  而论文 Table 6 以及 exp3–exp7 用的是 original_metrics.py 的那套：
    bio    → 词级 BIO 标签 macro-F1
    cls    → 归一化后的 label macro-F1
    em     → exact match
    entity → 方括号实体的集合级 F1
  两套口径在数值上不可比（同一份预测能差 5–10 分）。本脚本把 typed 预测"还原"成原始串，
  于是可以直接喂 eval_original.py，与论文数字对齐。

自校验：
  脚本会先用同一套转换器把 typed **金标**转回字符串，与数据里现成的 gold_legacy 逐条比对，
  并打印每个 source 的一致率。一致率不到 100% 的 source 会在报告里标出来。

用法：
  python convert_typed_to_legacy.py --input out/v2_full_plain_json1024/preds.json \
      --out out/legacy_from_typed/exp6/preds_legacy.json
"""

import argparse
import collections
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "code", "src")))

from eval_typed import extract_json  # noqa: E402  复用同一 JSON 抽取/修复逻辑


# --------------------------------------------------------------------------- #
# typed → legacy
# --------------------------------------------------------------------------- #
def bio_tags(tokens, entities):
    """把实体文本序列还原成词级 BIO 串：'VHL [O] ... RCC [B] ...'。

    按实体在列表中的先后顺序，在 token 流里贪心定位；找不到的实体跳过
    （与原始构造器一致：金标只标出实际出现的位置）。
    """
    tags = ["[O]"] * len(tokens)
    pos = 0
    for ent in entities:
        parts = str(ent).split()
        if not parts:
            continue
        k = len(parts)
        for i in range(pos, len(tokens) - k + 1):
            if tokens[i:i + k] == parts:
                tags[i] = "[B]"
                for j in range(1, k):
                    tags[i + j] = "[I]"
                pos = i + k
                break
    return " ".join("%s %s" % (t, g) for t, g in zip(tokens, tags))


def to_legacy(rec, fmt, tokens=None):
    """typed 记录 → 原文格式字符串。rec 为 None（解析失败）时返回空串。"""
    if not isinstance(rec, dict):
        return ""
    if fmt == "mention":
        return " ".join("[%s]" % m for m in (rec.get("mentions") or []))
    if fmt in ("span", "entities"):
        out = []
        for e in rec.get("entities") or []:
            text = e.get("text")
            if text is None:
                continue
            lab = e.get("label")
            out.append("[%s <%s>]" % (text, lab) if lab else "[%s]" % text)
        return " ".join(out)
    if fmt in ("rel", "relations"):
        out = []
        for r in rec.get("relations") or []:
            rel = r.get("relation") or r.get("type") or ""
            out.append("[<%s> <%s> <%s>]" % (r.get("head", ""), rel, r.get("tail", "")))
        return " ".join(out)
    if fmt in ("events", "event"):
        out = []
        for e in rec.get("events") or []:
            out.append("[<%s> <%s> <%s>]" % (e.get("type", ""), e.get("trigger", ""), e.get("theme", "")))
        return " ".join(out)
    if fmt == "label":
        lab = rec.get("label")
        return "" if lab is None else str(lab)
    if fmt in ("text", "answer"):
        return str(rec.get("answer") or "")
    if fmt == "bio":
        ents = [e.get("text") for e in (rec.get("entities") or []) if e.get("text")]
        return bio_tags(tokens or [], ents)
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="typed preds.json")
    ap.add_argument("--out", required=True, help="输出的 legacy preds.json")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    rows = json.load(open(args.input, encoding="utf-8"))

    out_rows = []
    ok = collections.Counter()
    tot = collections.Counter()
    parse_fail = collections.Counter()

    for x in rows:
        src = x.get("source", "?")
        gold = extract_json(x.get("gold")) or {}
        fmt = gold.get("format")
        tokens = (x.get("input") or "").split() if fmt == "bio" else None

        # 自校验：typed 金标 → 原文，应与现成的 gold_legacy 一致
        if x.get("gold_legacy") is not None:
            tot[src] += 1
            if to_legacy(gold, fmt, tokens) == x["gold_legacy"]:
                ok[src] += 1

        pred = extract_json(x.get("prediction"))
        if pred is None:
            parse_fail[src] += 1

        y = {k: x.get(k) for k in ("source", "task", "template_id") if k in x}
        y["prediction"] = to_legacy(pred, fmt, tokens)
        y["gold_legacy"] = x.get("gold_legacy")
        out_rows.append(y)

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    json.dump(out_rows, open(args.out, "w", encoding="utf-8"), ensure_ascii=False)

    if not args.quiet:
        bad = [(s, ok[s], tot[s]) for s in tot if ok[s] != tot[s]]
        print("转换 %d 条 -> %s" % (len(out_rows), args.out))
        print("自校验（typed 金标 → 原文 vs 现存 gold_legacy）：一致 %d/%d" %
              (sum(ok.values()), sum(tot.values())))
        if bad:
            print("  ⚠ 不一致的 source：")
            for s, a, b in sorted(bad, key=lambda z: z[1] / z[2]):
                print("    %-22s %d/%d (%.1f%%)" % (s, a, b, 100 * a / b))
        if parse_fail:
            print("  JSON 解析失败：", dict(parse_fail))


if __name__ == "__main__":
    main()
