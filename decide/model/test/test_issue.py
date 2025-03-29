from unittest import TestCase

from decide.model.base import Issue


class TestIssue(TestCase):
    def test_normalization(self) -> None:
        # the normal case, works always
        x = Issue(name="test", lower=0, upper=100)

        assert x.step_size == 1
        assert x.de_normalize(50) == 50

        # case with a smaller delta
        y = Issue(name="test", lower=0, upper=60)

        assert y.step_size == 100 / 60
        self.assertAlmostEqual(y.de_normalize(50), 30, delta=0.00001)

        # case with a negative delta
        z = Issue(name="test", lower=0, upper=-60)

        assert z.step_size == 100 / -60
        self.assertAlmostEqual(z.de_normalize(50), -30, delta=1e-10)
        self.assertAlmostEqual(z.de_normalize(0), 0, delta=1e-10)
        self.assertAlmostEqual(z.de_normalize(100), -60, delta=1e-10)

        # case with a different starting position

        a = Issue(name="test", lower=10, upper=90)

        assert a.step_size == 100 / 80
        assert a.delta == 80
        assert a.de_normalize(50) == 50
        assert a.de_normalize(0) == 10

        # case with a different starting position and negative delta

        b = Issue(name="test", lower=-10, upper=-90)

        assert b.step_size == 100 / -80
        assert b.delta == -80
        assert b.de_normalize(50) == -50
        assert b.de_normalize(0) == -10

        # negative delta, positive lower point, negative upper

        c = Issue(name="test", lower=10, upper=-90)

        assert c.step_size == 100 / -100
        assert c.delta == -100
        assert c.de_normalize(50) == -40
        assert c.de_normalize(0) == 10

    def test___eq__(self) -> None:
        issue = Issue(name="test")
        issue2 = Issue(name="test")
        issue3 = Issue(name="test3")

        assert issue == issue
        assert issue == issue2
        assert issue != issue3
