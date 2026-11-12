# Instruction-style rewriting versus data subsampling: analysis of the three-model comparison

## Scope

Three models are compared on a single test suite in which every item is rendered with a randomly
assigned instruction phrasing drawn from a fixed set of families, so that the models must cope with
wording variation rather than with a single template. Two of them are trained on the complete pool and
differ only in how many phrasings appear during training; the third is trained on a substantially smaller
subsample whose samples are taken from the previously published selection and whose templates are rewritten
to the current schema. All three are evaluated on identical items with identical decoding settings and the
paper metric, and SciFact is scored on its evidence-bearing subset.

## Principal observations

**Full-data training sets the upper bound.** Both full-pool models lead the subsample model on the
aggregate score. The margin is small, however: the subsample uses a small fraction of the pool and still
falls within a couple of points of the full-data models, which is the empirical basis for the
data-efficiency claim.

**Phrasing diversity costs almost nothing.** The model trained on a mixture of instruction families is
marginally behind the single-style model on the aggregate, and the per-task picture is split roughly
evenly between wins and losses. Because the mixture model was exposed to several renderings of the same
underlying task while the single-style model was not, the near-parity indicates that increasing phrasing
diversity is essentially free in accuracy terms, and it removes the need to know the test-time phrasing
in advance. The residual difference is of the same order as run-to-run variation on the smaller tasks.

**The subsample deficit is localised, not diffuse.** The aggregate gap is produced almost entirely by two
high-volume named-entity sources. In the subsample these sources retain only a small quota, whereas the
full pool exposes the models to many times more annotations; the resulting error is dominated by recall,
i.e. the model emits markedly fewer spans than the reference rather than mislabelling them. Every other
task, including relation extraction, claim verification, dialogue classification and the remaining
annotation tasks, is either at parity or slightly better for the subsample model.

**Small tasks fluctuate more than the aggregate suggests.** The tasks in which the subsample model loses
ground are low-resource ones whose test portions are small, and whose training portions are identical
across the two configurations. Drops of that magnitude therefore reflect optimisation variance rather than
the effect of the subsample, and they should not be over-interpreted.

**Subsampling is comparatively favourable for structured prediction over short spans.** Relation
extraction, event argument extraction and claim verification are at least as good with the smaller
training set, which is consistent with the idea that once output conventions are learned, additional
volume of routine examples adds little. The named-entity sources behave in the opposite way, because
their label space is large and long-tailed and benefits from broad exposure.

## Interpretation

The comparison separates two factors that are usually confounded: the amount of data and the wording of
the instructions. Holding the test rendering fixed, a subsample that preserves the per-source composition
of the original selection retains nearly all of the full-data performance, while a mixture of instruction
phrasings introduces no measurable penalty. The failure mode to avoid is therefore not the smaller budget
itself but the loss of coverage within high-volume sources, which manifests first and most visibly on
named-entity recognition.

## Limitations

Each model was trained once and evaluated with greedy decoding on a single rendering of the test suite, so
task-level differences of a few tenths of a point are indicative rather than established. The subsample
is inherited from an existing selection and its provenance is documented in the package rather than
re-derived here, so the analysis speaks to the effect of subsampling at that composition, not to the
optimality of the selection rule. The aggregate score weights every task equally, irrespective of the size
of its test portion or its clinical relevance.

## Practical recommendation

When a training budget must be reduced, preserve per-source quotas and verify the effect on the
high-volume named-entity sources first, since they are the earliest and most reliable indicator of coverage
loss. Report both aggregate and per-task results, and state the SciFact scoring view explicitly, because
its two views differ systematically and the difference propagates into the aggregate.
