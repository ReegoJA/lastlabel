# Threshold and window sensitivity

The paired replay analysis covers 1,728 setting-level comparisons across six tasks, two acquisition policies, clean and 15% symmetric annotation noise, three stop sets, and the SP and PCF threshold/window grids. Each comparison uses 30 matched seeds with the linear SVM learner. These 51,840 replay decisions reuse 720 training trajectories and are not independent experiments.

Each setting is compared with the same method and stop set at its default threshold (SP .99 or PCF .01) and window three. Pointwise 95% percentile bootstrap intervals resample paired seed-level differences. Positive-class F1, all windows, both query policies, and both noise rates are retained in [threshold-pairs.csv](threshold-pairs.csv).

## Illustrative threshold contrasts

The table holds the window at three and uses fixed stop sets, uncertainty acquisition, and 15% symmetric noise. It compares SP .97 with .99 and PCF .02 with .01. These descriptive contrasts were chosen after inspecting the sweep to illustrate threshold sensitivity, not to identify an optimal setting. Negative label differences indicate annotation savings. F1 differences are percentage points.

| Task | Method | Labels, difference [95% interval] | Macro F1, points [95% interval] |
| --- | --- | ---: | ---: |
| baseball-vs-hockey | PCF | -3.33 [-7.33, -0.67] | 0.07 [-0.05, 0.24] |
| baseball-vs-hockey | SP | -4.00 [-8.67, -0.67] | 0.05 [-0.05, 0.19] |
| graphics-vs-windows | PCF | -2.67 [-7.33, 0.00] | -0.03 [-0.09, 0.00] |
| graphics-vs-windows | SP | -2.00 [-5.33, 0.00] | -0.06 [-0.15, 0.00] |
| politics-vs-religion | PCF | -16.00 [-25.33, -8.00] | -0.45 [-0.79, -0.16] |
| politics-vs-religion | SP | -26.00 [-37.33, -16.00] | -0.31 [-0.72, 0.08] |
| space-vs-medicine | PCF | -29.33 [-41.35, -18.00] | -0.39 [-0.80, -0.06] |
| space-vs-medicine | SP | -22.67 [-33.33, -12.67] | -0.12 [-0.36, 0.09] |
| synthetic-balanced | PCF | -6.67 [-16.67, 0.00] | -0.08 [-0.22, 0.01] |
| synthetic-balanced | SP | -4.00 [-12.00, 0.00] | -0.03 [-0.09, 0.00] |
| synthetic-imbalanced | PCF | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| synthetic-imbalanced | SP | -2.00 [-4.02, 0.00] | -0.05 [-0.13, 0.00] |

## Interpretation

Relaxing the SP threshold saves 26 labels on politics/religion, with a macro-F1 difference of -0.31 points whose interval includes zero. Relaxing PCF saves 16 labels on that task, with a -0.45-point difference and an interval below zero. These comparisons have different reference methods and do not establish that SP outperforms PCF.

Window effects also depend on the task. At default SP, changing window three to one leaves graphics/Windows and balanced-synthetic outcomes unchanged in this condition. On the imbalanced synthetic task, it saves 8.67 labels [3.33, 15.33], with a macro-F1 difference of -0.17 points [-0.48, 0.06]. An interval spanning zero does not establish equivalence or acceptable performance loss.

Threshold changes alone do not remove finite-budget censoring. The sweep is descriptive, uses pointwise intervals without multiplicity correction, and does not select settings using held-out performance. A deployable recommendation would require a declared loss tolerance and separate development and confirmation data.

## Reproduction

Run the existing replay command with `configs/sensitivity.json`, then pass the resulting `sensitivity.csv` and stage `runs.csv` to `python -m stoplab.diagnostics --runs PATH --replay PATH --output PATH`. The input hashes and analyzed scope are recorded in [analysis.json](analysis.json). Local and compute-node executions produced identical output hashes.
