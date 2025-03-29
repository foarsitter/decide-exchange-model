import pytest


def test_float_range() -> None:
    from decide.cli import float_range

    xrange = list(float_range(0, 0.20, 0.05))

    assert sum([0.0, 0.05, 0.10, 0.15, 0.20]) == sum(xrange)

    assert sum(float_range(0, 0, 0)) == 0

    values = list(float_range(0.05, 0.1, 0.05))

    assert round(sum(values), 2) == 0.15, sum(values)

    assert sum(float_range(0, 0, 0.10)) == 0

    assert sum(float_range(0, 1, 0.0)) == 0

    with pytest.raises(RuntimeError):
        assert sum(float_range(0, 100, 0.00005)) == 0, "Should trigger RuntimeError"

    assert sum(float_range(0, 1, 0.0)) == 0
