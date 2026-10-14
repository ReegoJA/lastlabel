#!/usr/bin/env bash
#SBATCH --job-name=stoplab
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=02:00:00
#SBATCH --output=logs/stoplab-%A_%a.out

set -euo pipefail
cd "${SLURM_SUBMIT_DIR}"
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
offset="${STOPLAB_TASK_OFFSET:-0}"
[[ "$offset" =~ ^[0-9]+$ ]] || { echo "Invalid task offset" >&2; exit 2; }
task_count="${STOPLAB_TASKS_PER_JOB:-1}"
[[ "$task_count" =~ ^[1-9][0-9]*$ ]] || { echo "Invalid task count" >&2; exit 2; }
task_id=$((SLURM_ARRAY_TASK_ID * task_count + offset))
"${STOPLAB_PYTHON:-.venv/bin/python}" -m stoplab run \
  --config "${STOPLAB_CONFIG:-configs/cluster.json}" \
  --cache "${STOPLAB_CACHE:-data}" \
  --output "${STOPLAB_OUTPUT:-results/cluster}" \
  --task "$task_id" --task-count "$task_count"
