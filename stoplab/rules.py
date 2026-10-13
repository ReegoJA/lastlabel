"""Label-free binary stopping rules with explicit degenerate-case handling."""

import dataclasses

import numpy as np


def agreement(previous: np.ndarray, current: np.ndarray) -> dict:
    """Return kappa and predicted F change for aligned binary predictions.

    Undefined kappa and all-negative predicted F change return None rather
    than manufacturing evidence for a stop. No true labels are accepted.
    """
    previous = np.asarray(previous)
    current = np.asarray(current)
    if previous.shape != current.shape or previous.ndim != 1:
        raise ValueError("Predictions must be aligned one-dimensional arrays.")
    if not np.isin(previous, [0, 1]).all() or not np.isin(current,
                                                          [0, 1]).all():
        raise ValueError(
            "Only binary predictions encoded as 0 and 1 are supported.")
    if not previous.size:
        return {"kappa": None, "pcf": None}
    observed = float(np.mean(previous == current))
    left = float(previous.mean())
    right = float(current.mean())
    expected = left * right + (1 - left) * (1 - right)
    kappa = (observed - expected) / (1 - expected) if expected < 1 else None
    both_positive = int(np.sum((previous == 1) & (current == 1)))
    changes = int(np.sum(previous != current))
    denominator = 2 * both_positive + changes
    pcf = changes / denominator if denominator else None
    return {"kappa": kappa, "pcf": pcf}


@dataclasses.dataclass
class StopRule:
    """Track a criterion using only prediction-derived scalar statistics.

    SP uses a mean over consecutive pair agreements. PCF requires every
    change estimate in the window to be below its threshold. Confidence is
    an explicitly heuristic baseline, not a reproduction of DC or NC.
    """

    method: str
    threshold: float
    window: int = 3
    history: list = dataclasses.field(default_factory=list)

    def __post_init__(self):
        if self.method not in {"sp", "pcf", "confidence"}:
            raise ValueError("Unknown stopping method.")
        if self.window < 1 or not 0 <= self.threshold <= 1:
            raise ValueError("Invalid stopping threshold or window.")

    def update(self, value: float | None) -> bool:
        """Consume one step and return whether the rule currently fires."""
        self.history.append(value)
        recent = self.history[-self.window:]
        if len(recent) < self.window:
            return False
        if any(item is None or not np.isfinite(item) for item in recent):
            return False
        if self.method == "pcf":
            return max(recent) < self.threshold
        return float(np.mean(recent)) > self.threshold
