# Data construction: methods text and figure

Paper-ready English description of how the training and evaluation data of this package were produced,
with the editable figure (`pipeline.drawio`) and its vector preview (`pipeline.svg`). No counts appear
in the text or the figure; quantities are reported in `dataset.md` and `manifest.json`.

---

## Methods text (single paragraph, draft)

**Data construction.** We assembled the corpus from public biomedical corpora covering named entity
recognition, relation and event extraction, coreference, textual entailment, question answering and
dialogue-act classification. Because their annotation conventions differ — inline token-tag sequences,
bracketed entity lists, head–relation–tail triples, and plain labels or short free-text answers — every
record was rewritten by a deterministic, format-aware parser into a canonical structured answer, while
the original annotation string was retained alongside it so that a model can be scored in both
representations. Training instructions were deliberately not fixed to a single phrasing: a bank of
instruction families was generated programmatically from each task specification — its input
description, label inventory and output contract — and the training pool assigns every item one of
three families, namely a plain prose instruction, a format-first block that states the output contract
before the task, and a persona-style instruction with numbered requirements. No record is duplicated,
so inputs and answers stay untouched while the model still meets several renderings of each task. A
smaller training set was drawn from the same pool by ranking items within each source with a difficulty
score, derived from the conditional loss of a model previously trained on a small seed subset, and
retaining a per-source quota; this preserves the source composition while discarding the routine
majority of the high-volume corpora. Evaluation used one fixed item set, rendered once per family and once
in a mixed condition in which the families are rotated across items and balanced within every task, so
that differences between conditions are attributable to the phrasing alone. Items whose evidence field
is empty were removed from the claim-verification subset, because their reference label follows from
the input rather than from reasoning over evidence. Predictions were scored both against the canonical
structured answer, which tests compliance with the output contract, and after conversion back to the
source annotation convention, which yields the metric comparable with prior work; task-level scores were
aggregated with equal weight.

*Package mapping*: the training pool described above is `data/train/v2_p3_27k.json` (plain, format-first
and persona families); the difficulty-ranked subsample is `data/train/v2_ds10k_v1match_10k.json` (same
families); the evaluation set is `data/test/v2_test_mixed9_4800.json`.

---

## Figure caption

*Construction of the training and evaluation data. Public biomedical corpora are harmonised into a
canonical structured annotation while the original annotation strings are retained. A programmatically
generated bank of instruction families supplies several renderings of each task; the training branch
assigns one family per item and applies a difficulty-ranked, quota-preserving subsample, whereas the
evaluation branch keeps the item set fixed and rotates the families across it after removing items whose
label is determined by an empty evidence field. Models are scored against both the structured answer and
the original annotation format.*

---

## Figure files

| file | purpose |
|---|---|
| `pipeline.drawio` | editable source, open with draw.io / diagrams.net or the VS Code draw.io extension |
| `pipeline.svg` | vector preview, suitable for inclusion in a manuscript |

Conventions used in the figure: rectangles denote data or artefacts, light-filled rectangles denote
processing steps, bold labels mark the artefacts that enter training or reporting, solid arrows follow
the primary data flow, and dashed arrows carry artefact reuse rather than the main flow.
