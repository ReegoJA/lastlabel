"""Check paper equations, window semantics, and undefined statistics."""

import numpy as np
import pytest

from stoplab import rules


def test_hand_calculated_agreement():
    result = rules.agreement(np.array([1, 1, 0, 0]), np.array([1, 0, 1, 0]))
    assert result == {"kappa": 0.0, "pcf": 0.5}
    result = rules.agreement(np.array([1, 1, 0, 0]), np.array([1, 1, 1, 0]))
    assert result["kappa"] == pytest.approx(0.5)
    assert result["pcf"] == pytest.approx(0.2)


@pytest.mark.parametrize("values", [[], [0, 0]])
def test_degenerate_predictions_abstain(values):
    assert rules.agreement(values, values) == {"kappa": None, "pcf": None}


def test_sp_averages_but_pcf_requires_every_pair():
    sp = rules.StopRule("sp", 0.9, 3)
    assert [sp.update(value) for value in [0.8, 0.99, 0.99]
           ] == [False, False, True]
    pcf = rules.StopRule("pcf", 0.1, 3)
    assert not any(pcf.update(value) for value in [0.2, 0.01, 0.01])
    assert pcf.update(0.01)


def test_strict_thresholds_and_missing_window():
    assert not rules.StopRule("sp", 0.9, 1).update(0.9)
    assert not rules.StopRule("pcf", 0.1, 1).update(0.1)
    rule = rules.StopRule("sp", 0.9, 3)
    assert not any(rule.update(value) for value in [1, None, 1, 1])
    assert rule.update(1)


@pytest.mark.parametrize("left,right", [([0], [0, 1]), ([2], [1]),
                                        ([[0]], [[0]])])
def test_invalid_predictions(left, right):
    with pytest.raises(ValueError):
        rules.agreement(left, right)
