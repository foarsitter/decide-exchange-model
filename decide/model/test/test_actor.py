import pytest

from decide.model.base import Actor, Issue


def test_actor_functions():
    actor1 = Actor("Test")
    actor2 = Actor("Test")
    actor3 = Actor("Test 123")

    assert actor1.name == "Test"
    assert actor1.actor_id == "Test"
    assert actor2 == "Test"
    assert actor3.name == "Test 123"
    assert actor3.actor_id == "Test 123"
    assert str(actor3) == actor3.name

    # actor comparison happens on the key attribute. So the following is correct
    assert actor1 == actor1
    assert actor1 == actor2
    assert actor1 != actor3

    assert actor1 is not None

    # self.assertFalse(actor1 is None)
    with pytest.raises(NotImplementedError):
        assert actor1 == Issue("mock")

    # testing hash index functions
    store = {actor1: actor1, actor2: actor2, actor3: actor3}

    assert store[actor1] == actor1
    assert store[actor2] == actor1
    assert store[actor3] != actor1

    assert actor1 < actor3

    with pytest.raises(ValueError):
        assert actor1 < Issue("Mock")
