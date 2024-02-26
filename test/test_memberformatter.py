import discord
import pytest
import pubobot.memberformatter
# import pubobot.bot
from typing import List, Tuple
from unittest.mock import MagicMock

## Fixtures

@pytest.fixture
def mocked_members() -> List[discord.Member]:
    members = []
    for i in range(4):
        member = MagicMock(spec=discord.Member)
        member.id = i
        member.name = f"dc{i}k"
        member.nick = f"dc{i}"
        member.mention = f"<@{i}>"
        members.append(member)
    return members

@pytest.fixture
def members_with_normal_nicknames(mocked_members: List[discord.Member]) -> List[Tuple[discord.Member, List[str]]]:
    normal_nicknames = []
    for index, member in enumerate(mocked_members):
        normal_nicknames.append((member, None))
    return normal_nicknames

@pytest.fixture
def members_with_dumb_nicknames(mocked_members: List[discord.Member]) -> List[Tuple[discord.Member, List[str]]]:
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
    expected = "dc0 [[A+], :nomic:], dc1 [[A+], :nomic:], dc2 [[A+], :nomic:], dc3 [[A+], :nomic:]"
    actual = pubobot.memberformatter.format_list_tuples(members_with_decorations, False)
    assert(expected == actual)

def test_format_list_escapes_backticks(members_with_dumb_nicknames):
    expected = "d\\`c0, d\\`c1, d\\`c2, d\\`c3"
    actual = pubobot.memberformatter.format_list_tuples(members_with_dumb_nicknames, False)
    assert(expected == actual)

def test_format_list_mentions(members_with_normal_nicknames):
    expected = "<@0>, <@1>, <@2>, <@3>"
    actual = pubobot.memberformatter.format_list_tuples(members_with_normal_nicknames, True)
    assert(expected == actual)

# def test_format_unpicked_pool(members_with_normal_nicknames):
#     import pubobot.bot
#     unpicked = pubobot.bot.UnpickedPool(members_with_normal_nicknames).all
#     assert(pubobot.memberformatter.format_unpicked("Unpicked:", unpicked) == "Unpicked: 1. dc, 2. dc, 3. dc, 4. dc")