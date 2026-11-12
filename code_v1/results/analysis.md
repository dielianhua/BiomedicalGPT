# Data selection for biomedical instruction tuning: analysis of the full benchmark comparison

## Scope

The comparison covers a single test suite rendered in a fixed instruction style and scored with the
paper metric, so every column is evaluated on identical items with identical decoding settings. The
configurations fall into four groups: instruction tuning on the complete in-house pool, difficulty-based
subsampling of that pool at different budgets, non-difficulty selection baselines (matched random
sampling, plain random sampling, entropy-based active learning, and core-set selection), and off-the-shelf
instruction-tuned models evaluated without further tuning. SciFact is scored on the evidence-bearing
subset only, because the remaining items admit a constant gold label.

## Principal observations

**Tuning on in-house data dominates.** Both full-pool configurations and the better difficulty-based
subsets sit clearly above the off-the-shelf instruction-tuned models. The gap is not uniform: the
general-purpose models remain competitive on natural-language judgement tasks such as dialogue
classification or claim verification, but degrade sharply on span-level annotation tasks, where their
outputs deviate from the required structured format. The weakest of them approaches the floor on several
extraction and coreference tasks, which indicates a formatting failure rather than a knowledge deficit.

**Difficulty-based selection is the strongest selection strategy.** Among the subsampling baselines, the
difficulty-based subset attains the highest average, followed by the size-matched random baseline and by
plain random sampling. Entropy-based active learning and core-set selection fall below both random
baselines. This ordering is consistent across the majority of tasks, and it is the opposite of what one
would expect if representativeness alone drove downstream quality: the subset that concentrates on samples
the model finds difficult transfers better than subsets chosen for diversity or uncertainty.

**The budget response is non-monotonic.** Increasing the difficulty-based budget does not improve the
average; the larger subset is worse than the smaller one and remains below full-pool tuning. Two effects
are entangled here. A larger subset covers more sources but also admits progressively easier samples,
diluting the signal that made the smaller subset effective. The observation argues against treating
subset size as a monotone proxy for quality, and for reporting the selection criterion and the per-source
composition together with the budget.

**Task heterogeneity dominates the aggregate picture.** Discriminative and question-answering tasks are
comparatively stable across configurations, whereas extraction tasks, relation extraction and event
extraction span the widest range. The largest swings appear in sources that contribute many near-duplicate
templates: a configuration can be close to the best on one annotation type and collapse on another. Two
failure modes recur among the weaker configurations: under-generation, where the model emits far fewer
spans than the reference, and format drift, where spans are produced but cannot be aligned to the gold
schema. Because the average weights tasks equally, a collapse in a single low-resource task moves the
aggregate as much as a broad but modest improvement elsewhere.

**No configuration dominates per task.** Dialogue classification, claim verification and event extraction
each have a different winner. This rank instability across tasks is the main reason to prefer paired,
per-task reporting over a single aggregate score when comparing selection strategies on a heterogeneous
biomedical benchmark.

## Interpretation

Taken together, the results suggest that the benefit of difficulty-based selection is conditional on
retaining coverage of every source. Selection operates by removing samples, and on high-volume sources it
removes precisely the routine cases that teach output conventions and label boundaries; what remains is
skewed towards atypical inputs. When the budget is small and the quota per source is preserved, the
trade-off is favourable; when it is relaxed, coverage loss outweighs the gain in difficulty. This reading
also explains why the diversity-oriented baselines underperform: they optimise spread in representation
space but do not protect the per-source coverage that the downstream metric rewards.

## Limitations

Each configuration was trained once, so differences of a few tenths of a point on individual tasks should
be read as indicative rather than established; only the ordering of groups is stable enough to interpret.
The instruction style is fixed by the test rendering, so the comparison isolates data effects and says
nothing about prompt sensitivity. Finally, the aggregate treats all tasks equally regardless of their
clinical importance or annotation reliability.

## Practical recommendation

Report difficulty-based selection against both a matched random baseline and full-pool tuning, and
report the per-source composition of every subset. Where a budget must be fixed in advance, prefer a
smaller subset with preserved per-source quotas over a larger subset selected globally, and validate the
choice on the extraction tasks, which are the first to show coverage loss.
