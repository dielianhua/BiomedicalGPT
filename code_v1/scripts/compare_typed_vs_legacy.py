# -*- coding: utf-8 -*-
"""
把 typed（schema v2.0）预测转成论文原始串，用论文指标重评，并与 typed 指标逐项对照。

流程（每个 run 各做一次）：
  preds.json ──convert_typed_to_legacy.py──> preds_legacy.json
             ──code/src/eval_original.py──> metrics_legacy.json
  再与已有的 typed metrics.json 对比。

用法：
  python compare_typed_vs_legacy.py \
      --out out/legacy_from_typed \
      --run "exp6|out/v2_full_plain_json1024/preds.json|out/v2_full_plain_json1024/metrics.json" \
      --run "exp7|out/v2_full_plain_plain1024/preds.json|out/v2_full_plain_plain1024/metrics.json" \
      --md ../../outputs/tables/typed_vs_legacy_metric.md
"""

import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
CONV = os.path.join(HERE, "convert_typed_to_legacy.py")
EVAL = os.path.abspath(os.path.join(HERE, "..", "code", "src", "eval_original.py"))


def sh(args):
    r = subprocess.run([PY] + args, capture_output=True, text=True, cwd=HERE)
    if r.returncode != 0:
        raise RuntimeError("命令失败: %s\n%s" % (" ".join(args), r.stderr[-800:]))
    return r.stdout.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "out/legacy_from_typed"))
    ap.add_argument("--run", action="append", required=True,
                    help="tag|typed_preds.json|typed_metrics.json，可重复")
    ap.add_argument("--md", default="")
    ap.add_argument("--detail", default="", help="额外打印逐任务明细的 run tag（逗号分隔）")
    args = ap.parse_args()

    runs = []
    for spec in args.run:
        tag, preds, tmetrics = spec.split("|")
        d = os.path.join(args.out, tag)
        os.makedirs(d, exist_ok=True)
        leg_preds = os.path.join(d, "preds_legacy.json")
        leg_metrics = os.path.join(d, "metrics_legacy.json")
        sh([CONV, "--input", preds, "--out", leg_preds, "--quiet"])
        sh([EVAL, "--input", leg_preds, "--out", leg_metrics])
        runs.append({
            "tag": tag,
            "typed": json.load(open(tmetrics, encoding="utf-8")),
            "legacy": json.load(open(leg_metrics, encoding="utf-8")),
        })

    L = ["# typed 指标 vs 论文原始指标（同一份预测）\n",
         "typed = `eval_typed.py`（schema 空间 micro P/R/F1）；legacy = `eval_original.py`（论文 Table 6 口径）。",
         "两者用**同一份 preds**，只换指标实现。\n",
         "| run | typed macro | legacy macro | Δ | 最大单任务差 |",
         "|---|---:|---:|---:|---:|"]
    for r in runs:
        t, g = r["typed"], r["legacy"]
        tp, lp = t["per_source"], g["per_source"]
        diffs = [abs(lp[k]["f1"] - tp[k]["f1"]) for k in lp if k in tp]
        L.append("| %s | %.2f | **%.2f** | %+.2f | %.2f |" % (
            r["tag"], t["macro"], g["macro"], g["macro"] - t["macro"], max(diffs) if diffs else 0))

    detail = [x.strip() for x in args.detail.split(",") if x.strip()]
    for r in runs:
        if not any(r["tag"].startswith(d) for d in detail):
            continue
        tp, lp = r["typed"]["per_source"], r["legacy"]["per_source"]
        rows = sorted(((k, tp[k]["f1"], lp[k]["f1"], tp[k]["metric"], lp[k]["metric"])
                       for k in lp if k in tp), key=lambda x: -abs(x[2] - x[1]))
        L += ["", "## 逐任务：%s（按差绝对值排序）\n" % r["tag"],
              "| 任务 | typed | legacy | Δ | typed 指标 | legacy 指标 |",
              "|---|---:|---:|---:|---|---|"]
        for k, a, b, m1, m2 in rows:
            L.append("| %s | %.2f | %.2f | %+.2f | %s | %s |" % (k, a, b, b - a, m1, m2))

    txt = "\n".join(L) + "\n"
    print(txt)
    if args.md:
        os.makedirs(os.path.dirname(os.path.abspath(args.md)), exist_ok=True)
        open(args.md, "w", encoding="utf-8").write(txt)
        print("-> %s" % args.md)


if __name__ == "__main__":
    main()
