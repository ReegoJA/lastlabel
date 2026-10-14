"""Paired active-learning trajectories with isolated retrospective evaluation."""

import dataclasses
import hashlib
import time
import warnings

import numpy as np
from sklearn import exceptions
from sklearn import metrics

from stoplab import data
from stoplab import learners
from stoplab import noise
from stoplab import rules


@dataclasses.dataclass(frozen=True)
class Config:
    """Parameters fixed before test evaluation; budgets count all queried labels."""

    seed: int = 0
    variant: str = "baseline"
    learner: str = "logistic"
    noise_model: str = "symmetric"
    query: str = "uncertainty"
    noise: float = 0.0
    initial: int = 40
    batch: int = 20
    budget: int = 400
    stop_size: int = 400
    kappa: float = 0.99
    pcf: float = 0.01
    confidence: float = 0.95
    window: int = 3
    tolerance: float = 0.01

    def validate(self, pool_size: int):
        """Reject configurations that cannot produce a valid trajectory."""
        if self.query not in {"uncertainty", "random"}:
            raise ValueError("Query must be uncertainty or random.")
        if not 0 <= self.noise < 0.5 or not 0 <= self.tolerance <= 1:
            raise ValueError("Noise must be in [0, .5); tolerance in [0, 1].")
        if not 2 <= self.initial < self.budget <= pool_size:
            raise ValueError("Require 2 <= initial < budget <= pool size.")
        if self.batch < 1 or not 2 <= self.stop_size <= pool_size:
            raise ValueError("Invalid batch or stop-set size.")


choose_batch = learners.choose_batch


def evaluate(scores: np.ndarray, labels: np.ndarray) -> dict:
    """Compute held-out metrics after acquisition and stopping decisions."""
    predictions = (scores >= 0).astype(int)
    return {
        "macro_f1":
            float(
                metrics.f1_score(labels,
                                 predictions,
                                 average="macro",
                                 zero_division=0)),
        "positive_f1":
            float(metrics.f1_score(labels, predictions, zero_division=0)),
        "auc":
            float(metrics.roc_auc_score(labels, scores)),
    }


def run(dataset: data.Dataset, config: Config) -> dict:
    """Run once to budget and replay all criteria on the same training history.

    Fixed stop sets may overlap queried examples, as in the original SP
    protocol. Moving stop-set comparisons index both models on current U.
    """
    config.validate(len(dataset.pool_y))
    start = time.perf_counter()
    seed_rng, noise_rng, query_rng, stop_rng = [
        np.random.default_rng(child)
        for child in np.random.SeedSequence(config.seed).spawn(4)
    ]
    oracle, flips = noise.corrupt(dataset.pool_y, config.noise,
                                  config.noise_model, noise_rng)
    order = seed_rng.permutation(len(oracle))
    labeled = order[:config.initial].tolist()
    cursor = config.initial
    while len(np.unique(oracle[labeled])) < 2 and cursor < config.budget:
        labeled.append(int(order[cursor]))
        cursor += 1
    if len(np.unique(oracle[labeled])) < 2:
        raise ValueError(
            "Initial acquisition exhausted budget without two classes.")
    fixed = stop_rng.choice(len(oracle), config.stop_size, replace=False)
    easy = None
    previous = None
    traces = []
    test_scores = []
    decisions = {}
    methods = {
        "sp": config.kappa,
        "pcf": config.pcf,
        "confidence": config.confidence
    }
    stop_rules = {
        f"{method}:{stop_set}": rules.StopRule(method, threshold, config.window)
        for method, threshold in methods.items()
        for stop_set in ("fixed", "remaining", "easy")
    }
    with warnings.catch_warnings():
        warnings.simplefilter("error", exceptions.ConvergenceWarning)
        active = learners.initialize(dataset.pool_x, labeled, oracle[labeled],
                                     config, query_rng)
    while True:
        model = active.classifier.model
        scores = model.decision_function(dataset.pool_x)
        predictions = (scores >= 0).astype(int)
        if easy is None:
            easy = np.argsort(-np.abs(scores), kind="stable")[:config.stop_size]
        mask = np.ones(len(oracle), dtype=bool)
        mask[labeled] = False
        available = np.flatnonzero(mask)
        sets = {"fixed": fixed, "remaining": available, "easy": easy}
        statistics = {}
        probabilities = model.predict_proba(dataset.pool_x).max(axis=1)
        for stop_set, indices in sets.items():
            stats = {"kappa": None, "pcf": None}
            if previous is not None:
                stats = rules.agreement(previous[indices], predictions[indices])
            stats["confidence"] = float(
                probabilities[indices].mean()) if len(indices) else None
            stats["size"] = len(indices)
            stats["queried_overlap"] = int(np.isin(indices, labeled).sum())
            statistics[stop_set] = stats
            for method in methods:
                key = f"{method}:{stop_set}"
                value = stats["kappa" if method == "sp" else method]
                if stop_rules[key].update(value) and key not in decisions:
                    decisions[key] = len(traces)
        record = {
            "labels":
                len(labeled),
            "statistics":
                statistics,
            "queried_indices":
                labeled.copy(),
            "training_index_hash":
                hashlib.sha256(np.asarray(labeled, dtype=np.int64).tobytes()
                              ).hexdigest(),
        }
        traces.append(record)
        test_scores.append(model.decision_function(dataset.test_x))
        if len(labeled) >= config.budget:
            break
        chosen = active.query(num_samples=min(config.batch, config.budget -
                                              len(labeled)))
        with warnings.catch_warnings():
            warnings.simplefilter("error", exceptions.ConvergenceWarning)
            active.update(oracle[chosen])
        labeled = active.indices_labeled.tolist()
        previous = predictions
    for record, scores in zip(traces, test_scores):
        record.update(evaluate(scores, dataset.test_y))
    peak = max(row["macro_f1"] for row in traces)
    target = peak - config.tolerance
    reference = next(
        row["labels"] for row in traces if row["macro_f1"] >= target)
    outcomes = []
    for key in [*stop_rules, "budget:all"]:
        stopped = key in decisions
        row = traces[decisions[key] if stopped else -1]
        outcomes.append({
            "rule": key,
            "stopped": stopped,
            "labels": row["labels"],
            "macro_f1": row["macro_f1"],
            "positive_f1": row["positive_f1"],
            "auc": row["auc"],
            "f1_gap_to_peak": peak - row["macro_f1"],
            "label_savings": 1 - row["labels"] / traces[-1]["labels"],
            "premature": row["macro_f1"] < target,
            "excess_labels": max(0, row["labels"] - reference),
        })
    return {
        "config": dataclasses.asdict(config),
        "dataset": dataset.metadata,
        "trace": traces,
        "outcomes": outcomes,
        "retrospective": {
            "peak_macro_f1": peak,
            "earliest_near_peak_labels": reference
        },
        "noise_fraction_realized": float(flips.mean()),
        "noise_fraction_queried": float(flips[labeled].mean()),
        "fixed_stop_indices": fixed.tolist(),
        "easy_stop_indices": easy.tolist(),
        "wall_seconds": time.perf_counter() - start,
    }
