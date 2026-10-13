"""Seeded annotation-oracle corruption; evaluation labels stay untouched."""

import numpy as np


def corrupt(labels: np.ndarray, rate: float, mode: str,
            rng: np.random.Generator) -> tuple:
    """Flip labels independently at a conditional rate in eligible classes.

    Positive-only and negative-only rates are conditional on the clean class,
    so their overall flip fractions need not equal the symmetric rate.
    """
    if mode not in {"symmetric", "positive-only", "negative-only"}:
        raise ValueError("Unknown annotation noise model.")
    eligible = np.ones(len(labels), dtype=bool)
    if mode == "positive-only":
        eligible = labels == 1
    elif mode == "negative-only":
        eligible = labels == 0
    flips = (rng.random(len(labels)) < rate) & eligible
    observed = labels.copy()
    observed[flips] = 1 - observed[flips]
    return observed, flips
