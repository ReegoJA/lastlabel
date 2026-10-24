# Research result artifacts

The [v0.4.0 release](https://github.com/ReegoJA/lastlabel/releases/tag/v0.4.0) contains the completed descriptive study. No new model training is needed to reproduce the analyses below.

| Asset | Contents |
| --- | --- |
| `study-records.tar.gz` | All 15,360 trajectory JSON records and three original training manifests |
| `analysis-tables.zip` | Per-run tables for all three stages and the main-stage threshold replay table |
| `record-hashes.json` | SHA-256 of each unchanged archived JSON record |
| `SHA256SUMS.txt` | SHA-256 of the distributed assets |

The result archive contains numeric metrics, query indices, configuration, and provenance, not raw corpus documents or fitted models. Logs, local workflow notes, and repository backups are excluded. Training used revision `7f7d2c74d018d93e2844f67317245eb5c8c3a893`. Each manifest records the training environment. Analysis uses the tagged release code. Original outcome fields are preserved, including the historical `premature` field, which denotes a retrospective performance gap rather than necessarily an early stop.

Extract `analysis-tables.zip` at the repository root. Install the project as described in the README, then run:

```sh
python -m stoplab.interactions --runs reports/main/runs.csv --output reports/main/interactions
python -m stoplab.diagnostics --runs reports/main/runs.csv --replay reports/main/sensitivity.csv --output reports/main/diagnostics
python -m stoplab.diagnostics --runs reports/ablations/runs.csv --output reports/ablations/diagnostics
python -m stoplab.diagnostics --runs reports/budget/runs.csv --output reports/budget/diagnostics
python -m stoplab.conventions --archive study-records.tar.gz --prefix results/phoenix-main --output reports/main/conventions
python -m stoplab.cases --archive study-records.tar.gz --prefix results/phoenix-main --output reports/main/diagnostics/cases.json
```

Archive prefixes retain the original result directory names. The original private backup and the distributed result-only archive have different container hashes. Their included JSON records are byte-identical, as checked by `record-hashes.json`. Replaying a different archive container changes the archive hash in analysis metadata, not the scientific outputs.

The [technical report source](../paper/lastlabel.tex) contains the methods, results, and limitations. The [main findings](../reports/main/FINDINGS.md) provide a readable web summary. This release completes the stated descriptive study, not a new stopping algorithm or a claim of peer-reviewed novelty. Additional corpora, real annotation errors, and separately validated interventions remain future research.
