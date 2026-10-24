"""Verify paired differences of differences and incomplete-data rejection."""

import pytest

from stoplab.interactions import compare


def records():
    rows = []
    for seed, baseline in ((1, .4), (2, .8)):
        for noise in (0, .15):
            for method in ('sp', 'pcf'):
                for stop_set in ('fixed', 'easy', 'remaining'):
                    penalty = .1 if stop_set == 'easy' and noise else 0
                    rows.append(dict(dataset='d', query='q', variant='v', seed=seed,
                                     noise=noise, rule=f'{method}:{stop_set}',
                                     macro_f1=baseline - penalty,
                                     positive_f1=baseline - 2 * penalty,
                                     labels=400 - 100 * penalty))
    return rows


def test_noise_interaction_is_paired_before_resampling():
    result = compare(list(reversed(records())))
    for row in result:
        expected = -.1 if row['stop_set'] == 'easy' else 0
        assert row['macro_f1_interaction'] == pytest.approx(expected)
        assert row['macro_f1_low'] == pytest.approx(expected)
        assert row['macro_f1_high'] == pytest.approx(expected)
        assert row['positive_f1_interaction'] == pytest.approx(2 * expected)
        assert row['labels_interaction'] == pytest.approx(100 * expected)


def test_incomplete_and_duplicate_pairs_are_rejected():
    rows = records()
    with pytest.raises(ValueError, match='Duplicate'):
        compare(rows + [rows[0]])
    with pytest.raises(ValueError, match='Missing paired'):
        compare(rows[1:])
    with pytest.raises(ValueError, match='seed sets'):
        compare([r for r in rows if not (r['noise'] == 0 and r['seed'] == 1)])
