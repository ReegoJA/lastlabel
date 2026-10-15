# Phoenix budget: initial follow-up comparisons

October 15, 2026. Training, outcome audit, reporting, and threshold replay completed successfully. These are descriptive comparisons of prespecified variants, not newly tuned rules. Training source was `7f7d2c74d018d93e2844f67317245eb5c8c3a893`.

This illustration uses all six tasks, uncertainty acquisition, linear SVM, 15% simulated symmetric annotation noise, and fixed-set SP. Each comparison includes 20 matched seeds. Differences are variant minus its declared within-learner reference. Negative label differences mean savings. Positive F1 differences mean better performance. Intervals are pointwise 95% percentile bootstrap intervals from 2,000 resamples of paired seeds. F1 is shown in percentage points.

| Task | Variant | Labels, difference [interval] | Macro F1, pp [interval] | Positive F1, pp [interval] |
| --- | --- | ---: | ---: | ---: |
| baseball-vs-hockey | budget-800 | 175.00 [157.00, 193.00] | 1.80 [0.99, 2.55] | 1.78 [1.03, 2.47] |
| graphics-vs-windows | budget-800 | 225.00 [183.97, 263.00] | 1.86 [1.01, 2.61] | 1.71 [0.84, 2.51] |
| politics-vs-religion | budget-800 | 208.00 [161.00, 255.00] | 1.31 [0.76, 1.88] | 1.13 [0.39, 1.85] |
| space-vs-medicine | budget-800 | 123.00 [91.00, 156.02] | 1.07 [0.28, 1.81] | 1.06 [0.29, 1.79] |
| synthetic-balanced | budget-800 | 316.00 [265.98, 358.00] | 1.66 [0.92, 2.45] | 1.90 [0.97, 2.99] |
| synthetic-imbalanced | budget-800 | 172.00 [114.00, 229.00] | -0.32 [-1.33, 0.53] | -0.63 [-2.54, 0.98] |

## Interpretation and limitations

The 800-label ceiling often spends more annotations and improves mean performance in this slice. The imbalanced synthetic task is an exception in mean macro F1. A larger budget is not automatically better, and a stopping rule is not validated merely because it eventually triggers. Compare cost and performance jointly, retaining budget fallbacks.

These runs use seeds 300-319. Compare 400 and 800 within this stage rather than against the main stage with different seeds. Fractional savings and hindsight peak-based diagnostics use different budget denominators or references, so the table uses absolute labels and F1.

The slice is descriptive and was selected for continuity with the initial main-study illustration. Full [variant comparisons](variants.csv), [stop-set comparisons](paired.csv), and [condition summaries](summary.csv) retain all settings. Intervals do not adjust for multiple comparisons. Text seeds share held-out documents, while synthetic seeds also change generated datasets. Positive-class F1 is not necessarily minority-class F1 in every task.

The completed follow-ups answer the planned budget and setting questions without additional training. Before another experiment, finish failure analysis and specify a concrete new hypothesis with separate development and confirmation data.
