# Batch execution

The study uses CPU jobs and small-text 1.4.1. Install the package in a Python 3.11+ environment shared by compute nodes. Supply the account and partition permitted by your scheduler.

```sh
python -m pip install -e '.[dev]'
python -m stoplab fetch --config configs/cluster.json --cache data
python cluster/submit.py --config configs/cluster.json --output results/main --account YOUR_ACCOUNT
```

The submission tool previews its commands by default. Add `--submit` to submit the bounded array. Run the ablation and budget configurations in the same way, using distinct output directories. Measure representative tasks before setting resource limits.

After each stage completes, audit its records before reporting:

```sh
python -m stoplab audit --results results/main
python -m stoplab report --results results/main --output reports/main
python -m stoplab replay --results results/main --grid configs/sensitivity.json --output reports/main/sensitivity
```

Keep raw records, manifests, the source revision, dependency versions, and job logs in durable storage. The historical pilot uses an older engine and must not be resumed with the current implementation.
