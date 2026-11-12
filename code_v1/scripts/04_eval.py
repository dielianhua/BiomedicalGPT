# -*- coding: utf-8 -*-
"""
用**原始评测代码**给 mix3 打分。

直接 import 项目根目录的 evaluation_medinst32.py，调用它自己的
post_entity / entity_level_f1 / label_level_f1 / word_level_f1 / exact_match_score / post_bio，
任务→指标映射也照它的 cls / em / bio / entity 列表。

用法：
  python eval_with_orig.py --input out/mix3_v4full/preds.json --out out/mix3_v4full/metrics.json
"""

import argparse
import collections
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..")))
import original_metrics as O  # noqa: E402


def metric_of(src):
    if src in O.bio:
        return "bio"
    if src in O.cls:
        return "cls"
    if src in O.em:
        return "em"
    return "entity"


TOKTAG = re.compile(r"(\S+)\s*\[(B|I|O)\]")


def parse_toktag(s):
    """把 'word [B] word [O]' 拆成 (tokens, tags)，与 O.post_bio 的标签集合一致。"""
    toks, tags = [], []
    for m in TOKTAG.finditer(s or ""):
        toks.append(m.group(1))
        tags.append("[%s]" % m.group(2))
    return toks, tags


def align_bio_tags(gold, pred):
    """按词对齐后再比标签。

    原脚本直接按长度截断；若模型漏掉句首几个词，后面每个标签都会错位。
    这里先在金标词序列里定位预测的起点，再把标签搬到对应位置；
    被漏掉的句首沿用 '[N]'（不计分、也不给白送 [O] 的分）。
    """
    gt, gtg = parse_toktag(gold)
    pt, ptg = parse_toktag(pred)
    if not gt:
        return gtg, []
    k = None
    for i in range(min(len(gt), 15)):
        if pt and gt[i:i + 3] == pt[:3]:
            k = i
            break
    if k is None:                          # 对不上就退回原做法
        q = (ptg[:len(gt)] + ["[N]"] * len(gt))[:len(gt)]
        return gtg, q
    q = ["[N]"] * len(gt)
    for j, t in enumerate(ptg):
        if k + j < len(gt):
            q[k + j] = t
    return gtg, q


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--bio-align", choices=["word", "naive"], default="word",
                    help="BIO 任务标签对齐方式：word=按词对齐（默认），naive=原脚本盲截断")
    args = ap.parse_args()

    rows = json.load(open(args.input, encoding="utf-8"))
    by = collections.defaultdict(list)
    for x in rows:
        by[x["source"]].append(x)

    per = {}
    for src, items in sorted(by.items()):
        k = metric_of(src)
        preds = [x.get("prediction") or "" for x in items]
        golds = [x.get("gold_legacy") or "" for x in items]

        if k == "bio":
            ts, ps = [], []
            for g, p in zip(golds, preds):
                if args.bio_align == "word":
                    t, q = align_bio_tags(g, p)
                else:                      # naive：原脚本做法，按长度盲截断
                    t, q = O.post_bio(g, p)
                    if len(t) > len(q):
                        q = q + ["[N]"] * (len(t) - len(q))
                    q = q[:len(t)]
                ts.extend(t)
                ps.extend(q)
            val = O.label_level_f1(ts, ps)
        elif k == "cls":
            ts = [O.normalize_answer(g) for g in golds]
            ps = [O.normalize_answer(p) for p in preds]
            val = O.label_level_f1(ts, ps)
        elif k == "em":
            val = 100 * sum(O.exact_match_score(p, g) for g, p in zip(golds, preds)) / len(preds)
        else:
            sc = []
            for g, p in zip(golds, preds):
                t, q = O.post_entity(g, p)
                if not t and not q:
                    sc.append(100.0 * O.exact_match_score(p, g))
                else:
                    sc.append(O.entity_level_f1(t, q))
            val = sum(sc) / len(sc)

        per[src] = {"f1": round(val, 2), "n": len(items), "metric": k}

    macro = sum(v["f1"] for v in per.values()) / max(1, len(per))
    out = {"macro": round(macro, 2), "n_tasks": len(per), "per_source": per}
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    json.dump(out, open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("macro %.2f（%d 任务）-> %s" % (out["macro"], len(per), args.out))


if __name__ == "__main__":
    main()
