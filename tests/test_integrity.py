"""Reject inconsistent research artifacts before aggregation."""

import argparse
import json

import pytest

from stoplab import cli
from stoplab import replay
from stoplab import report


@pytest.fixture
def results(tmp_path):
    specification = {
        "datasets": [{
            "name": "small",
            "kind": "synthetic",
            "samples": 300
        }],
        "seeds": [0],
        "queries": ["random"],
        "noise_rates": [0],
        "experiment": {
            "initial": 20,
            "budget": 60,
            "batch": 20,
            "stop_size": 40
        },
    }
    config = tmp_path / "config.json"
    config.write_text(json.dumps(specification), encoding="utf-8")
    destination = tmp_path / "results"
    cli.execute(
        argparse.Namespace(config=config,
                           output=destination,
                           cache=tmp_path / "data",
                           task=None,
                           download=False))
    return destination


@pytest.mark.parametrize("metric", [
    "positive_f1", "auc", "label_savings", "premature", "excess_labels",
    "f1_gap_to_peak"
])
def test_report_rejects_modified_outcome(results, tmp_path, metric):
    path = results / "run-00000.json"
    run = json.loads(path.read_text(encoding="utf-8"))
    run["outcomes"][0][metric] = -1
    path.write_text(json.dumps(run), encoding="utf-8")
    with pytest.raises(ValueError, match="Saved outcome"):
        report.generate(results, tmp_path / "report")


def test_missing_outcome_rejected(results):
    path = results / "run-00000.json"
    run = json.loads(path.read_text(encoding="utf-8"))
    run["outcomes"].pop()
    path.write_text(json.dumps(run), encoding="utf-8")
    with pytest.raises(ValueError, match="Missing or duplicate"):
        replay.audit(results)


def test_manifest_mutation_rejected(results):
    path = results / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["expected_runs"] = 999
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="Manifest hash"):
        replay.audit(results)


def test_run_config_must_match_task(results):
    path = results / "run-00000.json"
    run = json.loads(path.read_text(encoding="utf-8"))
    run["config"]["seed"] = 900
    path.write_text(json.dumps(run), encoding="utf-8")
    with pytest.raises(ValueError, match="configuration"):
        replay.audit(results)


def test_partial_report_keeps_declared_reference(results, tmp_path,
                                                 monkeypatch):
    path = results / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["specification"]["variants"] = [{
        "name": "baseline"
    }, {
        "name": "other"
    }]
    run = json.loads((results / "run-00000.json").read_text(encoding="utf-8"))
    run["config"]["variant"] = "other"
    monkeypatch.setattr(replay, "audit", lambda _: {})
    monkeypatch.setattr(replay, "load_runs", lambda _: (manifest, [run]))
    references = []
    monkeypatch.setattr(
        report, "variant_comparisons",
        lambda rows, reference: references.append(reference) or [])
    report.generate(results, tmp_path / "report")
    assert references == ["baseline"]
