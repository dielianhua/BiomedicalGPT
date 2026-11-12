# -*- coding: utf-8 -*-
"""Score one predictions file with both metrics.

    python scripts/03_eval.py --preds preds/ds10k_v1match/preds.json --outdir preds/ds10k_v1match

Produces, next to the predictions:
    metrics_typed.json    micro-F1 per task (eval_typed.py)
    preds_legacy.json     predictions converted back to the legacy answer format
    metrics_legacy.json   paper metric: entity-F1 / label-F1 / acc-EM, macro over 20 tasks

Requires: numpy, scikit-learn, tqdm.
"""
import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, 'lib')


def run(args):
    print('  $', ' '.join(os.path.basename(a) if a.endswith('.py') else a for a in args))
    subprocess.run(args, check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--preds', required=True, help='typed preds.json produced by 02_infer.sh')
    ap.add_argument('--outdir', default='')
    args = ap.parse_args()

    preds = os.path.abspath(args.preds)
    outdir = os.path.abspath(args.outdir or os.path.dirname(preds))
    os.makedirs(outdir, exist_ok=True)

    typed = os.path.join(outdir, 'metrics_typed.json')
    legacy_preds = os.path.join(outdir, 'preds_legacy.json')
    legacy = os.path.join(outdir, 'metrics_legacy.json')

    run([sys.executable, os.path.join(LIB, 'eval_typed.py'), '--input', preds, '--out', typed])
    run([sys.executable, os.path.join(LIB, 'convert_typed_to_legacy.py'),
         '--input', preds, '--out', legacy_preds])
    run([sys.executable, os.path.join(LIB, 'eval_original.py'),
         '--input', legacy_preds, '--out', legacy])

    print('\n  typed  :', typed)
    print('  legacy :', legacy)


if __name__ == '__main__':
    main()
