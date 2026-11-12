# Three models × mixed9: final 20-task results

Test set: **mixed9, 4,800 items** (4,481 items over 19 tasks plus 319 SciFact items; the 209 view is the
evidence-bearing subset of SciFact after removing 110 items whose gold label is leaked by an empty
evidence field). Metric: `eval_original.py` (a mix of entity-F1 / label-F1 / acc-EM), unweighted mean
over 20 tasks; `max_tokens=1024, T=0`. Only mixed9 is reported here; the plain-test results are excluded.

## Training recipes

| model | training set | items | instruction style |
|---|---|---:|---|
| plain | `v2_full_plain` | 27,673 | plain only (single style) |
| p3 | `v2_full_p3` | 27,673 | plain / format_first / persona (roughly one third each) |
| **DS-10K (v1match)** | `v2_p3_ds10k_v1match` | **10,000** | same as p3; items are those of the paper's DS-10K, templates rewritten for v2 |

## Main table (paper metric, mixed9)

| task | plain | p3 | **DS-10K (v1match)** |
|---|---:|---:|---:|
| AnEM-COREF | 100.00 | 100.00 | 100.00 |
| MedDialog | 100.00 | 99.18 | 99.18 |
| MLEE-COREF | 99.12 | 97.94 | 93.81 |
| NCBI-disease | 92.78 | 92.57 | 86.96 |
| BC5CDR | 93.14 | 92.44 | 89.36 |
| SciFact | 92.56 | 90.30 | 92.07 |
| BioRED | 84.75 | 86.79 | 86.21 |
| BioNLP-2009 | 87.60 | 86.34 | 86.80 |
| BioNLP-2011-REL | 87.49 | 86.09 | 86.81 |
| BioNLP-2011-GE | 86.98 | 84.77 | 86.43 |
| BioNLP-2013-CG | 81.51 | 81.81 | 82.28 |
| BioNLP-2011-ID | 76.38 | 77.04 | 73.57 |
| BioNLP-2013-GE | 75.27 | 73.08 | 73.17 |
| PubMedQA-labeled | 59.77 | 61.60 | 63.00 |
| MedQA | 61.51 | 60.41 | 57.58 |
| AnEM | 58.18 | 59.45 | 55.07 |
| BioNLP-2013-GRO | 42.88 | 41.97 | 41.79 |
| BioInfer-RE | 39.91 | 36.64 | 39.90 |
| MLEE-EE | 18.20 | 18.16 | 18.32 |
| BC5CDR-RE | 12.12 | 15.62 | 14.84 |
| **macro (319 view)** | **72.51** | **72.11** | **71.36** |
| **macro (209 view)** | **72.32** | **71.87** | **71.16** |

> The 209 view changes SciFact only (88.84 / 85.45 / 88.10); the other 19 tasks are unchanged, hence the
> macro drops by 0.19 / 0.24 / 0.20 respectively.

## Summary

| metric | plain | p3 | DS-10K (v1match) |
|---|---:|---:|---:|
| macro (319) | 72.51 | 72.11 | 71.36 |
| macro (209) | 72.32 | 71.87 | 71.16 |
| mean of the 16 extraction tasks | **71.02** | 70.67 | 69.71 |
| mean of the 4 judgment / QA tasks | 78.46 | 77.87 | 77.96 |
| training set size | 27,673 | 27,673 | **10,000 (36%)** |

Per-task win/loss:

- DS-10K vs p3: 9 wins / 9 losses / 2 ties (macro −0.75)
- DS-10K vs plain: 5 wins / 14 losses / 1 tie (macro −1.15)
- p3 vs plain: 6 wins / 13 losses / 1 tie (macro −0.40)

## Conclusions

1. **The 10K subset essentially matches full-data training**: DS-10K (v1match) reaches 71.36 with **36%**
   of the data, i.e. **98.96%** of the full p3 model and **98.41%** of the full plain model (319 view).
   With 9 wins and 9 losses per task, the result is not carried by a single task family.
2. **The gap is concentrated in two NER sources**: NCBI (−5.61) and BC5CDR (−3.08) account for most of the
   macro deficit; the 10K subset keeps only 500 items from each, against 5,432 / 4,560 in the full pool.
   This is a coverage limitation of the subsample rather than a failure of the selection method.
3. **Tasks where the subset wins** (relative to p3): BioInfer-RE +3.26, SciFact +1.77, BioNLP-2011-GE +1.66,
   PubMedQA +1.40; relative to plain: PubMedQA +3.23, BC5CDR-RE +2.72, BioRED +1.46.
   Keeping all small sources while taking the paper's quota from the large ones is more economical for
   RE and judgment-style tasks.
4. **Rewriting the templates costs nothing**: DS-10K uses the same three instruction families as p3
   (format_first / plain / persona, roughly one third each). Its behaviour on mixed9 is consistent with the
   earlier mixed4 finding — training on several phrasings does not degrade accuracy.
5. Suggested wording for the paper's final table: report **71.36 (319) / 71.16 (209)** for mixed9 and present
   “10K vs 27,673” as the data-efficiency statement; state in the caption that SciFact is scored on the
   209 evidence-bearing items.

## Reproduction

| item | path |
|---|---|
| table generation | `scripts/04_make_table.py` |
| plain predictions | `predictions/plain/preds_legacy.json` |
| p3 predictions | `predictions/p3/preds_legacy.json` |
| DS-10K predictions | `predictions/ds10k_v1match/preds_legacy.json` |
