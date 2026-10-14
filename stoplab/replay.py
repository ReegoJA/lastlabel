"""Counterfactual threshold sweeps and validation of saved experiment records."""

import hashlib
import dataclasses
import itertools
import json
import pathlib

import numpy as np

from stoplab import report
from stoplab import rules
from stoplab import experiment


def load_runs(results: pathlib.Path) -> tuple:
    """Read a manifest and runs, rejecting mixed or duplicated task records."""
    manifest = json.loads(
        (results / "manifest.json").read_text(encoding="utf-8"))
    identity = {
        key: value for key, value in manifest.items() if key != "manifest_id"
    }
    digest = hashlib.sha256(json.dumps(identity,
                                       sort_keys=True).encode()).hexdigest()
    if digest != manifest["manifest_id"]:
        raise ValueError("Manifest hash mismatch.")
    spec = manifest["specification"]
    tasks = []
    for dataset, seed, query, noise, variant in itertools.product(
            spec["datasets"], spec["seeds"], spec["queries"],
            spec["noise_rates"], spec.get("variants", [{
                "name": "baseline"
            }])):
        parameters = {
            **spec["experiment"],
            **{
                key: value for key, value in variant.items() if key not in {
                    "name", "reference"
                }
            }
        }
        config = experiment.Config(**parameters,
                                   seed=seed,
                                   query=query,
                                   noise=noise,
                                   variant=variant["name"])
        tasks.append((dataset["name"], dataclasses.asdict(config)))
    if len(tasks) != manifest["expected_runs"]:
        raise ValueError("Manifest task count mismatch.")
    runs = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(results.glob("run-*.json"))
    ]
    seen = set()
    for run in runs:
        if run["manifest_id"] != manifest["manifest_id"]:
            raise ValueError("Run does not match experiment manifest.")
        if run["task"] in seen or not 0 <= run["task"] < manifest[
                "expected_runs"]:
            raise ValueError("Duplicate or invalid task ID.")
        seen.add(run["task"])
        name, config = tasks[run["task"]]
        if (run["config"] != config or run["dataset"]["name"] != name or
                run["expected_runs"] != len(tasks)):
            raise ValueError(
                "Run configuration does not match its manifest task.")
    if not runs:
        raise ValueError("No completed runs found.")
    return manifest, runs


def decision(trace: list, method: str, stop_set: str, threshold: float,
             window: int) -> tuple:
    """Replay one label-free rule; return its record and censoring indicator."""
    rule = rules.StopRule(method, threshold, window)
    statistic = "kappa" if method == "sp" else method
    for row in trace:
        if rule.update(row["statistics"][stop_set][statistic]):
            return row, True
    return trace[-1], False


def audit(results: pathlib.Path) -> dict:
    """Check provenance, label accounting, hashes, and saved stop decisions."""
    manifest, runs = load_runs(results)
    for run in runs:
        cfg = run["config"]
        previous = []
        trace = run["trace"]
        if not trace or trace[-1]["labels"] != cfg["budget"]:
            raise ValueError("Incomplete trajectory.")
        pool_size = run["dataset"]["pool_size"]
        for row in trace:
            indices = row["queried_indices"]
            if (len(indices) != row["labels"] or
                    len(set(indices)) != row["labels"] or
                    indices[:len(previous)] != previous or
                    any(index < 0 or index >= pool_size for index in indices)):
                raise ValueError("Invalid query history.")
            if (previous and len(indices) != min(
                    len(previous) + cfg["batch"], cfg["budget"])):
                raise ValueError("Invalid query batch size.")
            if not previous and not cfg["initial"] <= len(
                    indices) <= cfg["budget"]:
                raise ValueError("Invalid initial query size.")
            digest = hashlib.sha256(
                np.asarray(indices, dtype=np.int64).tobytes()).hexdigest()
            if digest != row["training_index_hash"]:
                raise ValueError("Training index hash mismatch.")
            if row["statistics"]["remaining"]["size"] != pool_size - len(
                    indices):
                raise ValueError("Remaining-set accounting mismatch.")
            for metric in ("macro_f1", "positive_f1", "auc"):
                if not 0 <= row[metric] <= 1:
                    raise ValueError("Metric outside its valid range.")
            previous = indices
        expected_rules = {
            f"{method}:{stop_set}" for method in ("sp", "pcf", "confidence")
            for stop_set in ("fixed", "remaining", "easy")
        }
        expected_rules.add("budget:all")
        if (len(run["outcomes"]) != len(expected_rules) or
            {row["rule"] for row in run["outcomes"]} != expected_rules):
            raise ValueError("Missing or duplicate stopping outcomes.")
        peak = max(row["macro_f1"] for row in trace)
        target = peak - cfg["tolerance"]
        reference = next(
            row["labels"] for row in trace if row["macro_f1"] >= target)
        if run["retrospective"] != {
                "peak_macro_f1": peak,
                "earliest_near_peak_labels": reference
        }:
            raise ValueError("Retrospective reference mismatch.")
        for outcome in run["outcomes"]:
            method, stop_set = outcome["rule"].split(":")
            if method == "budget":
                selected, stopped = trace[-1], False
            else:
                selected, stopped = decision(
                    trace, method, stop_set,
                    cfg["kappa" if method == "sp" else method], cfg["window"])
            expected = {
                key: selected[key]
                for key in ("labels", "macro_f1", "positive_f1", "auc")
            }
            expected.update(
                stopped=stopped,
                f1_gap_to_peak=peak - selected["macro_f1"],
                label_savings=1 - selected["labels"] / cfg["budget"],
                premature=selected["macro_f1"] < target,
                excess_labels=max(0, selected["labels"] - reference))
            if any(outcome[key] != value for key, value in expected.items()):
                raise ValueError("Saved outcome does not match replay.")
    return {
        "validated_runs": len(runs),
        "expected_runs": manifest["expected_runs"],
        "complete": len(runs) == manifest["expected_runs"],
        "manifest_id": manifest["manifest_id"]
    }


def generate(results: pathlib.Path, grid: pathlib.Path,
             output: pathlib.Path) -> dict:
    """Evaluate declared thresholds without retraining or selecting a winner.

    A sweep reuses the same trajectories and is exploratory. Evaluation
    labels must not be used to select thresholds for a confirmatory claim.
    """
    validation = audit(results)
    _, runs = load_runs(results)
    specification = json.loads(grid.read_text(encoding="utf-8"))
    rows = []
    for run in runs:
        cfg = run["config"]
        for method, thresholds in specification["thresholds"].items():
            for threshold, window, stop_set in itertools.product(
                    thresholds, specification["windows"],
                    specification["stop_sets"]):
                selected, stopped = decision(run["trace"], method, stop_set,
                                             threshold, window)
                rows.append({
                    "task":
                        run["task"],
                    "dataset":
                        run["dataset"]["name"],
                    "variant":
                        cfg["variant"],
                    "seed":
                        cfg["seed"],
                    "query":
                        cfg["query"],
                    "noise":
                        cfg["noise"],
                    "method":
                        method,
                    "threshold":
                        threshold,
                    "window":
                        window,
                    "stop_set":
                        stop_set,
                    "stopped":
                        stopped,
                    "labels":
                        selected["labels"],
                    "macro_f1":
                        selected["macro_f1"],
                    "positive_f1":
                        selected["positive_f1"],
                    "label_savings":
                        1 - selected["labels"] / cfg["budget"],
                    "f1_gap_to_peak":
                        run["retrospective"]["peak_macro_f1"] -
                        selected["macro_f1"],
                })
    output.mkdir(parents=True, exist_ok=True)
    report.write_csv(output / "sensitivity.csv", rows)
    (output / "replay-manifest.json").write_text(json.dumps(
        {
            "source_manifest":
                validation["manifest_id"],
            "grid":
                specification,
            "decisions":
                len(rows),
            "trajectories":
                len(runs),
            "interpretation":
                "Exploratory paired counterfactuals; no threshold selection on test labels.",
        },
        indent=2) + "\n",
                                                 encoding="utf-8")
    return {"trajectories": len(runs), "replayed_decisions": len(rows)}
