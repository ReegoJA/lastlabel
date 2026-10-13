# Slurm execution

The job array uses one CPU per task. Set the account, partition, and resource limits for your cluster.

## Prepare the project

Copy the project to a working directory on the cluster. Load a site-supported
Python 3.11+ module according to PACE's documentation, create one environment
shared by all tasks. Install once on a node where installation is permitted.

```sh
python -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python -m pytest -q
.venv/bin/python -m stoplab fetch --config configs/cluster.json --cache data
mkdir -p logs
.venv/bin/python -m stoplab plan --config configs/cluster.json
```

The last command reports 5,120 tasks, IDs 0–5119. The fetch step downloads and
caches the public text corpus once. Compute jobs then run without network
access. Follow local guidance for storage quotas and shared filesystem use.

## Measure one task first

The launcher requests one CPU, 4 GB, and two hours as conservative starting
limits, not measured guarantees. First submit one task with your allocation
flags. For a text SVM task in the declared cluster ordering, task 2561 exercises
the second learner on the first text condition.

```sh
export STOPLAB_CONFIG=configs/cluster.json
export STOPLAB_OUTPUT=results/cluster
sbatch --array=1 --export=ALL,STOPLAB_TASK_OFFSET=2560 cluster/run.sbatch
```

Add your approved `--account`, `--partition`, or `--qos` flags if required.
Inspect `sacct` elapsed time, MaxRSS, and exit status. Tune limits based on the
slowest relevant variant, especially batch 5. Wall-time measurements from the
local pilot are not cluster benchmarks.

## Submit bounded arrays

Site array-size limits may be lower than 5,120 tasks. The launcher supports a
global task offset, so the following chunks only require array indices up to
999. Reduce chunk size if your site's current policy requires it:

```sh
sbatch --array=0-999%20 --export=ALL,STOPLAB_TASK_OFFSET=0 cluster/run.sbatch
sbatch --array=0-999%20 --export=ALL,STOPLAB_TASK_OFFSET=1000 cluster/run.sbatch
sbatch --array=0-999%20 --export=ALL,STOPLAB_TASK_OFFSET=2000 cluster/run.sbatch
sbatch --array=0-999%20 --export=ALL,STOPLAB_TASK_OFFSET=3000 cluster/run.sbatch
sbatch --array=0-999%20 --export=ALL,STOPLAB_TASK_OFFSET=4000 cluster/run.sbatch
sbatch --array=0-119%20 --export=ALL,STOPLAB_TASK_OFFSET=5000 cluster/run.sbatch
```

`%20` caps concurrency **per submission**, so six simultaneous submissions can
run 120 jobs. Submit sequentially or reduce those caps to stay within your
allocation. The offset maps scheduler indices to unique global experiment IDs,
keep offsets and ranges disjoint within a shared result directory.

The environment can override `STOPLAB_PYTHON`, `STOPLAB_CONFIG`, `STOPLAB_CACHE`,
and `STOPLAB_OUTPUT`. BLAS thread counts are capped at one. Preserve the same
Python/dependency environment and source checkout for every task in a study.
Changed code or platform requires a new output directory. Identical completed
tasks are reused, interrupted tasks restart. Do not launch the same task twice
concurrently or change files while jobs are running.

## Audit and analyze

```sh
.venv/bin/python -m stoplab audit --results results/cluster
.venv/bin/python -m stoplab report --results results/cluster --output reports/cluster
.venv/bin/python -m stoplab replay --results results/cluster --grid configs/sensitivity.json --output reports/cluster/sensitivity
```

The audit reports completed versus expected trajectories and verifies query
hashes and stop-decision replay. An incomplete matrix is explicitly reported,
resubmit missing/failed task IDs before interpreting the final study. Reports
can inspect partial results, but missing jobs may create unequal seed counts.

References: [PACE Slurm guide](https://docs.pace.gatech.edu/phoenix_cluster/slurm_guide_phnx/),
[Slurm arrays](https://slurm.schedmd.com/job_array.html), and
[sbatch](https://slurm.schedmd.com/sbatch.html).
