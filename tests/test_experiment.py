"""Protect label accounting, paired comparisons, and held-out isolation."""

import dataclasses

import numpy as np
import pytest

from stoplab import data
from stoplab import experiment


@pytest.fixture
def dataset():
    return data.load({
        "name": "test",
        "kind": "synthetic",
        "samples": 300
    }, 4, "")


@pytest.fixture
def config():
    return experiment.Config(seed=8,
                             initial=20,
                             batch=13,
                             budget=61,
                             stop_size=40)


def test_budget_unique_labels_and_aligned_remaining_set(dataset, config):
    result = experiment.run(dataset, config)
    assert [row["labels"] for row in result["trace"]] == [20, 33, 46, 59, 61]
    for row in result["trace"]:
        assert len(set(row["queried_indices"])) == row["labels"]
        assert row["statistics"]["remaining"]["size"] == len(
            dataset.pool_y) - row["labels"]
        assert row["statistics"]["remaining"]["queried_overlap"] == 0
        assert row["statistics"]["fixed"]["size"] == config.stop_size
    assert len(result["outcomes"]) == 10
    assert result["outcomes"][-1]["labels"] == config.budget
    assert not result["outcomes"][-1]["stopped"]


def test_test_labels_cannot_change_acquisition_or_stopping(dataset, config):
    original = experiment.run(dataset, config)
    altered = experiment.run(
        dataclasses.replace(dataset, test_y=1 - dataset.test_y), config)
    assert [row["statistics"] for row in original["trace"]
           ] == [row["statistics"] for row in altered["trace"]]
    assert [row["queried_indices"] for row in original["trace"]
           ] == [row["queried_indices"] for row in altered["trace"]]
    assert [(row["labels"], row["stopped"]) for row in original["outcomes"]
           ] == [(row["labels"], row["stopped"]) for row in altered["outcomes"]]
    assert original["trace"][-1]["macro_f1"] != altered["trace"][-1]["macro_f1"]


def test_repeatable_and_noise_paired_across_query_policies(dataset, config):
    config = dataclasses.replace(config, noise=0.15)
    first = experiment.run(dataset, config)
    repeated = experiment.run(dataset, config)
    assert first["trace"] == repeated["trace"]
    assert first["outcomes"] == repeated["outcomes"]
    random = experiment.run(dataset, dataclasses.replace(config,
                                                         query="random"))
    assert first["noise_fraction_realized"] == random["noise_fraction_realized"]
    assert first["trace"][0]["queried_indices"] == random["trace"][0][
        "queried_indices"]


def test_uncertainty_order_and_ties():
    chosen = experiment.choose_batch(np.array([0.5, -0.1, 0.1, 2]),
                                     np.array([3, 2, 1]), 2, "uncertainty",
                                     np.random.default_rng(0))
    assert chosen.tolist() == [1, 2]


def test_budget_fallback(dataset, config):
    result = experiment.run(dataset, dataclasses.replace(config, window=100))
    assert all(not row["stopped"] and row["labels"] == 61
               for row in result["outcomes"])


@pytest.mark.parametrize("changes", [{
    "noise": 0.5
}, {
    "budget": 500
}, {
    "batch": 0
}])
def test_invalid_configuration(dataset, config, changes):
    with pytest.raises(ValueError):
        experiment.run(dataset, dataclasses.replace(config, **changes))
