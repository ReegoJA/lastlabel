"""Check that convention replay isolates the intended boundary case."""

from stoplab.conventions import replay


def sample(values, sizes=None):
    sizes = sizes or [20] * len(values)
    return dict(config=dict(kappa=.99, window=3), trace=[
        dict(statistics=dict(fixed=dict(kappa=value, size=size)))
        for value, size in zip(values, sizes)])


def test_constant_predictions_change_only_the_alternative():
    run = sample([None, None, None, None, .5])
    assert replay(run, 'fixed') == (4, False)
    assert replay(run, 'fixed', True) == (3, True)


def test_initial_and_empty_sets_do_not_create_agreement():
    assert replay(sample([None, 1, 1]), 'fixed', True) == (2, False)
    assert replay(sample([None] * 4, [0] * 4), 'fixed', True) == (3, False)


def test_defined_values_preserve_strict_threshold():
    run = sample([None, .99, .99, .99])
    assert replay(run, 'fixed') == replay(run, 'fixed', True) == (3, False)
