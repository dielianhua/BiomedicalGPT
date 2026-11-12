# 3 models × mixed9 — reproducible package

Everything needed to reproduce the 20-task table **plain / p3 / DS-10K(v1match)** on the
**mixed9** test set (4,800 items). Predictions are shipped, so the table can be rebuilt without a GPU.

| model | training data | size | macro (319) | macro (209) |
|---|---|---:|---:|---:|
| plain | `data/train/v2_plain_27k.json` | 27,673 | **72.51** | **72.32** |
| p3 | `data/train/v2_p3_27k.json` | 27,673 | **72.11** | **71.87** |
| DS-10K (v1match) | `data/train/v2_ds10k_v1match_10k.json` | **10,000** | **71.36** | **71.16** |

Full 20-task table: `tables/3models_mixed9_20tasks_final.md` (regenerated) and
`tables/report.md` (analysis).

---

## 1. Layout

```
code_v2/
├── README.md
├── manifest.json                    # md5 / bytes / record count for every shipped file
├── data/
│   ├── train/
│   │   ├── v2_plain_27k.json           # 27,673  single instruction style
│   │   ├── v2_p3_27k.json              # 27,673  three instruction families (~1/3 each)
│   │   └── v2_ds10k_v1match_10k.json   # 10,000  DS-10K subsample, v2 templates
│   └── test/
│       ├── v2_test_mixed9_4800.json    # 4,800   19 tasks × 4,481 + SciFact 319
│       ├── v2_test_plain_4800.json     # 4,800   same items, single instruction (not used here)
│       └── v2_scifact209_idx.json      # positions of the 209 evidence-bearing SciFact items
│   └── SOURCES.md               # source corpora: task, accession URL, licence, reference
├── docs/
│   ├── data_fields.md               # combined v1/v2 data-field table (Table 1)
│   ├── data_fields.xlsx             # the same table in spreadsheet form (active preview)
│   ├── dataset.md                   # templates, prompt examples, distributions, conversion rules
│   ├── pipeline.md                  # paper-ready methods text + figure caption
│   ├── pipeline.drawio              # editable pipeline figure (draw.io / diagrams.net)
│   └── pipeline.svg                 # vector preview of the same figure
├── predictions/
│   ├── plain/preds_legacy.json
│   ├── p3/preds_legacy.json
│   └── ds10k_v1match/preds_legacy.json
├── results/
│   ├── plain/{metrics_legacy.json, metrics_typed.json}
│   ├── p3/{metrics_legacy.json, metrics_typed.json}
│   └── ds10k_v1match/{metrics_legacy.json, metrics_typed.json}
├── tables/
│   ├── 3models_mixed9_20tasks_final.md
│   ├── 3models_mixed9_20tasks_final.xlsx   # Excel version of the table
│   ├── report.md                           # results, conclusions (English)
│   └── analysis.md                         # qualitative discussion (English)
└── scripts/
    ├── 01_train.sh                  # LoRA fine-tune + merge adapter
    ├── 02_infer.sh                  # vLLM serving + prediction dump
    ├── 03_eval.py                   # typed + legacy metrics for one preds.json
    ├── 04_make_table.py             # rebuild the 20-task table (CPU only)
    ├── md2xlsx.py                   # Markdown table -> formatted .xlsx
    ├── build_ds10k_v1match.py       # rebuild the DS-10K subsample from the paper subset
    ├── lib/
    │   ├── eval_original.py         # paper metric (entity-F1 / label-F1 / acc-EM)
    │   ├── original_metrics.py
    │   ├── eval_typed.py            # typed metric (micro-F1)
    │   ├── convert_typed_to_legacy.py
    │   └── gen_predictions.py
    └── train/
        ├── 11fintune_all_lang_med.sh
        ├── finetune_newmed.py
        ├── merge_model.py
        └── utils/
```

## 2. Data

The full description — instruction families, prompt examples for all nine phrasings, per-task and
per-family distributions, and the legacy-to-typed conversion rules — is in **`docs/dataset.md`**.
The summary below covers only what the table needs. Each training record carries a `source_url`
field; `data/SOURCES.md` is the single authority for those URLs.

**Test set.** `v2_test_mixed9_4800.json` is 4,800 items over 20 tasks; every item is rendered with one of
nine instruction families (525–544 per family) in a fixed mixed order. Two SciFact views are reported:

* `319` — all SciFact items (the official dev split held out from training).
* `209` — the 319 minus the 110 items whose `Evidence:` field is empty. Those 110 have a constant
  gold label (`Neutral`), i.e. the answer is leaked by the input, so the paper metric is reported on 209.
  `data/test/v2_scifact209_idx.json` stores their positions in the 4,800-item file.

**Training sets.** All use the same 20-task pool in the v2 typed schema (`output` is a JSON object,
`output_legacy` keeps the original answer string).

| file | n | instruction families |
|---|---:|---|
| `v2_plain_27k.json` | 27,673 | `plain` only |
| `v2_p3_27k.json` | 27,673 | `plain` / `format_first` / `persona` |
| `v2_ds10k_v1match_10k.json` | 10,000 | same three families, drawn from the DS-10K subsample |

**DS-10K subsample provenance.** Node-for-node the samples of the paper's `v1_DS_10000`:
9,696 items were matched into the v2 pool by exact `(input, answer)` after per-source indexing, and
304 SciFact items were matched after stripping the `\nCited abstract: …` suffix that the original
SciFact training file appends when `Evidence:` is empty. Every record carries
`from_v1=true` and `text_mode ∈ {v1_exact, v2_no_cited_abstract}`. Rebuild with
`python scripts/build_ds10k_v1match.py` if the source pool is available.

## 3. Models

Merged models are **not** shipped (≈30 GB each). Leaves:

| leaf | path |
|---|---|
| `plain` | `models/Meta-Llama-3.1-8B-Instruct_v2_full_plain` |
| `p3` | `models/Meta-Llama-3.1-8B-Instruct_v2_full_p3` |
| `ds10k_v1match` | `models/Meta-Llama-3.1-8B-Instruct_v2_p3_ds10k_v1match` |

Training recipe, identical for the three (matches the paper):

* LoRA `r=8`, `alpha=8`, 7 projection layers (**not** `lm_head`), 20,971,520 trainable params
* batch 4 (micro 1), 3 epochs, `cutoff_len=2048`, lr 1e-4 cosine, warmup 0.01
* steps: 27,673 samples → 20,754; 10,000 samples → 7,500

Retrain:

```bash
bash scripts/01_train.sh data/train/v2_ds10k_v1match_10k.json ds10k_v1match
```

## 4. Inference and scoring

```bash
# greedy decoding, max_tokens=1024, max_model_len=32768
bash scripts/02_infer.sh ds10k_v1match data/test/v2_test_mixed9_4800.json preds/ds10k_v1match

python scripts/03_eval.py --preds preds/ds10k_v1match/preds.json --outdir preds/ds10k_v1match
# -> metrics_typed.json, preds_legacy.json, metrics_legacy.json
```

`03_eval.py` calls `eval_typed.py` (micro-F1), converts the typed answers back to the legacy format,
then calls `eval_original.py` (paper metric). Both use `python`, so run it in an environment with
`numpy`, `scikit-learn`, `tqdm`.

## 5. Rebuild the table (no GPU)

```bash
python scripts/04_make_table.py
# Excel version (needs openpyxl)
python scripts/md2xlsx.py tables/3models_mixed9_20tasks_final.md \
                          tables/3models_mixed9_20tasks_final.xlsx
```

It only re-scores the shipped `predictions/*/preds_legacy.json`: 19 tasks come straight from
`results/*/metrics_legacy.json`, SciFact is recomputed for both views (319 and the 209 subset).
A qualitative discussion of the comparison is in `tables/analysis.md`.
Expected output:

```
plain            macro319=72.51 macro209=72.32 SciFact@209=88.84 extraction=71.02 judgment=78.46
p3               macro319=72.11 macro209=71.87 SciFact@209=85.45 extraction=70.67 judgment=77.87
DS-10K (v1match) macro319=71.36 macro209=71.16 SciFact@209=88.10 extraction=69.71 judgment=77.96
```

## 6. Verified

| check | result |
|---|---|
| `03_eval.py` on `predictions/ds10k_v1match` (re-run whole chain) | legacy 71.36, typed 71.44 — identical to `results/` |
| `03_eval.py` on the plain model's typed preds | legacy 72.51, typed 72.83 — identical, all 20 tasks bit-equal |
| `04_make_table.py` | reproduces every cell of the shipped table |
| `manifest.json` | md5 + record count for all 37 shipped files |

## 7. Reading the numbers

* DS-10K uses 36% of the data and reaches 98.96% of p3's score (71.36 / 72.11).
* The gap is concentrated in two NER sources: NCBI-disease (−5.61) and BC5CDR (−3.08); in the 10K
  subsample they only keep 500 items each, versus 5,432 / 4,560 in the full pool.
* Reverse wins versus p3: BioInfer-RE +3.26, SciFact +1.77, BioNLP-2011-GE +1.66, PubMedQA +1.40.
* Per-task wins of DS-10K vs p3: 9 win / 9 lose / 2 tie — no single task family carries the result.
