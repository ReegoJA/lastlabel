"""Matched linear learners; all fitting uses queried labels only."""

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
