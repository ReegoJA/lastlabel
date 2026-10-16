"""Check trigger/fallback separation and seed-paired replay contrasts."""
import pytest
from stoplab.diagnostics import classify, failures, sensitivity


def test_event_and_gap_are_separate():
    base = dict(dataset='d', query='random', noise='0', variant='v', seed='1',
                labels='400', stopped='False', f1_gap_to_peak='.05')
    rows = [dict(base, rule='budget:all'), dict(base, rule='sp:fixed')]
    rows += [dict(base, rule='sp:easy', stopped='True', labels='100')]
    rows += [dict(base, rule='sp:remaining', stopped='True')]
    result = {r['rule']: r for r in failures(rows)}
    assert result['sp:fixed']['fallback_gap_count'] == 1
    assert result['sp:fixed']['early_trigger_gap_count'] == 0
    assert result['sp:fixed']['early_trigger_gap_rate_conditional'] is None
    assert result['sp:easy']['early_trigger_gap_count'] == 1
    assert result['sp:remaining']['budget_trigger_count'] == 1
    assert result['budget:all']['fixed_budget_count'] == 1


def test_invalid_fallback_and_duplicates_fail():
    with pytest.raises(ValueError, match="integers"):
        classify(dict(rule="sp:fixed", labels=100.5, stopped=True), 400)
    with pytest.raises(ValueError, match='final budget'):
        classify(dict(rule='sp:fixed', labels=100, stopped=False), 400)
    row = dict(dataset='d', query='random', noise='0', variant='v', seed='1',
               rule='sp:fixed', labels=400, stopped=False, f1_gap_to_peak=0)
    with pytest.raises(ValueError, match='Duplicate'):
        failures([row, row])
    with pytest.raises(ValueError, match='Missing'):
        failures([row])


def test_replay_pairs_seeds_before_intervals():
    rows=[]
    for seed, score in [('1', .3), ('2', .8)]:
        for threshold, delta in [(.99, 0), (.95, -.1)]:
            rows.append(dict(dataset='d', query='random', noise='0', variant='v',
                             seed=seed, method='sp', stop_set='fixed', window='3',
                             threshold=threshold, macro_f1=score + delta,
                             positive_f1=score - delta, labels=400 + 100 * delta,
                             stopped='True'))
    pairs=sensitivity(iter(reversed(rows)), ['v'], [0])
    changed=next(p for p in pairs if p['threshold']==.95)
    assert changed['seeds']==2
    assert changed['macro_f1_low']==pytest.approx(-.1)
    assert changed['macro_f1_high']==pytest.approx(-.1)
    assert changed['positive_f1_delta']==pytest.approx(.1)
    assert changed['labels_delta']==pytest.approx(-10)
    with pytest.raises(ValueError, match='Missing paired'):
        sensitivity([r for r in rows if r['threshold']==.95], ['v'], [0])
