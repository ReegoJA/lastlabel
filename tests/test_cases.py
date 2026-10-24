"""Check that descriptive cases follow the stated selection rule."""

import pytest
from stoplab.cases import select


def run(seed, gap, stopped=True):
    return dict(config=dict(seed=seed, variant='linear-svm-symmetric',
                            query='uncertainty', noise=.15, budget=400),
                dataset=dict(name='d'), trace=[], outcomes=[dict(rule='sp:easy',
                stopped=stopped, labels=200 if stopped else 400, f1_gap_to_peak=gap)])


def test_lower_median_excludes_fallbacks_when_early_triggers_exist():
    result = select([run(1, .1), run(2, .2), run(3, .3), run(4, 0, False)])
    assert result[0]['seed'] == 2
    assert result[0]['candidates'] == 3
    assert select([run(2, .1), run(1, .1)])[0]['seed'] == 1
    assert select([run(1, .2, False)])[0]['selection'] == 'all-run median'


def test_duplicate_case_seeds_fail():
    with pytest.raises(ValueError, match='Duplicate'):
        select([run(1, .1), run(1, .2)])
