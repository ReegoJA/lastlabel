# Noise and stop-set interactions

For each seed, compute `(alternative minus fixed) noisy minus (alternative minus fixed) clean`, then bootstrap those paired differences. The complete matrix contains 864 correlated contrasts with 30 seeds each. Intervals are pointwise 95% percentile intervals from 2,000 resamples. This is exploratory, not a preregistered confirmatory analysis.

The table retains all six tasks in the existing illustrative condition: linear SVM, uncertainty acquisition, 15% symmetric noise, SP, easy versus fixed.

| Task | Labels interaction [95% interval] | Macro F1 interaction, points [95% interval] |
| --- | ---: | ---: |
| baseball-vs-hockey | 0.00 [-3.33, 3.33] | 0.12 [-0.00, 0.28] |
| graphics-vs-windows | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| politics-vs-religion | 4.00 [-2.67, 10.67] | 0.02 [-0.15, 0.21] |
| space-vs-medicine | 16.67 [7.33, 27.33] | 0.12 [-0.11, 0.39] |
| synthetic-balanced | 8.00 [-62.02, 80.68] | -1.62 [-4.21, 0.74] |
| synthetic-imbalanced | -26.00 [-86.00, 32.67] | -3.28 [-6.28, -0.44] |

The balanced-synthetic interval includes zero. Its noisy easy-set performance loss is not sufficient evidence that noise increases that loss relative to clean training. The imbalanced macro-F1 interaction is below zero in this condition, but its annotation-count interval spans zero. These findings do not establish a general ranking across tasks or a multiplicity-adjusted discovery.

Class-conditional noise rates are conditional on the affected clean class. Equal nominal rates are not equal total corruption rates. Positive-class F1 and all settings are retained in [interactions.csv](interactions.csv).

Reproduce with `python -m stoplab.interactions --runs reports/main/runs.csv --output reports/main/interactions`. See [result artifacts](../../../docs/RESULTS.md).
