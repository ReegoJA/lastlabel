# Running LastLabel on PACE Phoenix

The study uses CPU jobs. Phoenix's Slurm scheduler runs trajectories independently. No GPU is needed for the current linear learners.

## Files to upload

Use the supplied `lastlabel-phoenix.zip`, or clone `https://github.com/ReegoJA/lastlabel.git` on Phoenix. The archive contains:

- `stoplab/`
- `configs/`
- `cluster/`
- `tests/`
- `docs/`
- `pyproject.toml`, `README.md`, `LICENSE`, `CITATION.cff`, `CONTRIBUTING.md`, `CHANGELOG.md`, `.style.yapf`

The pilot results, reports, local Python environments, and cached corpus are not required for new runs. Download the corpus once on Phoenix, or transfer the existing cache to the `data/` directory if compute-node networking is unavailable.

Use the Phoenix login address and Georgia Tech VPN instructions supplied with your account. PACE's older documentation has moved to its ServiceNow knowledge base, linked from [Accessing Clusters](https://docs.pace.gatech.edu/faqs/accessingClusters/). Use your actual charge account and permitted partition. None is embedded in the scripts.

Extract the archive into a shared project/work directory accessible to compute nodes. Keep long-term results in backed-up project storage. PACE scratch is temporary and is not a backup.

## Prepare the environment

From the repository root, load a PACE-supported Python 3.11+ environment and create the virtual environment on the cluster. Do not upload a Windows virtual environment.

```sh
python -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
mkdir -p logs
.venv/bin/python -m stoplab plan --config configs/cluster.json
.venv/bin/python -m stoplab plan --config configs/cluster-ablations.json
.venv/bin/python -m stoplab plan --config configs/cluster-budget.json
```

The task counts are 8640, 4800, and 1920. Planning and job submission are lightweight. Run training, tests, and report generation on allocated compute nodes.

On a compute node obtained through your Phoenix allocation, validate the installation and fetch the text corpus:

```sh
.venv/bin/python -m pytest -q
.venv/bin/python -m stoplab fetch --config configs/cluster.json --cache data
```

All later training runs use the cache offline. Every task in one output directory must use the same source and Python environment. Keep the checkout unchanged while jobs run.

## Measure representative jobs

Replace `YOUR_ACCOUNT` with your Phoenix charge account. Add `--partition=YOUR_PARTITION` only if your allocation requires it. The resource settings below are initial requests, not measured requirements.

```sh
sbatch --account=YOUR_ACCOUNT --array=0,2883%2 --export=ALL,STOPLAB_CONFIG=configs/cluster.json,STOPLAB_OUTPUT=results/phoenix-main cluster/run.sbatch
sbatch --account=YOUR_ACCOUNT --array=1606 --export=ALL,STOPLAB_CONFIG=configs/cluster-ablations.json,STOPLAB_OUTPUT=results/phoenix-ablations cluster/run.sbatch
sbatch --account=YOUR_ACCOUNT --array=1603 --export=ALL,STOPLAB_CONFIG=configs/cluster-budget.json,STOPLAB_OUTPUT=results/phoenix-budget cluster/run.sbatch
```

These cover a synthetic baseline, text SVM, small-batch text SVM, and 800-label text SVM. The script requests one CPU, 4 GB, and two hours per task. Inspect scheduler measurements:

```sh
sacct -j YOUR_JOB_ID --format=JobID,State,Elapsed,TotalCPU,MaxRSS,ExitCode
```

Use elapsed time and peak memory to adjust `--time` and `--mem`. If a task hits a resource limit, increase the allocation and rerun that task with the same study settings. Do not shrink budgets silently. Measure other conditions if their costs differ substantially.

## Submit the study

The helper prints a submission plan by default. It submits only when `--submit` is present. Run one stage at a time so their concurrency caps do not add together.

```sh
.venv/bin/python cluster/submit.py --config configs/cluster.json --output results/phoenix-main --account YOUR_ACCOUNT
```

After reviewing the plan and resource measurements:

```sh
.venv/bin/python cluster/submit.py --config configs/cluster.json --output results/phoenix-main --account YOUR_ACCOUNT --submit
```

Once the main stage finishes, use the same command with `configs/cluster-ablations.json` and `results/phoenix-ablations`, then with `configs/cluster-budget.json` and `results/phoenix-budget`.

The helper uses arrays of at most 500 elements and a default limit of 10 simultaneous jobs. Adjust `--array-size` and `--concurrency` to your allocation and the scheduler's current limits. Chunks use `afterany` dependencies, so the next chunk waits for the preceding array to finish. Failed tasks remain visible in the audit and need rerunning.

`--tasks-per-job N` groups adjacent trajectories in one job to reduce scheduling overhead. The default is one. Choose N after timing the workload and increase the job's wall-time request accordingly. Grouping does not change experiment settings or result identities. The final group is clipped to the task count.

Other options: `--partition`, `--time`, and `--mem`. `STOPLAB_PYTHON` and `STOPLAB_CACHE` can override the Python executable and data cache used by the batch runner. Absolute paths are useful when using shared storage.

## Audit, analyze, and retrieve

On an allocated compute node, audit each stage:

```sh
.venv/bin/python -m stoplab audit --results results/phoenix-main
.venv/bin/python -m stoplab audit --results results/phoenix-ablations
.venv/bin/python -m stoplab audit --results results/phoenix-budget
```

For the main stage, generate tables and replay thresholds:

```sh
.venv/bin/python -m stoplab report --results results/phoenix-main --output reports/phoenix-main
.venv/bin/python -m stoplab replay --results results/phoenix-main --grid configs/sensitivity.json --output reports/phoenix-main/sensitivity
```

Repeat with each stage's own directories. The current analysis loads a stage's records into memory, so request more RAM than a single training task and measure usage before replaying the full matrix. Keep stages separate. If memory is insufficient, stop and add streaming analysis rather than pooling incomplete chunks as final results.

Copy back the complete `results/phoenix-*` and `reports/phoenix-*` directories, the exact configs/source revision, and Slurm logs. Reports alone do not preserve query histories or provenance. New tasks can resume after interruption, but an interrupted trajectory restarts from its beginning.

## PACE acknowledgment

The planned resource is Phoenix, operated by the **Partnership for an Advanced Computing Environment (PACE) at Georgia Tech, RRID:SCR_027619**. The existing pilot was run locally.

After these runs actually use Phoenix, include an acknowledgment such as:

> Computing for these experiments was provided by Georgia Tech's Partnership for an Advanced Computing Environment (PACE), using the Phoenix cluster (RRID:SCR_027619).

Follow [PACE's current acknowledgment guidance](https://pace.gatech.edu/citing-pace/) in publications. Do not label the local pilot as a PACE result.

References: [PACE documentation entry point](https://docs.pace.gatech.edu/), [Phoenix Slurm guide](https://docs.pace.gatech.edu/phoenix_cluster/slurm_guide_phnx/), [Slurm job arrays](https://slurm.schedmd.com/job_array.html).
