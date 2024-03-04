import discord
import pytest

from typing import List, Tuple, OrderedDict
from unittest.mock import MagicMock

from pubobot import memberformatter, bot

## Fixtures


@pytest.fixture
def mocked_members() -> List[discord.Member]:
    members = []
    for i in range(4):
        member = MagicMock(spec=discord.Member)
        member.id = i
        member.name = f"Member_name_{i}"
        member.nick = f"Member_nick_{i}"
        member.mention = f"<@{i}>"
        members.append(member)
    return members


@pytest.fixture
def members_with_normal_nicknames(
    mocked_members: List[discord.Member],
) -> List[Tuple[discord.Member, List[str]]]:
    normal_nicknames = []
    for index, member in enumerate(mocked_members):
        normal_nicknames.append((member, None))
    return normal_nicknames


@pytest.fixture
def members_with_dumb_nicknames(
    mocked_members: List[discord.Member],
) -> List[Tuple[discord.Member, List[str]]]:
    dumb_nicknames = []
    for index, member in enumerate(mocked_members):
        member.nick = f"d`c{index}"
        dumb_nicknames.append((member, None))
    return dumb_nicknames


@pytest.fixture
def members_with_decorations(mocked_members) -> List[Tuple[discord.Member, List[str]]]:
    members = []
    decorations = ["[A+]", ":nomic:"]
    for member in mocked_members:
        tuple = (member, decorations)
        members.append(tuple)

    return members


## Tests


def test_format_list_uses_nicknames(members_with_decorations):
    expected = "Member_nick_0 [[A+], :nomic:], Member_nick_1 [[A+], :nomic:], Member_nick_2 [[A+], :nomic:], Member_nick_3 [[A+], :nomic:]"
    actual = memberformatter.format_list_tuples(members_with_decorations, False)
    assert expected == actual


def test_format_list_escapes_backticks(members_with_dumb_nicknames):
    expected = "d\\`c0, d\\`c1, d\\`c2, d\\`c3"
    actual = memberformatter.format_list_tuples(members_with_dumb_nicknames, False)
    assert expected == actual


def test_format_list_mentions(members_with_normal_nicknames):
    expected = "<@0>, <@1>, <@2>, <@3>"
    actual = memberformatter.format_list_tuples(members_with_normal_nicknames, True)
    assert expected == actual


def test_format_unpicked_pool(mocked_members):
    unpicked_pool = bot.UnpickedPool(mocked_members).all.items()
    unpicked_pool_data = OrderedDict()

    for position, player in unpicked_pool:
        player.nick = f"{position}"
        unpicked_pool_data[position] = {"player": player}

    assert (
        memberformatter.format_unpicked(unpicked_pool_data) == "1. 1, 2. 2, 3. 3, 4. 4"
    )
