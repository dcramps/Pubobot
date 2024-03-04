import pytest
from collections import deque

import discord

from matcher import PickStageMatcher, simple_match


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
    await pbot.send_message("!last", pbot.admin)
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
    assert match["alpha_team"] == " ".join(p.nick for p in alpha_team)
    assert match["beta_team"] == " ".join(p.nick for p in beta_team)
