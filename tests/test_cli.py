"""Exercise artifact provenance, resumption, and paired reports end to end."""

import argparse
import json

import pytest

from stoplab import cli
from stoplab import report


def test_run_resume_report_and_reject_changed_config(tmp_path):
    specification = {
        "datasets": [{
            "name": "small",
            "kind": "synthetic",
            "samples": 300
        }],
        "seeds": [0, 1],
        "queries": ["uncertainty"],
        "noise_rates": [0],
        "experiment": {
            "initial": 20,
            "batch": 20,
            "budget": 60,
            "stop_size": 40
        },
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(specification), encoding="utf-8")
    args = argparse.Namespace(config=config_path,
                              output=tmp_path / "results",
                              cache=tmp_path / "data",
                              task=None,
                              download=False)
    cli.execute(args)
    path = args.output / "run-00000.json"
    timestamp = path.stat().st_mtime_ns
    cli.execute(args)
    assert path.stat().st_mtime_ns == timestamp
    result = report.generate(args.output, tmp_path / "report")
    assert result["runs"] == result["expected"] == 2
    import csv
    with (tmp_path / "report" / "paired.csv").open() as stream:
        pairs = list(csv.DictReader(stream))
    for pair in pairs:
        differences = []
        for seed in (0, 1):
            run = json.loads((args.output / f"run-{seed:05d}.json").read_text())
            outcomes = {row["rule"]: row for row in run["outcomes"]}
            other = pair["comparison"].split()[0]
            differences.append(outcomes[f"{pair['method']}:{other}"]["positive_f1"] -
                               outcomes[f"{pair['method']}:fixed"]["positive_f1"])
        expected = report.interval(differences)
        assert [float(pair[key]) for key in
                ("positive_f1_delta", "positive_f1_low", "positive_f1_high")] == pytest.approx(expected)
    assert (tmp_path / "report" / "trajectory.svg").is_file()
    specification["noise_rates"] = [0.2]
    config_path.write_text(json.dumps(specification), encoding="utf-8")
    with pytest.raises(ValueError, match="different code/config/environment"):
        cli.execute(args)


def test_duplicate_tasks_rejected(tmp_path):
    path = tmp_path / "duplicate.json"
    path.write_text(json.dumps({
        "datasets": [{
            "name": "same"
        }],
        "seeds": [0, 0],
        "queries": ["random"],
        "noise_rates": [0],
        "experiment": {}
    }),
                    encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate"):
        cli.plan(path)


def test_bootstrap_unit_is_seed():
    assert report.interval([0.4]) == (0.4, None, None)
    mean, low, high = report.interval([0.2, 0.8])
    assert mean == 0.5
    assert 0.2 <= low <= mean <= high <= 0.8


def test_variant_contrasts_pair_with_matching_seed():
    rows = []
    for seed, base in [(0, 0.2), (1, 0.8)]:
        for variant, delta in [("control", 0), ("comparison", 0.1)]:
            rows.append(
                dict(dataset="d",
                     query="random",
                     noise=0,
                     rule="sp:fixed",
                     seed=seed,
                     variant=variant,
                     macro_f1=base + delta,
                     positive_f1=base - delta,
                     labels=100 + 10 * delta))
    result = report.variant_comparisons(rows, "control")[0]
    assert result["paired_seeds"] == 2
    assert result["macro_f1_delta"] == pytest.approx(0.1)
    assert result["macro_f1_low"] == pytest.approx(0.1)
    assert result["macro_f1_high"] == pytest.approx(0.1)

    assert result["positive_f1_delta"] == pytest.approx(-0.1)
    assert result["positive_f1_low"] == pytest.approx(-0.1)
    assert result["positive_f1_high"] == pytest.approx(-0.1)
