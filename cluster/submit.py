"""Plan bounded Slurm arrays, submitting only with an explicit flag."""

import argparse
import math
import pathlib
import shlex
import subprocess

from stoplab import cli


def chunks(total, tasks_per_job, array_size):
    """Yield disjoint task offsets and array lengths covering the matrix."""
    if min(total, tasks_per_job, array_size) < 1:
        raise ValueError("Task and array sizes must be positive.")
    span = tasks_per_job * array_size
    for offset in range(0, total, span):
        yield offset, math.ceil(min(span, total - offset) / tasks_per_job)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=pathlib.Path, required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    parser.add_argument("--account", required=True)
    parser.add_argument("--partition")
    parser.add_argument("--tasks-per-job", type=int, default=1)
    parser.add_argument("--array-size", type=int, default=500)
    parser.add_argument("--concurrency", type=int, default=10)
    parser.add_argument("--time", default="02:00:00")
    parser.add_argument("--mem", default="4G")
    parser.add_argument("--submit", action="store_true")
    args = parser.parse_args()
    if args.concurrency < 1:
        parser.error("Concurrency must be positive.")
    root = pathlib.Path(__file__).resolve().parents[1]
    if pathlib.Path.cwd().resolve() != root:
        parser.error("Run this command from the repository root.")
    if any("," in str(value) for value in (args.config, args.output)):
        parser.error("Exported paths cannot contain commas.")
    _, tasks = cli.plan(args.config)
    dependency = None
    for offset, count in chunks(len(tasks), args.tasks_per_job,
                                args.array_size):
        command = [
            "sbatch", "--parsable", f"--account={args.account}",
            f"--array=0-{count - 1}%{args.concurrency}", f"--time={args.time}",
            f"--mem={args.mem}", "--export=ALL," + ",".join([
                f"STOPLAB_CONFIG={args.config}",
                f"STOPLAB_OUTPUT={args.output}",
                f"STOPLAB_TASK_OFFSET={offset}",
                f"STOPLAB_TASKS_PER_JOB={args.tasks_per_job}"
            ])
        ]
        if args.partition:
            command.append(f"--partition={args.partition}")
        if dependency:
            command.append(f"--dependency=afterany:{dependency}")
        command.append("cluster/run.sbatch")
        print(shlex.join(command), flush=True)
        if args.submit:
            pathlib.Path("logs").mkdir(exist_ok=True)
            response = subprocess.check_output(command, text=True).strip()
            dependency = response.split(";")[0]
            if not dependency.isdecimal():
                raise RuntimeError(
                    "Unexpected sbatch response. Check submitted jobs before retrying."
                )
            print(f"Submitted {dependency}", flush=True)
        else:
            dependency = "PREVIOUS_JOB_ID"


if __name__ == "__main__":
    main()
