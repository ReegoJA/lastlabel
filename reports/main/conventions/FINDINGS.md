# Constant-agreement sensitivity

Replay all 8,640 main trajectories, assigning kappa 1 only to undefined noninitial comparisons on nonempty sets. In this binary implementation those comparisons have identical constant-class predictions. Keep the strict SP threshold, window, trained models, and PCF unchanged. This isolates one convention, not every small-text default.

The original convention is replayed and checked against archived label counts and trigger status before the alternative is evaluated. Of 25,920 SP outcomes, 905 select a different model and 790 change trigger status. These counts overlap. They are correlated outcomes rather than independent experiments.

In the illustrative linear-SVM, uncertainty, 15% symmetric-noise condition, all four text tasks and the balanced-synthetic task retain their original selections. The imbalanced easy set changes one selected model, producing mean changes of -4.67 labels [-14.00, 0.00] and -0.16 macro-F1 points [-0.47, 0.00]. Its remaining set changes one trigger status at the budget without changing the selected model. The headline balanced-task comparison is unchanged, but the convention matters elsewhere in the full matrix.

[paired.csv](paired.csv) reports alternative-minus-original differences within each task, query policy, learner/noise variant, noise rate, and stop set. Intervals resample matched seeds with 2,000 draws and are pointwise. [runs.csv](runs.csv) retains every seed-level difference. Original results are not overwritten and this analysis does not select a preferred convention by test performance.

Reproduce with `python -m stoplab.conventions --archive study-records.tar.gz --prefix results/phoenix-main --output reports/main/conventions`. The prefix is an archived directory identifier. See [result artifacts](../../../docs/RESULTS.md).
