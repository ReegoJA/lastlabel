"""Command-line planning, offline execution, and aggregate reporting."""

import argparse
import hashlib
import importlib.metadata
import itertools
import json
import os
import pathlib
import platform
import tempfile

import threadpoolctl

from stoplab import data
from stoplab import experiment
from stoplab import report
from stoplab import replay


def source_hash() -> str:
    """Identify the exact Python source used for a run or resume operation."""
    digest = hashlib.sha256()
    for path in sorted(pathlib.Path(__file__).parent.glob("*.py")):
        digest.update(path.name.encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def atomic_json(path: pathlib.Path, value: dict):
    """Replace a complete artifact atomically to survive interrupted jobs."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w",
                                     encoding="utf-8",
                                     dir=path.parent,
                                     delete=False) as stream:
        temporary = pathlib.Path(stream.name)
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")
    os.replace(temporary, path)


def plan(path: pathlib.Path) -> tuple:
    """Expand a predeclared matrix into deterministic zero-based task IDs."""
    spec = json.loads(path.read_text(encoding="utf-8"))
    names = [item["name"] for item in spec["datasets"]]
    if len(names) != len(set(names)):
        raise ValueError("Dataset names must be unique.")
    tasks = []
    variants = spec.get("variants", [{"name": "baseline"}])
    if len({item["name"] for item in variants}) != len(variants):
        raise ValueError("Variant names must be unique.")
    for dataset, seed, query, noise, variant in itertools.product(
            spec["datasets"], spec["seeds"], spec["queries"],
            spec["noise_rates"], variants):
        parameters = {
            **spec["experiment"],
            **{
                key: value for key, value in variant.items() if key != "name"
            }
        }
        config = experiment.Config(**parameters,
                                   seed=seed,
                                   query=query,
                                   noise=noise,
                                   variant=variant["name"])
        tasks.append((dataset, config))
    identities = [(item[0]["name"], item[1].seed, item[1].query, item[1].noise,
                   item[1].variant) for item in tasks]
    if not tasks or len(identities) != len(set(identities)):
        raise ValueError(
            "Experiment grid is empty or contains duplicate tasks.")
    return spec, tasks


def execute(args):
    """Run independent tasks; completed results resume only with matching provenance."""
    spec, tasks = plan(args.config)
    versions = {
        name: importlib.metadata.version(name)
        for name in ("numpy", "scipy", "scikit-learn", "matplotlib")
    }
    manifest = {
        "specification": spec,
        "source_sha256": source_hash(),
        "versions": versions,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "expected_runs": len(tasks)
    }
    manifest_id = hashlib.sha256(json.dumps(
        manifest, sort_keys=True).encode()).hexdigest()
    manifest["manifest_id"] = manifest_id
    manifest_path = args.output / "manifest.json"
    if manifest_path.exists():
        old = json.loads(manifest_path.read_text(encoding="utf-8"))
        if old["manifest_id"] != manifest_id:
            raise ValueError(
                "Output belongs to different code/config/environment. Use a new directory."
            )
    atomic_json(manifest_path, manifest)
    indices = range(len(tasks)) if args.task is None else [args.task]
    for index in indices:
        if not 0 <= index < len(tasks):
            raise ValueError(f"Task ID must be in [0, {len(tasks) - 1}].")
        dataset_spec, config = tasks[index]
        dataset = data.load(dataset_spec, config.seed, str(args.cache),
                            args.download)
        path = args.output / f"run-{index:05d}.json"
        if path.exists():
            previous = json.loads(path.read_text(encoding="utf-8"))
            if (previous["manifest_id"] != manifest_id or
                    previous["dataset"]["fingerprint"]
                    != dataset.metadata["fingerprint"]):
                raise ValueError("Existing result has incompatible provenance.")
            print(f"Reused task {index}", flush=True)
            continue
        with threadpoolctl.threadpool_limits(limits=1):
            result = experiment.run(dataset, config)
        result.update(manifest_id=manifest_id,
                      task=index,
                      expected_runs=len(tasks))
        atomic_json(path, result)
        print(
            f"Completed {index + 1}/{len(tasks)}: {dataset_spec['name']} "
            f"seed={config.seed} query={config.query} noise={config.noise}",
            flush=True)


def main():
    """Dispatch the public command-line interface."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("plan", "fetch", "run"):
        command = commands.add_parser(name)
        command.add_argument("--config", type=pathlib.Path, required=True)
        if name != "plan":
            command.add_argument("--cache",
                                 type=pathlib.Path,
                                 default=pathlib.Path("data"))
        if name == "run":
            command.add_argument("--output", type=pathlib.Path, required=True)
            command.add_argument("--task", type=int)
            command.add_argument("--download", action="store_true")
    for name in ("report", "replay", "audit"):
        command = commands.add_parser(name)
        command.add_argument("--results", type=pathlib.Path, required=True)
        if name != "audit":
            command.add_argument("--output", type=pathlib.Path, required=True)
        if name == "replay":
            command.add_argument("--grid", type=pathlib.Path, required=True)
    args = parser.parse_args()
    if args.command == "plan":
        _, tasks = plan(args.config)
        print(
            json.dumps({
                "tasks": len(tasks),
                "slurm_array": f"0-{len(tasks) - 1}"
            }))
    elif args.command == "fetch":
        spec, _ = plan(args.config)
        for dataset in spec["datasets"]:
            loaded = data.load(dataset, spec["seeds"][0], str(args.cache), True)
            print(json.dumps(loaded.metadata))
    elif args.command == "run":
        execute(args)
    elif args.command == "report":
        print(json.dumps(report.generate(args.results, args.output)))
    elif args.command == "replay":
        print(json.dumps(replay.generate(args.results, args.grid, args.output)))
    else:
        print(json.dumps(replay.audit(args.results)))


if __name__ == "__main__":
    main()
