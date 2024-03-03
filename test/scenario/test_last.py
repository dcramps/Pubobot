import pytest

import discord

from collections import deque
from matcher import PickStageMatcher

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

    # Simulate join by each player
    for i, player in enumerate(players, 1):
        async with pbot.interact("!j elim", player) as msg:
            if i == pickup.players - 1:
                assert "Only 1 player left" in msg.content

            elif i < pickup.players:
                assert f"**elim** ({i}/{pickup.players})" in msg.content

    # Verify DMs were sent to players
    for player in players:
        async with pbot.message() as msg:
            assert "pickup has been started" in msg.content
            assert isinstance(msg.channel, discord.DMChannel)
            assert msg.channel.recipient.id == player.id

    async with pbot.message() as msg:
        assert "[**no pickups**]" in msg.content

    matcher = PickStageMatcher()

    async with pbot.message() as msg:
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

    await pbot.send_message("!last", pbot.admin)
    await pbot.get_message()

    #TODO: Figure out a regex to match the last format
    # Match {n} [{game}]: {time} ago\n{alpha_team}\n{beta_team}