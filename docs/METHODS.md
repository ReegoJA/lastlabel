# Methods and interpretation

This implementation builds on Dr. Michael Bloodgood's stopping research and Reego John-Annaselvan's undergraduate work with him. SP is credited to Bloodgood and Vijay-Shanker, its theoretical analysis to Bloodgood and Grothendieck, PCF to Altschuler and Bloodgood, and the stop-set comparison to Kurlandski and Bloodgood. See [REFERENCES.md](REFERENCES.md) for the papers and [STUDY.md](STUDY.md) for the new experimental choices.

## Experimental unit

A trajectory is a dataset, seed, acquisition policy, noise rate, and named
variant. Each trajectory is trained all the way to a fixed annotation budget.
Every stopping rule observes the same fitted-model sequence. Its first trigger
selects an earlier point on that sequence, continuing the sequence is an
evaluation mechanism, not a claim that stopping actually saved computation
during the benchmark.

Seeds control separate random streams for initialization, annotation noise,
random querying, and random stop-set selection. The first labeled sample is
random, not selected using clean class labels. If observed labels contain only
one class, further random examples are queried and counted until both classes
appear or the budget is exhausted. Imbalanced data can therefore start above
the nominal initial sample size.

## Criteria

For two consecutive models evaluated on identical example indices, let `a`
count both-positive predictions, `d` both-negative predictions, and `b,c`
disagreements. Let observed agreement be `Po`, and let `Pe` be the agreement
expected from the two predicted class marginals.

**SP:** `kappa = (Po - Pe) / (1 - Pe)`. Stop when the mean of the last `window`
consecutive-pair kappas strictly exceeds the threshold. Default: three pairs,
threshold 0.99. A three-pair window requires four fitted models. If `Pe=1`,
kappa is undefined and the window cannot trigger, constant predictions are
not automatically treated as evidence of successful learning.

**PCF:** estimated positive-class F change is
`1 - 2a / (2a + b + c) = (b + c) / (2a + b + c)`.
Every estimate in the last `window` pairs must be strictly below epsilon.
Default: three pairs, epsilon 0.01. This is not SP's mean-window condition.
If the denominator is zero, the estimate is undefined and the rule abstains.
The estimate rests on assumptions about errors on disagreement examples,
it is not a guaranteed bound on held-out F1 under arbitrary label noise.

**Confidence heuristic:** mean maximum class probability exceeds a declared
threshold for a mean window. This is an explicit heuristic baseline, not an
implementation of published Declining Confidence or Non-increasing Confidence.
For SVM, probabilities use libsvm's internal training-only calibration, while
predictions and acquisition use the decision margin. Calibration quality can
be poor at small budgets or under noise. A probability is not ground truth.

**Fixed budget:** use the last model. A criterion that never fires also uses
the last model, with `stopped=false`. This is right censoring at the budget,
it does not mean the rule would never stop with more annotations.

## Stop sets

| Design | Definition | What it tests |
|---|---|---|
| Fixed | Random sample of the complete initial pool | Representative reference |
| Remaining | Current unqueried pool after acquisition | Endogenous sampling bias |
| Easy | Highest absolute margins from the first model, fixed thereafter | Deliberately biased stability probe |

The fixed and easy sets may include queried examples and retain them when
queried. This matches the original fixed-stop-set SP protocol rather than
silently imposing an excluded holdout. The remaining-set comparison evaluates
both consecutive models on the **same current remaining indices**, never on
different example populations. Empty sets cannot trigger. The easy-set stress
condition is an extension in this implementation, not attributed to the papers.

## Learners, features, and noise

Both learners use fixed `C=1`: liblinear logistic regression and linear-kernel
SVC. No hyperparameter is selected with test labels. Uncertainty acquisition
queries smallest absolute decision margins, ties break by original pool index.
Random acquisition samples without replacement. Convergence warnings cause
the trajectory to fail rather than silently treating an unconverged fit as data.

Synthetic tasks use 30 features (15 informative, 5 redundant), 2,400 examples,
and a stratified 70/30 split. Scaling fits only the training pool. Changing
the seed generates a new synthetic problem as well as a new acquisition
sequence, synthetic-seed intervals include both sources of variation.

Text tasks use the original 20 Newsgroups train/test split, 20,000 maximum
TF-IDF features, word unigrams/bigrams, `min_df=2`, `max_df=.95`, and sublinear
term frequency. Actual class-1 names and feature counts are recorded per run.
Text seeds retain the same documents and change acquisition/noise randomness.

Annotation corruption is fixed per pool example for a trajectory. A queried
example always returns the same corrupted annotation. Symmetric noise flips
either class at the configured rate. Positive-only and negative-only modes
apply that probability only within the named **clean** class. These modes have
different overall corruption rates, compare both nominal and realized rates.
The simulator may access clean pool labels only to construct the oracle.
Acquisition and stopping accept predictions, scores, and indices, never labels.

Test features receive predictions during fitting iterations, test labels are
read only after all querying and stopping decisions. All saved test metrics
are retrospective. A regression test inverts test labels and requires identical
query histories and stopping decisions.

## Outcomes and uncertainty

Macro F1 is the primary robustness metric, positive F1 separately aligns with
PCF's binary positive-class quantity. AUROC is also retained. Label savings
is `1 - selected labels / final budget`. Premature stopping is selected macro
F1 more than 0.01 below the **best observed point on that finite trajectory**.
Excess labeling is labels beyond the first point within that tolerance of the
peak, clipped at zero. This hindsight reference is not a globally optimal
budget or a deployable oracle. A final-budget model can be below an earlier
peak, particularly under noisy annotation.

Intervals use 2,000 percentile bootstrap samples of independent seeds, not
correlated model iterations. Stop-set and variant effects are paired within
seed before resampling. Different rules and replay settings remain correlated,
10,368 replay decisions are not 10,368 independent experiments. Three-seed
pilot intervals are descriptive. The suite performs no automatic significance
tests, ranking, multiple-comparison claims, or test-set threshold selection.

## Deliberate limits

This is a binary-classification methodology extension, not an exact reproduction
of a paper's original datasets, SVM configuration, budgets, or published tables.
Noise is simulated, it does not model every human annotation failure. Remaining
and fixed stop sets differ in both selection and size, the explicit stop-size
variants help investigate size but do not completely isolate every interaction.
The easy-set experiment intentionally combines selection and model dependence.
The bundled study is one-factor-at-a-time, not a complete factorial interaction
study. No clinical, production, or universal performance claim follows from it.

## Small-text engine

Since version 0.3.0, every new trajectory uses small-text 1.4.1's `PoolBasedActiveLearner` and `SklearnClassifierFactory`. There is no alternate engine. This reconnects the implementation to the library used in Reego John-Annaselvan's research with Dr. Michael Bloodgood. The historical library version and experiment settings from that work are unknown.

The dataset given to small-text contains features and unlabeled sentinels, never the oracle's full label vector. Only initial and queried labels are supplied through `initialize_data` and `update`. Models are rebuilt each round. Evaluation labels remain outside the learner.

A custom `QueryStrategy` preserves the study's decision-margin sampling, deterministic index tie-breaking, and independent random stream. This avoids substituting probability-based uncertainty or global random state during migration. Both linear learners are tested against direct scikit-learn training on dense and sparse inputs.

LastLabel retains its scalar stopping-rule evaluator so shrinking stop sets compare both models on the same current indices and saved traces remain replayable. Tests cross-check fixed-set SP and PCF against small-text's `KappaAverage` and `DeltaFScore`. The following differences are intentional:

- SP uses strict `>` in LastLabel. Small-text uses `>=`, so exact threshold equality differs.
- LastLabel treats constant-class agreement as undefined kappa and does not stop on it. Small-text returns kappa 1 for identical predictions.
- All-negative PCF comparisons are undefined. LastLabel records `None`, whereas small-text produces NaN. Neither supplies a stop in this case.
- PCF arithmetic can differ at floating-point boundaries. LastLabel keeps the stored scalar definition used by its pilot and replay.

Small-text's fixed-length prediction interface is not used directly for shrinking stop sets. Doing so would either reject changing lengths or compare different examples. These adapters and conventions are part of LastLabel, not claimed as small-text defaults.

The pinned 1.4.1 release is a reproducibility choice, not a claim about the version used at TCNJ. It includes the stopping-criterion corrections documented in 1.3.3. Version 2 development interfaces are outside this study. The original pilot remains a legacy result and is not relabeled as a small-text run.

## Event-level diagnostics

The diagnostic analysis separates early triggers, triggers exactly at the budget, and fallback without a trigger. The fixed-budget baseline is recorded separately. The existing `premature` outcome is a retrospective gap flag that can be true even for a final-budget model. Interpret it alongside event status, not as a count of actual early stops. Conditional gap rates are undefined when no corresponding events occur. See the [failure analysis](../reports/main/diagnostics/FINDINGS.md).
