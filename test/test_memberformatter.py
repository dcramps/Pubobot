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
        member.mention = f"<@!{i}>"
        members.append(member)
    return members

@pytest.fixture
def members_list(mocked_members: List[discord.Member]) -> List[discord.Member]:
    for index, member in enumerate(mocked_members):
        member.nick = f"dc{index}"
    return mocked_members

@pytest.fixture
def dumb_nicknames(mocked_members: List[discord.Member]) -> List[discord.Member]:
    for index, member in enumerate(mocked_members):
        member.nick = f"d`c{index}"
    return mocked_members

@pytest.fixture
def non_unique_members_list() -> List[discord.Member]:
    members = []
    for i in range(4):
        member = MagicMock(spec=discord.Member)
        member.id = i
        member.name = "dc3k"
        member.nick = "dc"
        member.mention = "<@!0>"
        members.append(member)
    return members

@pytest.fixture
def members_with_decorations(members_list) -> List[Tuple[discord.Member, List[str]]]:
    members = []
    decorations = ["[A+]", ":nomic:"]
    for member in members_list:
        tuple = (member, decorations)
        members.append(tuple)

    return members

## Tests

def test_format_list_uses_nicknames(members_with_decorations):
    print(members_with_decorations)
    assert(pubobot.memberformatter.format_list(members_with_decorations, True) == "dc0, dc1, dc2, dc3")

# def test_format_list_escapes_backticks(dumb_nicknames: List[discord.Member]):
#     assert(pubobot.memberformatter.format_list(dumb_nicknames, None, False) == "d\\`c0, d\\`c1, d\\`c2, d\\`c3")

# def test_format_list_mentions(members_list: List[discord.Member]):
#     assert(pubobot.memberformatter.format_list(members_list, None, True) == "<@!0>, <@!1>, <@!2>, <@!3>")

# def test_format_team(members_list: List[discord.Member]):
#     assert(pubobot.memberformatter.format_team(":ut_red:", members_list, None, False) == ":ut_red: dc0, dc1, dc2, dc3")

# def test_format_team_mentions(members_list: List[discord.Member]):
#     assert(pubobot.memberformatter.format_team(":ut_red:", members_list, None, True) == ":ut_red: <@!0>, <@!1>, <@!2>, <@!3>")

# def test_format_unpicked_pool(non_unique_members_list: List[discord.Member]):
#     import pubobot.bot
#     unpicked = pubobot.bot.UnpickedPool(non_unique_members_list).all
#     assert(pubobot.memberformatter.format_unpicked("Unpicked:", unpicked) == "Unpicked: 1. dc, 2. dc, 3. dc, 4. dc")

# def test_ranked(members_list: List[discord.Member], ranked_members: Dict[int, str]):
#     assert(pubobot.memberformatter.format_list(members_list, ranked_members, False) == "[A+] dc0, [A+] dc1, [A+] dc2, [A+] dc3")