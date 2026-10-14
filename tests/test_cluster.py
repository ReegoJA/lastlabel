"""Check expanded matrix pairing and scheduler task coverage."""

import argparse
import dataclasses
import importlib.util
import json
import pathlib

import pytest

from stoplab import cli
from stoplab import replay
from stoplab import report

ROOT = pathlib.Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("filename,count", [("cluster.json", 8640),
                                            ("cluster-ablations.json", 4800),
                                            ("cluster-budget.json", 1920)])
def test_matrix_references_and_pairing(filename, count):
    spec, tasks = cli.plan(ROOT / "configs" / filename)
    assert len(tasks) == count
    assert not set(spec["seeds"]) & {0, 1, 2}
    variants = {row["name"]: row for row in spec["variants"]}
    for variant in variants.values():
        reference = variants[variant["reference"]]
        assert reference["learner"] == variant["learner"]
    for _, config in tasks:
        config.validate(842)


def test_variant_effect_uses_same_learner():
    rows = [
        dict(dataset="d",
             query="random",
             noise=.15,
             rule="sp:fixed",
             seed=0,
             variant=name,
             macro_f1=value,
             labels=100)
        for name, value in [("logistic", .2), ("svm", .8), ("svm-noise", .7)]
    ]
    pairs = report.variant_comparisons(rows, {
        "logistic": "logistic",
        "svm": "svm",
        "svm-noise": "svm"
    })
    assert len(pairs) == 1
    assert pairs[0]["reference"] == "svm"
    assert pairs[0]["macro_f1_delta"] == pytest.approx(-.1)


def test_grouped_task_tail_and_audit(tmp_path):
    spec = {
        "datasets": [{
            "name": "small",
            "kind": "synthetic",
            "samples": 300
        }],
        "seeds": [0, 1, 2],
        "queries": ["random"],
        "noise_rates": [0],
        "variants": [{
            "name": "base",
            "reference": "base"
        }],
        "experiment": {
            "initial": 20,
            "budget": 40,
            "stop_size": 40
        }
    }
    path = tmp_path / "config.json"
    path.write_text(json.dumps(spec), encoding="utf-8")
    args = argparse.Namespace(config=path,
                              output=tmp_path / "runs",
                              cache=tmp_path / "data",
                              task=0,
                              task_count=2,
                              download=False)
    cli.execute(args)
    args.task = 2
    cli.execute(args)
    assert replay.audit(args.output)["complete"]
    assert len(list(args.output.glob("run-*.json"))) == 3


def test_array_chunks_cover_each_task_once():
    spec = importlib.util.spec_from_file_location("submit",
                                                  ROOT / "cluster/submit.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for total in [1, 999, 8640]:
        indices = []
        for offset, count in module.chunks(total, 10, 500):
            assert count <= 500
            for index in range(count):
                start = offset + index * 10
                indices.extend(range(start, min(start + 10, total)))
        assert indices == list(range(total))
