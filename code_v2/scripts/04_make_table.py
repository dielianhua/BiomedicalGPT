# -*- coding: utf-8 -*-
"""Rebuild the 3-model x mixed9 (20-task) table from shipped predictions.

No GPU needed: it re-scores the stored `preds_legacy.json` only.

    python scripts/04_make_table.py
    python scripts/04_make_table.py --out tables/3models_mixed9_20tasks_final.md

Requires: numpy, scikit-learn, tqdm (same env used for evaluation).
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
LIB = os.path.join(HERE, 'lib')
sys.path.insert(0, LIB)
import eval_original as EO  # noqa: E402

PLAIN = 'plain'
P3 = 'p3'
DS = 'ds10k_v1match'
MODELS = [PLAIN, P3, DS]
LABEL = {PLAIN: 'plain', P3: 'p3', DS: 'DS-10K (v1match)'}
JUDGE = {'MedQA', 'PubMedQA-labeled', 'MedDialog', 'SciFact'}


def scifact_209(preds_path, idx):
    """F1 of SciFact on the 209 evidence-bearing items, paper metric."""
    preds = json.load(open(preds_path, encoding='utf-8'))
    sub = [preds[i] for i in idx]
    per = EO.score_rows(sub)
    return per['SciFact']['f1'], len(sub)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pkg', default=PKG)
    ap.add_argument('--out', default=os.path.join(PKG, 'tables', '3models_mixed9_20tasks_final.md'))
    args = ap.parse_args()

    idx = json.load(open(os.path.join(args.pkg, 'data/test/v2_scifact209_idx.json')))
    data = {}
    for m in MODELS:
        mp = os.path.join(args.pkg, 'results', m, 'metrics_legacy.json')
        pp = os.path.join(args.pkg, 'predictions', m, 'preds_legacy.json')
        met = json.load(open(mp, encoding='utf-8'))
        per = {k: v['f1'] for k, v in met['per_source'].items()}
        sf209, n209 = scifact_209(pp, idx)
        per209 = dict(per)
        per209['SciFact'] = sf209
        data[m] = dict(per=per, macro=met['macro'], sf209=sf209, n209=n209,
                       macro209=sum(per209.values()) / len(per209))

    tasks = sorted(data[P3]['per'].keys(), key=lambda t: -data[P3]['per'][t])
    lines = []
    lines.append('| task | ' + ' | '.join(LABEL[m] for m in MODELS) + ' |')
    lines.append('|---|' + '---:|' * len(MODELS))
    for t in tasks:
        lines.append('| %s | %s |' % (t, ' | '.join('%.2f' % data[m]['per'][t] for m in MODELS)))
    lines.append('| **macro (319)** | %s |' % ' | '.join('**%.2f**' % data[m]['macro'] for m in MODELS))
    lines.append('| **macro (209)** | %s |' % ' | '.join('**%.2f**' % data[m]['macro209'] for m in MODELS))
    body = '\n'.join(lines)
    print(body)

    print('\nsummary:')
    for m in MODELS:
        ext = [v for k, v in data[m]['per'].items() if k not in JUDGE]
        jud = [v for k, v in data[m]['per'].items() if k in JUDGE]
        print('  %-16s macro319=%.2f macro209=%.2f SciFact@209=%.2f (n=%d) '
              'extraction=%.2f judgment=%.2f'
              % (LABEL[m], data[m]['macro'], data[m]['macro209'], data[m]['sf209'],
                 data[m]['n209'], sum(ext) / len(ext), sum(jud) / len(jud)))

    if args.out:
        os.makedirs(os.path.dirname(args.out), exist_ok=True)
        with open(args.out, 'w', encoding='utf-8') as f:
            f.write('# 3 models x mixed9 (20 tasks) — regenerated from predictions\n\n')
            f.write(body + '\n')
        print('\nwritten:', args.out)


if __name__ == '__main__':
    main()
