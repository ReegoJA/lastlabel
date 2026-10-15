# Ablations: initial follow-up comparisons

October 15, 2026. Training, outcome audit, reporting, and threshold replay completed successfully. These are descriptive comparisons of prespecified variants, not newly tuned rules. Training source was `7f7d2c74d018d93e2844f67317245eb5c8c3a893`.

This illustration uses all six tasks, uncertainty acquisition, linear SVM, 15% simulated symmetric annotation noise, and fixed-set SP. Each comparison includes 20 matched seeds. Differences are variant minus its declared within-learner reference. Negative label differences mean savings. Positive F1 differences mean better performance. Intervals are pointwise 95% percentile bootstrap intervals from 2,000 resamples of paired seeds. F1 is shown in percentage points.

| Task | Variant | Labels, difference [interval] | Macro F1, pp [interval] | Positive F1, pp [interval] |
| --- | --- | ---: | ---: | ---: |
| baseball-vs-hockey | batch-5 | -55.25 [-70.01, -39.50] | -0.70 [-1.80, 0.27] | -0.49 [-1.57, 0.40] |
| baseball-vs-hockey | batch-50 | 0.00 [0.00, 0.00] | -0.29 [-1.30, 0.66] | 0.20 [-0.62, 0.99] |
| baseball-vs-hockey | stop-100 | -3.00 [-8.00, 0.00] | -0.16 [-0.48, 0.00] | -0.10 [-0.25, 0.00] |
| baseball-vs-hockey | stop-800 | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| graphics-vs-windows | batch-5 | -50.25 [-64.00, -35.74] | 0.02 [-0.89, 0.96] | 0.15 [-0.92, 1.38] |
| graphics-vs-windows | batch-50 | 0.00 [0.00, 0.00] | 0.19 [-0.53, 0.94] | 0.42 [-0.37, 1.21] |
| graphics-vs-windows | stop-100 | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| graphics-vs-windows | stop-800 | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| politics-vs-religion | batch-5 | -115.00 [-130.75, -98.75] | -1.55 [-2.47, -0.55] | -1.91 [-3.27, -0.46] |
| politics-vs-religion | batch-50 | 0.00 [0.00, 0.00] | -1.02 [-2.11, 0.18] | -0.81 [-2.36, 0.75] |
| politics-vs-religion | stop-100 | -5.00 [-13.00, 0.00] | -0.12 [-0.32, 0.00] | -0.16 [-0.41, 0.00] |
| politics-vs-religion | stop-800 | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| space-vs-medicine | batch-5 | -94.75 [-110.25, -79.25] | -1.00 [-1.94, -0.09] | -0.45 [-1.38, 0.56] |
| space-vs-medicine | batch-50 | 0.00 [0.00, 0.00] | 0.05 [-0.78, 0.85] | 0.44 [-0.62, 1.42] |
| space-vs-medicine | stop-100 | -5.00 [-14.00, 0.00] | -0.15 [-0.39, 0.00] | -0.15 [-0.40, 0.00] |
| space-vs-medicine | stop-800 | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| synthetic-balanced | batch-5 | -16.00 [-38.75, 0.00] | -0.68 [-1.42, 0.06] | -0.98 [-1.76, -0.18] |
| synthetic-balanced | batch-50 | 0.00 [0.00, 0.00] | -0.48 [-1.16, 0.19] | -0.45 [-1.19, 0.25] |
| synthetic-balanced | stop-100 | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| synthetic-balanced | stop-800 | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| synthetic-imbalanced | batch-5 | -76.50 [-100.50, -52.00] | 0.91 [-0.99, 2.88] | 1.92 [-1.62, 5.62] |
| synthetic-imbalanced | batch-50 | 1.50 [0.00, 4.50] | -0.64 [-2.12, 0.88] | -1.23 [-4.07, 1.69] |
| synthetic-imbalanced | stop-100 | -26.00 [-54.02, -4.98] | -0.67 [-1.70, -0.03] | -1.23 [-3.08, -0.06] |
| synthetic-imbalanced | stop-800 | 2.00 [0.00, 6.00] | -0.03 [-0.10, 0.00] | -0.06 [-0.18, 0.00] |

## Interpretation and limitations

Smaller batches change both acquisition timing and how often stability is checked. Batch-5 savings therefore cannot be attributed solely to stop-set selection. Changing stop-set size has smaller mean effects in several conditions, but a zero difference may reflect shared budget fallback rather than reliable early stopping.

These runs use seeds 200-219. Each variant is compared with its declared baseline from the same seed range.

The slice is descriptive and was selected for continuity with the initial main-study illustration. Full [variant comparisons](variants.csv), [stop-set comparisons](paired.csv), and [condition summaries](summary.csv) retain all settings. Intervals do not adjust for multiple comparisons. Text seeds share held-out documents, while synthetic seeds also change generated datasets. Positive-class F1 is not necessarily minority-class F1 in every task.

The completed follow-ups answer the planned budget and setting questions without additional training. Before another experiment, finish failure analysis and specify a concrete new hypothesis with separate development and confirmation data.
