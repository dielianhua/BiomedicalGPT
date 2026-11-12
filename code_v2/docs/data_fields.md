# Data fields in the released datasets

**Table 1. Data fields in the released `v1` and `v2` datasets.**

The last column identifies the release a field belongs to. Fields that share a name but differ in
meaning (`instruction`, `input`, `output`, `source_url`, and the difficulty score) are listed once per
release rather than merged, so that each description stays unambiguous.

| Field | Type | Description | Dataset |
|---|---|---|---|
| `instruction` | string | Natural-language task description (single fixed wording). | v1 |
| `input` | string | Task input (sentence, passage, dialogue, question, or structured prompt). | v1 |
| `output` | string | Reference output / target answer in the original annotation format of the source corpus. | v1 |
| `original_file` | string | Source file (e.g. `NCBI-disease_train.json`). | v1 |
| `task` | string | Task category (NER, QA, RE, TXTCLASS, TE, COREF, EE). | v1 |
| `split` | string | Always `"train"` for the released variants. | v1 |
| `mean_diff` | float | DS score = instruction-conditioned loss of the Meta-LLaMA-3.1-8B-Instruct model. Present in DS-selected variants only. | v1 |
| `source_url` | string | Accession URL of the source corpus, resolved from `data/SOURCES.md`. Present in the released training variants. | v1 |
| `instruction` | string | Natural-language task description, drawn from one of the instruction families used in the study. | v2 |
| `input` | string | Task input (sentence, passage, dialogue, question, or structured prompt). | v2 |
| `output` | string | Reference output as a canonical typed JSON object (serialised string, schema v2.0). | v2 |
| `output_legacy` | string | The same reference in the original annotation format of the source corpus, used for the legacy metric. | v2 |
| `source` | string | Source corpus (e.g. `NCBI-disease`). | v2 |
| `task` | string | Task category (NER, QA, RE, TXTCLASS, TE, COREF, EE). | v2 |
| `template_id` | string | Instruction family assigned to the record, written as `<source>#<family>`. | v2 |
| `source_url` | string | Accession URL of the source corpus, resolved from `data/SOURCES.md`. Present in the training variants only. | v2 |
| `label_split` | string | Phrasing-exposure label of the item; always `"seen"` in the released training variants. Present in the training variants only. | v2 |
| `in_test_split` | boolean | Whether the item also occurs in the test split. Present in the training variants only. | v2 |
| `ds_score` | float | DS score = instruction-conditioned loss (mean token loss of the answer under the full prompt) assigned by the seed-adapted Meta-LLaMA-3.1-8B-Instruct scorer. Present in the DS-selected variant only. | v2 |
| `from_v1` | boolean | Whether the item is one of the samples of the published `v1` DS-selected subset. Present in the DS-selected variant only. | v2 |
| `v1_original_file` | string | Source file of the matching `v1` record (e.g. `NCBI-disease_train.json`). Present in the DS-selected variant only. | v2 |
| `text_mode` | string | Whether the `v1` input text was matched verbatim or after removing the appended cited abstract. Present in the DS-selected variant only. | v2 |

## Structural differences between the two releases

The `v1` release keeps one answer representation (`output`) and one fixed instruction wording, with
`mean_diff` marking the difficulty-selected variants. The `v2` release replaces the single answer
string with a typed object (`output`) while retaining the original string in `output_legacy`, and adds
`template_id` to record which instruction family was used. Provenance is expressed differently:
`original_file` in `v1` versus `source` plus `source_url` in `v2`. The `v2` DS-selected variant
additionally carries link-back fields (`from_v1`, `v1_original_file`, `text_mode`) to the published
`v1` selection and its own difficulty score (`ds_score`).

## v2 field coverage by file

| Field | `v2_p3_27k.json`<br>`v2_plain_27k.json` | `v2_ds10k_v1match_10k.json` | `v2_test_mixed9_4800.json`<br>`v2_test_plain_4800.json` |
|---|:---:|:---:|:---:|
| `instruction`, `input`, `output`, `output_legacy` | ✓ | ✓ | ✓ |
| `source`, `task`, `template_id` | ✓ | ✓ | ✓ |
| `source_url`, `label_split`, `in_test_split` | ✓ | ✓ | — |
| `ds_score`, `from_v1`, `v1_original_file`, `text_mode` | — | ✓ | — |

The test files deliberately omit provenance and split metadata, so that the model cannot infer the
source corpus or its split from fields other than the task text. `data/test/v2_scifact209_idx.json` is
an auxiliary array of item positions, not a record file, and therefore has no field schema.

## Companion files

| file | purpose |
|---|---|
| `docs/data_fields.md` | this table (Markdown) |
| `docs/data_fields.xlsx` | the same table in spreadsheet form |
| `docs/dataset.md` | instruction families, prompt examples, distributions and conversion rules |
| `docs/pipeline.md` | methods text and the editable pipeline figure |
| `data/SOURCES.md` | source corpora, accession URLs, licences and references |
