# Selected descriptive trajectories

Within the existing SVM, uncertainty, 15% symmetric-noise condition, select the lower median retrospective performance gap among early triggers for each task and SP stop set. If no early trigger occurs, select among all runs. Break ties by ascending seed. This post-hoc descriptive selection is not a random sample or an estimate of average effect. Fixed and easy examples may use different seeds and must not be treated as paired comparisons.

| Task | Rule | Seed | Labels | Selected macro F1 | Gap to later or earlier trajectory peak |
| --- | --- | ---: | ---: | ---: | ---: |
| baseball-vs-hockey | sp:easy | 104 | 400 | 0.8289 | 0.0027 |
| baseball-vs-hockey | sp:fixed | 104 | 400 | 0.8289 | 0.0027 |
| graphics-vs-windows | sp:easy | 125 | 400 | 0.7529 | 0.0066 |
| graphics-vs-windows | sp:fixed | 125 | 400 | 0.7529 | 0.0066 |
| politics-vs-religion | sp:easy | 100 | 340 | 0.7148 | 0.0222 |
| politics-vs-religion | sp:fixed | 125 | 400 | 0.7092 | 0.0123 |
| space-vs-medicine | sp:easy | 116 | 360 | 0.8250 | 0.0053 |
| space-vs-medicine | sp:fixed | 121 | 400 | 0.8479 | 0.0050 |
| synthetic-balanced | sp:easy | 119 | 100 | 0.5595 | 0.0811 |
| synthetic-balanced | sp:fixed | 123 | 400 | 0.7916 | 0.0000 |
| synthetic-imbalanced | sp:easy | 119 | 100 | 0.5581 | 0.1206 |
| synthetic-imbalanced | sp:fixed | 107 | 360 | 0.6669 | 0.0107 |

The two synthetic easy-set examples stop at 100 labels before later performance improvements. This illustrates the observed stability/performance mismatch without proving that stop-set bias is its unique cause. The text fallback examples illustrate budget censoring. The full selected traces and selection metadata are retained in [cases.json](cases.json).

Reproduce with `python -m stoplab.cases --archive study-records.tar.gz --prefix results/phoenix-main --output reports/main/diagnostics/cases.json`. See [result artifacts](../../../docs/RESULTS.md).
