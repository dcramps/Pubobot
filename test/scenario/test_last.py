import pytest
from collections import deque

import discord

from matcher import PickStageMatcher, simple_match


async def simulate_pug(pbot, pickup):
    players = pbot.members[: pickup.players]

    for i, player in enumerate(players, 1):
        await pbot.send_message("!j elim", player)
        await pbot.get_message()

    for _ in range(pickup.players):
        await pbot.get_message()

    await pbot.get_message()

    matcher = PickStageMatcher()

    async with pbot.message() as msg:
        print(f"MESSAGE: {msg.content}")
        match = matcher.match_start(msg.content)
        assert len(match.unpicked) == len(players) - 2

    alpha_capt = next(p for p in players if p.id == match.alpha_capt_id)
    beta_capt = next(p for p in players if p.id == match.beta_capt_id)

    unpicked = deque()
    for num, name in match.unpicked:
        for p in players:
            if p.nick == name:
                unpicked.append((num, p))

    alpha_team = [alpha_capt]
    beta_team = [beta_capt]

    await pbot.send_message("!p 1", alpha_capt)
    await pbot.get_message()

    # Assign players to teams
    _, first_pick = unpicked.popleft()
    alpha_team.append(first_pick)
    _, last_pick = unpicked.popleft()
    beta_team.append(last_pick)

    return (alpha_team, beta_team)


@pytest.mark.asyncio
@pytest.mark.scenario(guild="Example", channel="General", members=20)
@pytest.mark.pickup(
    name="elim",
    players=4,
    config={
        "pick_captains": "2",
        "pick_teams": "manual",
        "pick_order": "ab",
    },
)
async def test_last(pbot, pickup):
    (alpha_team_1, beta_team_1) = await simulate_pug(pbot, pickup)

    await pbot.send_message("!last elim", pbot.admin)
    await pbot.get_message()
    msg = await pbot.get_message()
    match = simple_match(
        "**Match {n} [{game}]:** {time} ago\n{alpha_team}\n{beta_team}{_:$}",
        msg.content,
    )
    assert match
    assert match["n"] == "0"
    assert match["game"] == "elim"
    assert match["time"]  # Just check if it's non-empty
    assert match["alpha_team"] == " ".join(p.nick for p in alpha_team_1)
    assert match["beta_team"] == " ".join(p.nick for p in beta_team_1)

    (alpha_team_2, beta_team_2) = await simulate_pug(pbot, pickup)

    await pbot.send_message("!lastt elim", pbot.admin)
    await pbot.get_message()
    msg = await pbot.get_message()
    match = simple_match(
        "**Match {n} [{game}]:** {time} ago\n{alpha_team}\n{beta_team}{_:$}",
        msg.content,
    )

    # lastt should have the same data as the first pug, since it is now the oldest
    assert match
    assert match["n"] == "0"
    assert match["game"] == "elim"
    assert match["time"]  # Just check if it's non-empty
    assert match["alpha_team"] == " ".join(p.nick for p in alpha_team_1)
    assert match["beta_team"] == " ".join(p.nick for p in beta_team_1)

    # new last is match 1
    await pbot.send_message("!last", pbot.admin)
    msg = await pbot.get_message()
    match = simple_match(
        "**Match {n} [{game}]:** {time} ago\n{alpha_team}\n{beta_team}{_:$}",
        msg.content,
    )
    assert match
    assert match["n"] == "1"
    assert match["game"] == "elim"
    assert match["time"]  # Just check if it's non-empty
    assert match["alpha_team"] == " ".join(p.nick for p in alpha_team_2)
    assert match["beta_team"] == " ".join(p.nick for p in beta_team_2)

    # last by player name
    await pbot.send_message("!last ExampleUser2_2_nick", pbot.admin)
    msg = await pbot.get_message()
    match = simple_match(
        "**Match {n} [{game}]:** {time} ago\n{alpha_team}\n{beta_team}{_:$}",
        msg.content,
    )
    assert match
    assert match["n"] == "1"
    assert match["game"] == "elim"
    assert match["time"]  # Just check if it's non-empty
    assert match["alpha_team"] == " ".join(p.nick for p in alpha_team_2)
    assert match["beta_team"] == " ".join(p.nick for p in beta_team_2)

    # lasttt should give no data since there have only been two pugs
    await pbot.send_message("!lasttt", pbot.admin)
    msg = await pbot.get_message()
    assert msg.content == "No pickups found."
