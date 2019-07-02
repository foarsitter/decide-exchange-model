import pytest


def test_float_range():
    from decide.cli import float_range

    xrange = list(float_range(0, 0.20, 0.05))

    assert sum([0.0, 0.05, 0.10, 0.15, 0.20]) == sum(xrange)

    assert 0 == sum(float_range(0, 0, 0))

    values = list(float_range(0.05, 0.1, 0.05))

    assert 0.15 == round(sum(values), 2), sum(values)

    assert 0 == sum(float_range(0, 0, 0.10))

    assert 0 == sum(float_range(0, 1, 0.0))

    with pytest.raises(RuntimeError):
        assert 0 == sum(float_range(0, 100, 0.00005)), "Should trigger RuntimeError"

    assert 0 == sum(float_range(0, 1, 0.0))
