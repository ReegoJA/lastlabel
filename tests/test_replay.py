"""Check annotation mechanisms and offline counterfactual stopping."""

import argparse
import json

import numpy as np
import pytest

from stoplab import cli
from stoplab import data
from stoplab import experiment
from stoplab import noise
from stoplab import replay


@pytest.mark.parametrize("mode,protected", [("positive-only", 0),
                                            ("negative-only", 1)])
def test_conditional_noise_never_flips_protected_class(mode, protected):
    labels = np.tile([0, 1], 1000)
    observed, flips = noise.corrupt(labels, 0.2, mode, np.random.default_rng(2))
    assert np.all(observed[labels == protected] == protected)
    assert 0.05 < flips.mean() < 0.15


def test_linear_svm_end_to_end():
    dataset = data.load({
        "name": "svm",
        "kind": "synthetic",
        "samples": 300
    }, 0, "")
    config = experiment.Config(learner="linear-svm",
                               initial=20,
                               budget=60,
                               stop_size=40,
                               noise_model="positive-only",
                               noise=0.1)
    result = experiment.run(dataset, config)
    assert result["trace"][-1]["labels"] == 60
    assert 0 <= result["trace"][-1]["macro_f1"] <= 1


def test_audit_replay_and_tamper_detection(tmp_path):
    config = tmp_path / "config.json"
    config.write_text(json.dumps({
        "datasets": [{
            "name": "small",
            "kind": "synthetic",
            "samples": 300
        }],
        "seeds": [0],
        "queries": ["random"],
        "noise_rates": [0],
        "variants": [{
            "name": "one",
            "learner": "logistic"
        }, {
            "name": "two",
            "learner": "linear-svm"
        }],
        "experiment": {
            "initial": 20,
            "batch": 20,
            "budget": 60,
            "stop_size": 40
        },
    }),
                      encoding="utf-8")
    results = tmp_path / "results"
    cli.execute(
        argparse.Namespace(config=config,
                           output=results,
                           task=None,
                           cache=tmp_path / "data",
                           download=False))
    assert replay.audit(results)["complete"]
    grid = tmp_path / "grid.json"
    grid.write_text(json.dumps({
        "thresholds": {
            "sp": [0.9, 0.99]
        },
        "windows": [1, 3],
        "stop_sets": ["fixed"]
    }),
                    encoding="utf-8")
    assert replay.generate(results, grid,
                           tmp_path / "replay")["replayed_decisions"] == 8
    path = results / "run-00000.json"
    run = json.loads(path.read_text(encoding="utf-8"))
    run["outcomes"][0]["labels"] = -1
    path.write_text(json.dumps(run), encoding="utf-8")
    with pytest.raises(ValueError, match="Saved outcome"):
        replay.audit(results)
