"""Matched linear learners; all fitting uses queried labels only."""

import numpy as np

from small_text import PoolBasedActiveLearner, SklearnDataset
from small_text.classifiers import SklearnClassifierFactory
from small_text.query_strategies import QueryStrategy

from sklearn import linear_model
from sklearn import svm


def create(name: str, seed: int):
    """Construct a fresh learner with fixed, untuned hyperparameters.

    SVC's internal probability calibration uses training labels only.
    Acquisition and class prediction use its decision margin; confidence
    is an auxiliary probability-based heuristic, not a correctness bound.
    """
    if name == "logistic":
        return linear_model.LogisticRegression(C=1.0,
                                               solver="liblinear",
                                               max_iter=2000,
                                               random_state=seed)
    if name == "linear-svm":
        return svm.SVC(C=1.0,
                       kernel="linear",
                       probability=True,
                       random_state=seed,
                       cache_size=256)
    raise ValueError("Learner must be logistic or linear-svm.")


def choose_batch(scores, available, size, query, rng):
    """Select by decision margin with index ties and an independent RNG."""
    if query == "random":
        return rng.choice(available, min(size, len(available)), replace=False)
    order = np.lexsort((available, np.abs(scores[available])))
    return available[order[:size]]


class PairedQuery(QueryStrategy):
    """Preserve the study's acquisition policy inside small-text."""

    def __init__(self, policy, rng):
        self.policy = policy
        self.rng = rng

    def query(self, clf, dataset, indices_unlabeled, indices_labeled, y, n=10):
        scores = (np.zeros(len(dataset)) if self.policy == "random" else
                  clf.model.decision_function(dataset.x))
        return choose_batch(scores, indices_unlabeled, n, self.policy, self.rng)


def initialize(features, indices, labels, config, rng):
    """Create an active learner without exposing unqueried oracle labels."""
    dataset = SklearnDataset(features,
                             np.full(features.shape[0], -1),
                             target_labels=np.array([0, 1]))
    factory = SklearnClassifierFactory(create(config.learner, config.seed), 2)
    active = PoolBasedActiveLearner(factory,
                                    PairedQuery(config.query, rng),
                                    dataset,
                                    reuse_model=False)
    active.initialize_data(np.asarray(indices, dtype=int), np.asarray(labels))
    return active
