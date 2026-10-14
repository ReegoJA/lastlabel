# LastLabel

**When should active learning stop asking for labels?**

LastLabel builds directly on Dr. Michael Bloodgood's research on stopping active learning and my undergraduate research with him at The College of New Jersey. His work with K. Vijay-Shanker, John Grothendieck, Michael Altschuler, and Luke Kurlandski provides the methodological foundation for this project.

The goal is to identify when a model's apparent stability is a reliable reason to stop annotation. Stopping too early can sacrifice predictive performance. Stopping too late spends time and money labeling examples that add little value. LastLabel measures that trade-off and tests where the published criteria become less reliable under noisy labels or biased stop sets.

This is a research benchmark for practitioners choosing a stopping policy and researchers testing improvements. It provides paired comparisons, auditable run records, and reusable experiments. It does not claim a new stopping algorithm or an exact reproduction of the papers' published tables.

[Methods](docs/METHODS.md) / [Study design](docs/STUDY.md) / [Pilot findings](reports/pilot/FINDINGS.md) / [Phoenix guide](docs/CLUSTER.md)

The active-learning engine is [small-text](https://github.com/webis-de/small-text). LastLabel adds stopping-rule evaluation, noise experiments, and auditable reports. The Python package and CLI retain the name `stoplab`.

## Research foundation

- **Stabilizing Predictions:** Bloodgood and Vijay-Shanker, [2009](https://aclanthology.org/W09-1107/). Agreement between successive models supplies a label-free stopping signal.
- **Theory:** Bloodgood and Grothendieck, [2015](https://arxiv.org/abs/1504.06329). Analysis connecting prediction stability with changes in F measure.
- **Predicted Change of F:** Altschuler and Bloodgood, [2019](https://arxiv.org/abs/1901.09118). A stopping criterion estimating changes in positive-class F measure.
- **Stop-set selection:** Kurlandski and Bloodgood, [2022](https://arxiv.org/abs/2201.05460). The basis for comparing a representative fixed stop set with the shrinking unlabeled pool.

LastLabel extends these ideas with simulated annotation noise, an initially easy stop set, matched learner comparisons, and offline threshold replay. The [study specification](docs/STUDY.md) distinguishes paper-derived methods from these extensions and explains each experimental choice. Full attribution is in [REFERENCES.md](docs/REFERENCES.md).

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

The smoke experiment runs offline with synthetic data. Reports measure label savings, premature stops, excess labeling, and held-out F1. Stopping decisions never use evaluation labels.

## Completed pilot

The bundled pilot contains **96 trajectories**, four binary tasks, two learners, two acquisition policies, two noise rates, and three seeds per condition. It produced 960 default-rule outcomes and 10,368 replay decisions. These reuse the same trajectories and are not independent experiments.

Fixed-set SP stopped in 8 of 96 trajectories, compared with 30 for the remaining pool and 23 for the initially easy set. The [findings](reports/pilot/FINDINGS.md) describe the performance trade-offs. Three-seed intervals are exploratory.

![One pilot trajectory and its stop-set agreement](reports/pilot/trajectory.png)

```sh
python -m stoplab audit --results results/pilot
python -m stoplab replay --results results/pilot --grid configs/sensitivity.json --output reports/replay
```

The pilot predates the small-text migration. Its records and manifest are preserved. New runs use small-text 1.4.1 and require new output directories. See [implementation details](docs/METHODS.md#small-text-engine) for compatibility checks and stopping-rule differences.

## Expanded Phoenix study

| Stage | Trajectories | Question |
| --- | ---: | --- |
| Robustness | 8,640 | How do stop-set effects change with learner, task, and annotation-noise mechanism? |
| Controlled ablations | 4,800 | Are differences driven by query batch size or stop-set size? |
| Budget extension | 1,920 | Does a 400-label ceiling hide later stopping behavior? |

The **15,360 planned trajectories** cover six tasks. The main stage uses 30 seeds per condition, with 20 per condition in each follow-up stage. Four text tasks come from the same 20 Newsgroups corpus, alongside two synthetic conditions. The larger study has not run.

The execution workflow targets Georgia Tech's **PACE Phoenix** cluster, provided by the Partnership for an Advanced Computing Environment (**RRID:SCR_027619**). PACE is the intended infrastructure for this study. The completed pilot ran locally. See the [Phoenix guide](docs/CLUSTER.md) for setup, resource measurement, and the acknowledgment to use after cluster execution.

## Project structure

| Path | Contents |
| --- | --- |
| `stoplab/` | Data, learners, stopping rules, experiments, reports, replay, and CLI |
| `tests/` | Equations, isolation, pairing, task coverage, and artifact checks |
| `configs/` | Smoke, pilot, expanded studies, and replay specifications |
| `cluster/` | Slurm runner and bounded-array submission tool |
| `docs/` | Methods, study design, Phoenix guide, and references |
| `results/pilot/`, `reports/pilot/` | Completed pilot evidence |
| `requirements-pilot.txt` | Original pilot environment |

## Credits and license

Created October 13, 2026 by Reego John-Annaselvan. [MIT license](LICENSE). [Release history](CHANGELOG.md). [Contributing](CONTRIBUTING.md).

Dr. Michael Bloodgood's research and my work with him are the starting point for LastLabel. The cited coauthors share credit for the underlying methods. The extensions and this implementation are my responsibility.

Uses small-text, NumPy, SciPy, scikit-learn, Matplotlib, and threadpoolctl. Development tools include pytest, YAPF, and setuptools. Maintainer and license details are in [REFERENCES.md](docs/REFERENCES.md). Raw 20 Newsgroups text is downloaded separately.
