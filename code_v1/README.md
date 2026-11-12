# Biomedical Instruction Dataset — Data Selection (DS) Pipeline

A reproducible pipeline that builds a biomedical instruction-tuning dataset from 20 biomedical
NLP tasks, selects a subset with **instruction-conditioned loss (the DS score)**, fine-tunes
Llama-3.1-8B-Instruct with LoRA, and evaluates on the same 20 tasks.

This directory is **self-contained**: data, scripts and evaluation results are all included.
Follow the steps below to run the whole pipeline from scratch.

---

## 1. Repository layout

```
code_v1/
├── README.md
├── data/
│   ├── SOURCES.md               provenance: task, accession URL, licence, reference
│   ├── train/
│   │   ├── v1_DS_10k.json          10,000 samples (top-10K by DS score)
│   │   ├── v1_DS_20k.json          20,000 samples
│   │   └── v1_DS_27k.json          27,673 samples (full pool)
│   └── test/
│       ├── test_4800.json       20-task test set (4,800 samples, see §4)
│       └── test_scifact_209.json  SciFact evidence-bearing subset (209 samples)
├── scripts/
│   ├── 01_ds_score.py           DS scoring (instruction-conditioned loss)
│   ├── 02_select_subset.py      Threshold-based subset selection
│   ├── 03_infer.py              Batched inference via vLLM
│   ├── 04_eval.py               Evaluation (entity-F1 / label-F1 / EM)
│   ├── 05_train.sh              LoRA fine-tuning + merge
│   ├── 06_run_eval.sh           One-command inference + evaluation
│   ├── 07_summarize.py          Build the 20-task summary tables
│   ├── finetune_newmed.py       Training entry point (called by 05_train.sh)
│   ├── merge_model.py           LoRA merge utility
│   ├── original_metrics.py      Metric implementations (used by 04_eval.py)
│   └── utils/                   Training dependencies (prompter, etc.)
├── models/                      Training outputs (created at runtime)
└── results/
    ├── table_319.md             20-task table (SciFact = 319)
    ├── table_209.md             **20-task table (SciFact = 209) — main result**
    ├── table_319.xlsx           Excel version of the table above
    ├── table_209.xlsx           Excel version of the main result
    ├── analysis.md              analysis of the comparison (English, qualitative)
    └── <tag>/<test>/            preds.json + metrics.json per model
```

---

## 2. Environment

```bash
conda create -n ds python=3.10
conda activate ds
pip install torch transformers peft datasets accelerate \
            sentencepiece protobuf scikit-learn rouge_score tqdm \
            vllm openai
```

- A single 4090 24G GPU is sufficient for both training and inference (8B model, LoRA).
- Training on the 10K subset (3 epochs) takes roughly 3 hours.
- Inference over 4,800 samples takes about 12 minutes with vLLM at concurrency 32.

---

## 3. Data sources

The 20 source corpora, their task type, accession URL, licence and the matching entry in the
manuscript's reference list are documented once in **[`data/SOURCES.md`](data/SOURCES.md)**.
Each training record carries a `source_url` field alongside `original_file`; both resolve to
the corpus names used in that table.

**Note**: the MLEE corpora are released under **CC BY-NC-SA 3.0**, which prohibits commercial
use; anyone reusing this dataset must comply with that restriction. All other corpora are used
under their own original terms. This project redistributes the data under those original
licences only and grants no additional rights.

---

## 4. Test sets

| File                    | Samples   | Description                                                                                                                                                                                                                    |
| ----------------------- | ---------:| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `test_4800.json`        | **4,800** | Full 20-task test set (the original 5,670 items after de-duplication and format unification). Each item has `instruction` / `input` / `output` / `history`.                                                                    |
| `test_scifact_209.json` | **209**   | SciFact subset restricted to evidence-bearing items (138 Supports + 71 Refutes). The 110 items with an empty `Evidence:` field are excluded because their gold label is invariably `Neutral`, which constitutes label leakage. |

The `history` field holds **per-task, fixed 2-shot in-context examples**, formatted as
`[[example_input_1, answer_1], [example_input_2, answer_2]]`. Whether it is used is controlled by
`03_infer.py --use-history`.

---

## 5. Pipeline

### 5.1 DS scoring

The DS score is the negative log-likelihood of the target output, conditioned on the instruction
and input. The scoring code follows the official implementation in
[BiomedicalGPT](https://github.com/dielianhua/BiomedicalGPT) and is bundled here as
`01_ds_score.py`.

```bash
cd scripts

# 1) Score every sample in the full pool (writes a .pt file)
#    --mod cherry is REQUIRED: it is the only mode that stores per-token losses
#    (token_loss) that step 2 reads. --mod pre only stores ppl / sentence
#    embeddings and would make step 2 fail.
#    --max_length 512 and --prompt alpaca follow the original code/run.sh.
python 01_ds_score.py \
    --data_path ../data/train/v1_DS_27k.json \
    --model_name_or_path /path/to/Meta-Llama-3.1-8B-Instruct_pre \
    --save_path ../data/scores_all.pt \
    --max_length 512 \
    --prompt alpaca \
    --mod cherry
```

`mod=cherry` scores every sample with the **pre-experienced scorer** (the `_pre` model of the
original pipeline). For each sample it stores the answer-only loss (`token_loss[1]`) and the
instruction-conditioned loss (`token_loss[2]`). The DS score actually used downstream is
`mean(token_loss[2])`, i.e. the conditional loss alone — *not* the difference
`mean_2 - mean_1` of the original IFD definition.

### 5.2 Subset selection

```bash
# 2) Keep the N samples with the HIGHEST instruction-conditioned loss.
#    The original script sorts ascending and takes [-N:], so per source file the
#    hardest samples are kept (small files are kept in full).
python 02_select_subset.py \
    --pt_data_path ../data/scores_all.pt \
    --json_data_path ../data/train/v1_DS_27k.json \
    --json_save_path ../data/train/v1_DS_10k_repro.json \
    --sample_number 10000 \
    --max_length 512 \
    --prompt alpaca
```

> **Consistency check**: the ready-made `v1_DS_10k.json` / `v1_DS_20k.json` / `v1_DS_27k.json` are already
> included, so re-scoring is not required in normal use. To verify reproduction, compare
> `v1_DS_10k_repro.json` against `v1_DS_10k.json` item by item (they should overlap almost completely).

### 5.3 Training

```bash
bash 05_train.sh 10k        # DS-10K
bash 05_train.sh 20k        # DS-20K
bash 05_train.sh all        # DS-All

# Override the base model path via an environment variable
BASE_MODEL=/path/to/Meta-Llama-3.1-8B-Instruct bash 05_train.sh 10k
```

Fixed hyper-parameters (identical to the paper — do not change casually):

| Parameter                | Value                           |
| ------------------------ | ------------------------------- |
| LoRA r / alpha / dropout | 8 / 8 / 0.05                    |
| LoRA target modules      | q, k, v, o, gate, up, down_proj |
| epochs / lr              | 3 / 1e-4                        |
| batch / micro-batch      | 4 / 1                           |
| cutoff_len               | 2048                            |
| scheduler / warmup ratio | cosine / 0.1                    |

Output: `models/DS_10K/` (full merged weights).

### 5.4 Inference and evaluation

```bash
# 20 tasks (4,800 samples), 0-shot
bash 06_run_eval.sh model=../models/DS_10K test=test4800 shot=0

# SciFact 209 (short-answer task, cap generation at 128 tokens)
bash 06_run_eval.sh model=../models/DS_10K test=sci209 tag=DS_10K shot=0

# Batch: every model under models/
bash 06_run_eval.sh all
```

**Shot setting**: the main table reports methods 1–9 with **0-shot** and methods 10–12 with
**2-shot**. For 2-shot, pass `shot=2` (which enables `--use-history`).

**`max_tokens` matters a lot**:

- Long-output tasks (NER / RE / EE / COREF) need 1024.
- Short-answer tasks (SciFact / MedDialog / MedQA / PubMedQA) should be capped at 128; otherwise
  the model starts explaining itself and label-F1 collapses to token overlap.

### 5.5 Summarisation

```bash
python 07_summarize.py
```

Produces `results/table_319.md` and `results/table_209.md`. To obtain the Excel versions
(run from `scripts/`, needs `openpyxl`):

```bash
python md2xlsx.py ../results/table_209.md ../results/table_209.xlsx
python md2xlsx.py ../results/table_319.md ../results/table_319.xlsx
```

A qualitative discussion of the comparison is in `results/analysis.md`.

**The two tables compute Average differently**:

- `table_319`: Average is the plain 20-task macro average.
- `table_209`: SciFact is replaced by the 209-item result, and
  **Average = (19 tasks + SciFact209) / 20**.

### 5.6 Re-scoring typed (schema v2.0) predictions with the manuscript metric

The v2 experiments were scored in schema space by `eval_typed.py` (micro P/R/F1 per record type),
whereas Tables 5–6 use `eval_original.py` (BIO tag F1 / label macro-F1 / EM / bracketed-entity F1).
The two conventions differ by up to 15 points on individual tasks, so typed numbers must not be
mixed into the manuscript tables.

```bash
# 1) typed preds -> legacy strings (self-checks typed gold against the stored gold_legacy)
python convert_typed_to_legacy.py --input <typed_preds.json> --out <preds_legacy.json>

# 2) re-score with the manuscript metric and compare both conventions side by side
python compare_typed_vs_legacy.py \
  --run "exp6|<typed_preds.json>|<typed_metrics.json>" \
  --md ../../outputs/tables/typed_vs_legacy_metric.md
```

`convert_typed_to_legacy.py` reproduces the stored `gold_legacy` for **5,621 / 5,670 (99.1%)**
items; the residual is a property of the schema, not of the converter (see Known limitations).

---

## 6. Main results (`results/table_209.md`)

20-task macro average, with SciFact scored on the 209 evidence-bearing items:

| Method                                 | Setting | macro(209) |
| -------------------------------------- | ------- | ----------:|
| LLaMA3-MI (fine-tuned on 100K samples) | 0-shot  | **74.00**  |
| All (27,673)                           | 0-shot  | **73.13**  |
| DS-10K                                 | 0-shot  | **72.01**  |
| DS-20K                                 | 0-shot  | **69.17**  |
| Random-matched-10K                     | 0-shot  | **68.15**  |
| Random-10K                             | 0-shot  | **66.63**  |
| AL-Entropy-10K                         | 0-shot  | **62.17**  |
| Core-set-10K                           | 0-shot  | **50.00**  |
| LLaMA3                                 | 2-shot  | **42.62**  |
| BioMistral                             | 2-shot  | **26.98**  |
| MMEDL3-EnIns                           | 2-shot  | **16.31**  |

Per-task detail across all 20 rows is in `results/table_209.md`.

**Points worth keeping in mind when interpreting these numbers**:

1. **DS-10K reaches 98.4% of All** (72.01 / 73.13) while using only 1/2.77 of the data.
2. **At a matched 10K budget, DS is the strongest selector**: +5.4 over Random-10K, +9.8 over
   AL-Entropy, +22.0 over Core-set. Note, however, that the **+5.4 margin over random sampling is
   on the order of training noise** — retraining this pipeline with only 1.1% of samples changed
   leaves unrelated task scores fluctuating by up to ±6 points — so it should not be over-read.
   The margins over AL and Core-set are the robust ones.
3. **Core-set scores 50.00**, and the root cause is its lack of task-quota control: 8,762 of its
   10,000 samples (87.6%) are MedQA, while BC5CDR contributes 2 samples and MedDialog 6. This is
   a property of the method on a multi-task pool, not a training failure.
4. **The SciFact and MedDialog columns are affected by `max_tokens=1024`** (see §5.4). For the
   best possible values in these two columns, run them separately at 128 tokens and merge.

---

## 7. Reproduction checklist

Each step has a verifiable artefact:

| Step | Command                                                             | Expected output                                 |
| ---- | ------------------------------------------------------------------- | ----------------------------------------------- |
| 1    | `python 01_ds_score.py ...`                                         | `data/scores_all.pt` (27,673 scores)            |
| 2    | `python 02_select_subset.py ...`                                    | `data/train/v1_DS_10k_repro.json` (10,000 samples) |
| 3    | `bash 05_train.sh 10k`                                              | `models/DS_10K/config.json`                     |
| 4    | `bash 06_run_eval.sh model=../models/DS_10K test=test4800`          | `results/DS_10K/test4800/metrics.json`          |
| 5    | `bash 06_run_eval.sh model=../models/DS_10K test=sci209 tag=DS_10K` | `results/DS_10K/sci209/metrics.json`            |
| 6    | `python 07_summarize.py`                                            | `results/table_209.md`                          |

All scripts are **idempotent**: models that already have a `metrics.json` are skipped, so an
interrupted run can be resumed by re-issuing the same command.

---

## 8. Known limitations

1. **Two SciFact views (319 / 209)**: the 319-item view contains 110 items with empty evidence
   whose gold label is always `Neutral`, which creates a shortcut. The 209-item view is the clean
   one. The main table reports 209 and states that this column is not used to discriminate between
   methods (the spread among fine-tuned models is only about 3 points).

2. **`max_tokens` dominates short-answer tasks**: the same checkpoint on the same 5,670 items scores
   72.57 at `max_tokens=1024` and 67.55 at 512 — the whole 5-point gap comes from truncated JSON
   output (unclosed records: 421 → 595). Never compare runs produced with different caps.

3. **The typed schema is lossy for two corpora**: 17/87 MLEE-EE gold records are four-slot events
   (`[<type> <trigger> <theme1> <theme2>]`) while schema v2.0 stores a single `theme`, and 18/100
   BioRED records contain entity text with a literal `>` (e.g. `G-->A substitution at codon 1763`)
   that the bracketed format cannot express and that is therefore absent from the typed gold.
   Scores obtained on typed predictions are capped accordingly; report manuscript numbers with
   `eval_original.py`.
   
   
