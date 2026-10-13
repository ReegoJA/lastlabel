# LastLabel

**When should active learning stop?**

LastLabel benchmarks whether stopping rules save annotation effort without sacrificing predictive performance. It tests model stability under label noise, class imbalance, and biased stop sets.

Built from the STOPLAB research project. The Python package and CLI remain `stoplab`.

[Methods](docs/METHODS.md) · [Pilot findings](reports/pilot/FINDINGS.md) · [Research references](docs/REFERENCES.md)

## What it measures

- Stabilizing Predictions (SP) and Predicted Change of F (PCF), alongside confidence and fixed-budget baselines
- Fixed, remaining-pool, and initially easy stop sets
- Logistic regression and linear SVM with uncertainty or random acquisition
- Label savings, premature stops, excess labeling, and held-out F1
- Paired seed comparisons and threshold replay without retraining

Stopping decisions use predictions, not evaluation labels. Each trajectory continues to its budget so all criteria can be compared on the same model sequence.

## Quick start

Python 3.11+ and a CPU.

```sh
git clone https://github.com/ReegoJA/lastlabel.git
cd lastlabel
python -m pip install -e .
python -m stoplab run --config configs/smoke.json --output results/smoke
python -m stoplab audit --results results/smoke
python -m stoplab report --results results/smoke --output reports/smoke
```

The smoke experiment uses synthetic data and runs offline. Its report includes learning curves, per-rule results, and paired comparisons.

## Pilot

The included pilot contains **96 trajectories**, covering four binary classification tasks, two learners, two acquisition policies, two noise rates, and three seeds per condition. It produced 960 default-rule outcomes and 10,368 replay decisions. These are paired observations, not independent experiments.

Fixed-set SP stopped in 8 of 96 trajectories, compared with 30 for the remaining pool and 23 for the initially easy set. See the [findings](reports/pilot/FINDINGS.md) for the performance trade-offs and uncertainty. Three-seed intervals are exploratory.

![One pilot trajectory and its stop-set agreement](reports/pilot/trajectory.png)

Audit the included records or replay another threshold grid:

```sh
python -m stoplab audit --results results/pilot
python -m stoplab replay --results results/pilot --grid configs/sensitivity.json --output reports/replay
```

To rerun the text benchmarks, fetch the corpus once, then use a fresh output directory:

```sh
python -m stoplab fetch --config configs/pilot.json --cache data
python -m stoplab run --config configs/pilot.json --cache data --output results/pilot-new
```

The 5,120-trajectory [cluster study](docs/STUDY.md) is configured but has not run. [Slurm instructions](docs/CLUSTER.md) cover task arrays and resumption.

## Scope

This is a binary-classification research benchmark. Its noise models and stop-set experiments extend the cited methods. It does not reproduce the papers' original experimental tables.

A rule that never triggers uses the final-budget model and is marked as censored. Test metrics are retrospective. Threshold sweeps are exploratory and should not be used to select a rule and claim independent test performance on the same data.

The bundled pilot predates the release's stricter artifact checks. Its original manifest and measurements are preserved and pass the updated audit. New runs require a fresh output directory because the source fingerprint has changed.

## Project structure

| Path | Contents |
| --- | --- |
| `stoplab/` | Data loading, learners, stopping rules, experiments, reporting, replay, and CLI |
| `tests/` | Equation, isolation, determinism, budget, and artifact checks |
| `configs/` | Smoke, pilot, sensitivity, and cluster specifications |
| `cluster/` | Slurm array launcher |
| `docs/` | Methods, study design, cluster usage, and references |
| `results/pilot/` | Original pilot manifest and run records |
| `reports/pilot/` | Findings, tables, figures, and threshold replay |
| `requirements-pilot.txt` | Original pilot environment |

For development and tests, see [CONTRIBUTING.md](CONTRIBUTING.md).

## Credits and license

Created October 13, 2026 by Reego John-Annaselvan. [MIT license](LICENSE). Release history is in [CHANGELOG.md](CHANGELOG.md).

SP follows Bloodgood and Vijay-Shanker. PCF follows Altschuler and Bloodgood. Stop-set comparisons draw on Kurlandski and Bloodgood. Full papers and implementation details are in [REFERENCES.md](docs/REFERENCES.md).

Uses NumPy and SciPy for numerical work, scikit-learn for datasets and learners, Matplotlib for figures, and threadpoolctl for CPU limits. Development tools include pytest, YAPF, and setuptools. Their maintainers and licenses are credited in the references. Raw 20 Newsgroups text is downloaded separately and is not included in this repository.
