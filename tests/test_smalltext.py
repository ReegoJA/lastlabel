"""Verify small-text orchestration and document stopping-rule boundaries."""

import numpy as np
import pytest
from scipy import sparse
from small_text import PoolBasedActiveLearner
from small_text.stopping_criteria import DeltaFScore, KappaAverage

from stoplab import data, experiment, learners, rules


@pytest.mark.parametrize("model", ["logistic", "linear-svm"])
@pytest.mark.parametrize("policy", ["random", "uncertainty"])
@pytest.mark.parametrize("sparse_input", [False, True])
def test_smalltext_matches_direct_training(model, policy, sparse_input):
    dataset = data.load({
        "name": "check",
        "kind": "synthetic",
        "samples": 120
    }, 2, "")
    x = sparse.csr_matrix(dataset.pool_x) if sparse_input else dataset.pool_x
    cfg = experiment.Config(seed=3, learner=model, query=policy)
    indices = np.arange(20)
    labels = dataset.pool_y[indices]
    rng = np.random.default_rng(13)
    reference_rng = np.random.default_rng(13)
    active = learners.initialize(x, indices, labels, cfg, rng)
    assert isinstance(active, PoolBasedActiveLearner)
    assert np.all(active.dataset.y == -1)
    for _ in range(3):
        direct = learners.create(model, cfg.seed)
        direct.fit(x[indices], labels)
        np.testing.assert_allclose(active.classifier.model.decision_function(x),
                                   direct.decision_function(x),
                                   atol=1e-12)
        available = np.setdiff1d(np.arange(x.shape[0]), indices)
        expected = experiment.choose_batch(direct.decision_function(x),
                                           available, 7, policy, reference_rng)
        selected = active.query(num_samples=7)
        np.testing.assert_array_equal(selected, expected)
        new_labels = 1 - dataset.pool_y[selected]
        active.update(new_labels)
        indices = np.concatenate([indices, selected])
        labels = np.concatenate([labels, new_labels])
        np.testing.assert_array_equal(active.y, labels)
        np.testing.assert_array_equal(active.indices_labeled, indices)
        assert np.all(active.dataset.y == -1)


@pytest.mark.parametrize("method,threshold", [("sp", .99), ("pcf", .01)])
def test_fixed_set_stopping_matches_smalltext(method, threshold):
    native = rules.StopRule(method, threshold, 3)
    upstream = (KappaAverage(2, window_size=3, kappa=threshold) if method
                == "sp" else DeltaFScore(2, window_size=3, threshold=threshold))
    predictions = [np.array([0, 0, 1, 1]), np.array([0, 1, 1, 1])]
    predictions += [predictions[-1].copy() for _ in range(4)]
    previous = None
    for current in predictions:
        statistic = None if previous is None else rules.agreement(
            previous, current)["kappa" if method == "sp" else "pcf"]
        assert native.update(statistic) == upstream.stop(predictions=current)
        previous = current


def test_kappa_threshold_boundary_is_intentionally_strict():
    previous = np.array([0, 0, 1, 1])
    current = np.array([0, 1, 0, 1])
    upstream = KappaAverage(2, window_size=1, kappa=0)
    assert not upstream.stop(predictions=previous)
    assert upstream.stop(predictions=current)
    assert not rules.StopRule("sp", 0, 1).update(
        rules.agreement(previous, current)["kappa"])


def test_constant_predictions_do_not_supply_defined_kappa():
    current = np.zeros(4, dtype=int)
    upstream = KappaAverage(2, window_size=1)
    upstream.stop(predictions=current)
    assert upstream.stop(predictions=current)
    assert rules.agreement(current, current) == {"kappa": None, "pcf": None}
    assert not rules.StopRule("sp", .99, 1).update(None)
    delta = DeltaFScore(2, window_size=1)
    delta.stop(predictions=current)
    with np.errstate(invalid="ignore"):
        assert not delta.stop(predictions=current)
