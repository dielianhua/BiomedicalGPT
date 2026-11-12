# Dataset construction for the mixed9 experiments

This document describes the two training sets and the single test set that the published table uses,
the instruction templates they are built from, and how the legacy annotations were converted to the
typed schema. Every count below is computed directly from the shipped files in `data/`; nothing is
estimated. `data/train/v2_plain_27k.json` is shipped for completeness but is outside the scope of this
document, which covers only `p3` and `DS-10K (v1match)` as training sets and `mixed9` as the test set.

| role | file | items |
|---|---|---:|
| training, multi-style | `data/train/v2_p3_27k.json` | 27,673 |
| training, subsample | `data/train/v2_ds10k_v1match_10k.json` | 10,000 |
| test | `data/test/v2_test_mixed9_4800.json` | 4,800 |

---

## 1. Record schema

Every record carries the original annotation string and its typed counterpart, so no information is lost
when the answer format changes. A paper-ready combined field table for both releases is provided in
`docs/data_fields.md` (also as `docs/data_fields.xlsx`), with a `Dataset` column distinguishing `v1` from `v2`.

| field | meaning |
|---|---|
| `instruction` | the task instruction, one of nine phrasings (see §2) |
| `input` | the passage / claim / question, identical across phrasings |
| `output` | the answer as a canonical JSON object (schema v2.0) |
| `output_legacy` | the answer in the original dataset string format, kept for the paper metric |
| `source`, `task` | corpus name and task type (`NER`, `RE`, `EE`, `COREF`, `TE`, `QA`, `TXTCLASS`) |
| `template_id` | `<source>#<family>`, identifies which phrasing was used |
| `in_test_split` | whether the item also occurs in the test split of its source |
| `source_url` | accession URL of the source corpus, resolved from `data/SOURCES.md` |

---

## 2. The nine instruction families

Each family is a programmatic rewrite of the same task specification: the format description, the label
set and the output contract are held constant, and only the surrounding wording, ordering and register
change. Generation is deterministic and uses no language model, so re-running it reproduces the same
strings byte for byte.

| # | family | design probe | structural signature |
|---:|---|---|---|
| 1 | `plain` | seen | one-paragraph prose: "given X, do Y, return JSON" |
| 2 | `format_first` | seen | three-part block: `Output format` / `Input` / `Task`, contract stated first |
| 3 | `persona` | seen | role assignment + numbered requirements + "JSON only" |
| 4 | `order_emphasis` | seen | imperative first, explicit prohibition of explanation |
| 5 | `unseen_narrative` | **unseen** | second-person narrative, no lists, wholesale rewording |
| 6 | `paraphrase_frame` | in-style | new opening frame ("Below is …"), same action wording |
| 7 | `paraphrase_action` | in-style | same frame, different verb (assign → choose) |
| 8 | `terse` | out-of-style | compressed to the bare minimum, no politeness or explanation |
| 9 | `checklist` | out-of-style | numbered procedure |

Which families a training set contains:

| training set | families used |
|---|---|
| `p3_27k` | `plain`, `format_first`, `persona` (one family assigned per item; the data are **not** triplicated) |
| `ds10k_v1match_10k` | the same three, assigned per item |
| `mixed9` (test) | all nine, rotated per item |

Instruction length varies widely by family and by task, because long templates must enumerate the full
entity or relation inventory of the task:

| family | min chars | median | max |
|---|---:|---:|---:|
| `plain` | 115 | 193 | 4,257 |
| `format_first` | 142 | 220 | 4,284 |
| `persona` | 370 | 445 | 4,509 |
| `order_emphasis` | 155 | 277 | 4,341 |
| `unseen_narrative` | 260 | 349 | 4,413 |
| `paraphrase_frame` | 118 | 196 | 4,260 |
| `paraphrase_action` | 117 | 178 | 4,242 |
| `terse` | 72 | 118 | 2,150 |
| `checklist` | 119 | 165 | 2,197 |

---

## 3. Prompt examples

### 3.1 All nine phrasings of one task (MedDialog, sentence-level speaker classification)

```text
[plain]
Given a passage, assign exactly one label from: doctor, patient. Return a JSON object
{"label":<exactly one of: doctor, patient>}.

[format_first]
Output format — Return a JSON object {"label":<exactly one of: doctor, patient>}.

Input — a passage.

Task — Assign exactly one label from: doctor, patient.

[persona]
You are a clinical text annotator preparing training data for a biomedical language model.

The input is a passage. Read it in full before answering.

Requirements:
1. Assign exactly one label from: doctor, patient.
2. Return a JSON object {"label":<exactly one of: doctor, patient>}.
3. Return only the JSON object — no explanation, no markdown code fence, no extra text.

[order_emphasis]
Assign exactly one label from: doctor, patient. Do not add any explanation, justification or extra
text. Return a JSON object {"label":<exactly one of: doctor, patient>}.

[unseen_narrative]
The text below is a passage drawn from the biomedical literature. Read it carefully, then choose
exactly one label out of: doctor, patient. Give the answer as a single JSON object shaped like
{"label":<exactly one of: doctor, patient>}, with no other text before or after it.

[paraphrase_frame]
Below is a passage. Assign exactly one label from: doctor, patient. Return a JSON object
{"label":<exactly one of: doctor, patient>}.

[paraphrase_action]
Given a passage, choose exactly one label out of: doctor, patient. Return a JSON object
{"label":<exactly one of: doctor, patient>}.

[terse]
assign exactly one label from: doctor, patient. JSON only: {"label":...}.

[checklist]
Follow these steps.
1. Read the passage.
2. assign exactly one label from: doctor, patient.
3. JSON only: {"label":...}.
```

### 3.2 The same two probes on annotation tasks

```text
[NCBI-disease / plain]
Given a passage, identify every entity mention in the text and give its exact surface form, spelling
it exactly as it appears. Return a JSON object
{"entities":[{"text":<span>,"label":null},...]}. Every entity mention must appear exactly once,
in order of appearance.

[MedQA / plain]
Given a passage, answer the question and output only the answer. Return a JSON object
{"answer":<the answer only>}.
```

The `persona` variant of an annotation task runs to roughly four thousand characters because its
numbered requirements list every entity type the task defines; that is what drives the maximum in §2.

---

## 4. Training set `v2_p3_27k.json` (27,673 items)

Family assignment is per item, so each source is split roughly evenly across the three families:

| family | items |
|---|---:|
| `plain` | 9,188 |
| `format_first` | 9,160 |
| `persona` | 9,325 |

Per source:

| source | plain | format_first | persona | total |
|---|---:|---:|---:|---:|
| MedQA | 3,376 | 3,356 | 3,446 | 10,178 |
| NCBI-disease | 1,801 | 1,783 | 1,848 | 5,432 |
| BC5CDR | 1,556 | 1,501 | 1,503 | 4,560 |
| MedDialog | 309 | 354 | 318 | 981 |
| SciFact | 278 | 276 | 314 | 868 |
| BioNLP-2011-GE | 267 | 302 | 287 | 856 |
| BioNLP-2009 | 246 | 259 | 251 | 756 |
| BioNLP-2011-REL | 265 | 255 | 236 | 756 |
| BioInfer-RE | 206 | 223 | 213 | 642 |
| BC5CDR-RE | 172 | 161 | 167 | 500 |
| PubMedQA-labeled | 151 | 145 | 154 | 450 |
| BioRED | 125 | 128 | 147 | 400 |
| BioNLP-2013-CG | 108 | 100 | 92 | 300 |
| MLEE-COREF | 66 | 57 | 75 | 198 |
| BioNLP-2013-GE | 69 | 54 | 71 | 194 |
| AnEM | 50 | 58 | 56 | 164 |
| BioNLP-2011-ID | 58 | 40 | 53 | 151 |
| BioNLP-2013-GRO | 37 | 54 | 59 | 150 |
| MLEE-EE | 46 | 49 | 32 | 127 |
| AnEM-COREF | 2 | 5 | 3 | 10 |
| **total** | **9,188** | **9,160** | **9,325** | **27,673** |

The pool is strongly long-tailed: the three largest sources account for 72.9% of the items, while
seventeen sources contribute fewer than one thousand each.

---

## 5. Training set `v2_ds10k_v1match_10k.json` (10,000 items)

Items are those of the previously published DS-10K selection, re-rendered with the current templates.
No re-scoring is involved: the selection was fixed, and only the instruction wording and the answer
format changed.

| field value | items | meaning |
|---|---:|---|
| `from_v1 = true` | 10,000 | every item originates from the published selection |
| `text_mode = v1_exact` | 9,696 | matched to the v2 pool by exact `(input, answer)` |
| `text_mode = v2_no_cited_abstract` | 304 | SciFact items whose `Evidence:` field is empty; the published file appends a cited abstract there, the v2 pool does not |

Family distribution: `persona` 3,359 · `format_first` 3,343 · `plain` 3,298.

Retention per source (selected / pool):

| source | selected | pool | share |
|---|---:|---:|---:|
| MedQA | 1,497 | 10,178 | 14.7% |
| NCBI-disease | 500 | 5,432 | 9.2% |
| BC5CDR | 500 | 4,560 | 11.0% |
| MedDialog | 981 | 981 | 100% |
| SciFact | 868 | 868 | 100% |
| BioNLP-2011-GE | 856 | 856 | 100% |
| BioNLP-2009 | 756 | 756 | 100% |
| BioNLP-2011-REL | 756 | 756 | 100% |
| BioInfer-RE | 642 | 642 | 100% |
| BC5CDR-RE | 500 | 500 | 100% |
| PubMedQA-labeled | 450 | 450 | 100% |
| BioRED | 400 | 400 | 100% |
| BioNLP-2013-CG | 300 | 300 | 100% |
| MLEE-COREF | 198 | 198 | 100% |
| BioNLP-2013-GE | 194 | 194 | 100% |
| AnEM | 164 | 164 | 100% |
| BioNLP-2011-ID | 151 | 151 | 100% |
| BioNLP-2013-GRO | 150 | 150 | 100% |
| MLEE-EE | 127 | 127 | 100% |
| AnEM-COREF | 10 | 10 | 100% |

Only the three high-volume sources are subsampled; every other source is carried over in full. This is
the structural reason why the subsample loses accuracy almost exclusively on the two large
named-entity sources: they keep a fraction of their annotations, while everything else keeps all of its.

---

## 6. Test set `v2_test_mixed9_4800.json` (4,800 items)

All nine families are rotated over the items, so each family appears 525–544 times and every task
contains every family:

| family | items |
|---|---:|
| `plain` | 544 |
| `format_first` | 539 |
| `persona` | 537 |
| `order_emphasis` | 537 |
| `unseen_narrative` | 534 |
| `paraphrase_frame` | 529 |
| `paraphrase_action` | 528 |
| `terse` | 527 |
| `checklist` | 525 |

Per task:

| task | plain | format_first | persona | order_emphasis | unseen_narrative | paraphrase_frame | paraphrase_action | terse | checklist | total |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| MedQA | 142 | 142 | 142 | 142 | 141 | 141 | 141 | 141 | 141 | 1,273 |
| PubMedQA-labeled | 56 | 56 | 56 | 56 | 56 | 55 | 55 | 55 | 55 | 500 |
| BC5CDR-RE | 56 | 56 | 56 | 56 | 56 | 55 | 55 | 55 | 55 | 500 |
| SciFact | 36 | 36 | 36 | 36 | 35 | 35 | 35 | 35 | 35 | 319 |
| BioNLP-2009 | 29 | 29 | 29 | 29 | 29 | 29 | 29 | 29 | 28 | 260 |
| BioNLP-2011-REL | 29 | 29 | 29 | 29 | 29 | 29 | 29 | 29 | 28 | 260 |
| BioNLP-2013-GE | 29 | 29 | 29 | 29 | 28 | 28 | 28 | 28 | 28 | 256 |
| BioNLP-2013-CG | 23 | 23 | 22 | 22 | 22 | 22 | 22 | 22 | 22 | 200 |
| BioInfer-RE | 16 | 16 | 16 | 16 | 16 | 16 | 16 | 15 | 15 | 142 |
| AnEM | 16 | 16 | 15 | 15 | 15 | 15 | 15 | 15 | 15 | 137 |
| MedDialog | 14 | 14 | 14 | 14 | 14 | 13 | 13 | 13 | 13 | 122 |
| BioNLP-2011-ID | 13 | 13 | 13 | 13 | 13 | 13 | 13 | 13 | 13 | 117 |
| MLEE-COREF | 13 | 13 | 13 | 13 | 13 | 12 | 12 | 12 | 12 | 113 |
| NCBI-disease | 12 | 11 | 11 | 11 | 11 | 11 | 11 | 11 | 11 | 100 |
| BC5CDR | 12 | 11 | 11 | 11 | 11 | 11 | 11 | 11 | 11 | 100 |
| BioNLP-2011-GE | 12 | 11 | 11 | 11 | 11 | 11 | 11 | 11 | 11 | 100 |
| BioNLP-2013-GRO | 12 | 11 | 11 | 11 | 11 | 11 | 11 | 11 | 11 | 100 |
| BioRED | 12 | 11 | 11 | 11 | 11 | 11 | 11 | 11 | 11 | 100 |
| MLEE-EE | 10 | 10 | 10 | 10 | 10 | 10 | 9 | 9 | 9 | 87 |
| AnEM-COREF | 2 | 2 | 2 | 2 | 2 | 1 | 1 | 1 | 1 | 14 |
| **total** | **544** | **539** | **537** | **537** | **534** | **529** | **528** | **527** | **525** | **4,800** |

Three properties worth stating in a paper caption:

1. **The items are constant across phrasings.** `v2_test_plain_4800.json` and `v2_test_mixed9_4800.json`
   contain the same items in the same order — the fingerprint of
   `sorted(source, input, output_legacy)` is `52b48363a164` for both, and only `instruction` differs.
   Any gap between conditions is therefore attributable to the phrasing alone.
2. **Mixing is per item**, not per file, and it is balanced both globally and inside each task.
3. **SciFact has two scoring views.** Of the 319 items, 110 have an empty `Evidence:` field and a gold
   label that is constant (`Neutral`), so the label is determined by the input alone. Those items are
   excluded from the reported metric, which leaves 209; `data/test/v2_scifact209_idx.json` stores the
   positions of the 209 retained items inside the 4,800-item file.

---

## 7. Conversion from the legacy annotation format

The conversion is rule-based and deterministic, and it never discards a record: the original string is
kept in `output_legacy` and the parse status is recorded, so a downstream metric can fall back to the
legacy form. Parse failures on the shipped data: none.

| legacy format | example | rule | typed field | sources |
|---|---|---|---|---|
| `bio` | `Selegiline [B] - [O] induced [O] …` | merge `B`/`I` runs back into entity strings; no entity type | `entities[{text,label:null}]` | NCBI-disease, BC5CDR |
| `span` | `[urinary <Organism_substance>]` | `[text <label>]` | `entities[{text,label}]` | AnEM, BioNLP-\\*, BioRED |
| `rel` | `[<alpha-methyldopa> <CID> <hypotensive>]` | `[<head> <relation> <tail>]`, relation checked against a whitelist | `relations[{head,relation,tail}]` | BC5CDR-RE, BioInfer-RE |
| `event` | `[<Regulation> <regulation> <TGF-beta>]` | same triple, **renamed by semantics** | `events[{type,trigger,theme}]` | MLEE-EE |
| `mention` | `[ER]` | `[text]` | `mentions[str]` | AnEM-COREF, MLEE-COREF |
| `label` | `patient` | strip whitespace | `label` | MedDialog, SciFact, PubMedQA |
| `text` | `Nitrofurantoin` | verbatim | `answer` | MedQA |

`event` is a separate branch rather than a special case of `rel`: in MLEE the triple means
`<event type> <trigger> <theme>`, whereas in RE it means `<head> <relation> <tail>`. Sharing one field
order made the model learn the roles reversed and drove the score to zero — the only structural bug
encountered during conversion.

Real before/after examples taken from the shipped test file:

```text
[bio] NCBI-disease
  legacy : VHL [O] - [O] negative [O] 786 [O] - [O] 0 [O] RCC [B] cells [O] are [O] tumorigenic [O] …
  typed  : {"entities":[{"label":null,"text":"RCC"},{"label":null,"text":"VHL"}],
            "format":"bio","task":"NER","v":"2.0"}

[rel] BC5CDR-RE
  legacy : [<Famotidine> <CID> <delirium>] [<Famotidine> <CID> <delirium>] …
  typed  : {"format":"rel","relations":[{"head":"Famotidine","relation":"CID","tail":"delirium"}, …],
            "task":"RE","v":"2.0"}

[event] MLEE-EE
  legacy : [<Development> <formation> <bone>] [<Regulation> <effects> <bone>] …
  typed  : {"events":[{"theme":"bone","trigger":"formation","type":"Development"},
                      {"theme":"bone","trigger":"effects","type":"Regulation"}],
            "task":"EE","v":"2.0"}
```

JSON is emitted with sorted keys and no extra whitespace, so the training target string is stable.

Known representational losses, both inherent to the legacy format rather than parsing errors:

| source | loss | items |
|---|---|---:|
| MLEE-EE | four-slot events `[<type> <trigger> <theme1> <theme2>]` can only store one theme | 17 / 87 |
| BioRED | entity text containing a literal `>` (e.g. `G-->A substitution at codon 1763`) cannot be expressed inside the bracket notation | 18 / 100 |

Both affect the typed metric slightly and leave the legacy metric unaffected.

---

## 8. Reproducing the files

```bash
# rebuild the DS-10K subsample from the published selection (needs the source pool)
python scripts/build_ds10k_v1match.py

# re-score and rebuild the table from the shipped predictions (no GPU)
python scripts/04_make_table.py

# Markdown table -> Excel
python scripts/md2xlsx.py tables/3models_mixed9_20tasks_final.md \
                          tables/3models_mixed9_20tasks_final.xlsx
```

The training and test files themselves are shipped as-is; their md5 sums and record counts are listed in
`manifest.json`.
