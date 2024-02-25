import pytest

from unittest.mock import patch

from pubobot.bot import Pickup


class FakeUser:
    def __init__(self, id: int):
        self.id = id


@pytest.fixture
def pickup():
    return Pickup(None, {"pickup_name": "dummy"})


@pytest.fixture
def time_mock():
    with patch("time.time") as m:
        m.return_value = 0
        yield m


def test_user_ready_expiration(pickup, time_mock):
    users = [FakeUser(i) for i in range(5)]

    pickup.mark_user_ready(users[0], users[1], users[3])

    # Get users ready in the last 60 seconds
    ready_users = pickup.get_ready_users([users[1], users[2], users[3]], 60)
    assert ready_users == [users[1], users[3]]

    # Advance time by 120 seconds and check again
    time_mock.return_value += 120

    ready_users = pickup.get_ready_users([users[1], users[2], users[3]], 60)
    assert ready_users == []


def test_unmark_user_ready(pickup):
    users = [FakeUser(i) for i in range(5)]

    pickup.mark_user_ready(users[0], users[1], users[2])
    assert pickup.get_ready_users(users, 60) == [users[0], users[1], users[2]]

    pickup.unmark_user_ready(users[1], users[2], users[4])
    assert pickup.get_ready_users(users, 60) == [users[0]]
