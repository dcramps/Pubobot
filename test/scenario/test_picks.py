import pytest

import discord

from collections import deque

from matcher import PickStageMatcher


@pytest.mark.asyncio
@pytest.mark.scenario(guild="Example", channel="General", members=20)
@pytest.mark.pickup(
    name="elim",
    players=12,
    config={
        "pick_captains": "2",
        "pick_teams": "manual",
        "pick_order": "abbaabbaab",
    },
)
async def test_multi_pick(pbot, pickup):
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

    # Zero picks
    async with pbot.interact("!p", alpha_capt) as msg:
        assert "You must specify a player to pick!" in msg.content

    # Try to add a player not in the list by position
    async with pbot.interact("!p 20", alpha_capt) as msg:
        assert "Specified player are not in unpicked players list." in msg.content

    # Try to add a player not in the list by mention
    async with pbot.interact(f"!p <@{pbot.members[-1].id}>", alpha_capt) as msg:
        assert "Specified player are not in unpicked players list." in msg.content

    # Have alpha capt pick one
    num1, pick1 = unpicked.popleft()
    async with pbot.interact(f"!p {num1}", alpha_capt) as msg:
        alpha_team.append(pick1)

        match = matcher.match_turn(msg.content)
        assert match
        assert match.alpha_team == [p.nick for p in alpha_team]

    # Have a random player in the pug try to pick
    _, player = unpicked[0]
    num1, pick1 = unpicked[1]
    async with pbot.interact(f"!p {num1}", player) as msg:
        assert "You are not a captain." in msg.content

    # Have a non-pug player try to pick
    num1, pick1 = unpicked[0]
    async with pbot.interact(f"!p {num1}", pbot.members[-1]) as msg:
        assert "Could not find an active match." in msg.content

    # Beta capt picks two
    num1, pick1 = unpicked.popleft()
    num2, pick2 = unpicked.popleft()

    async with pbot.interact(f"!p <@{pick1.id}> {num2}", beta_capt) as msg:
        beta_team.append(pick1)
        beta_team.append(pick2)

        match = matcher.match_turn(msg.content)
        assert match
        assert match.beta_team == [p.nick for p in beta_team]

    # Sneaky beta capt tries to add another
    num1, pick1 = unpicked[0]
    async with pbot.interact(f"!p {num1}", beta_capt) as msg:
        assert "Not your turn to pick." in msg.content

    # Alpha capt picks three, only the first two should be added
    num1, pick1 = unpicked.popleft()
    num2, pick2 = unpicked.popleft()
    num3, _ = unpicked[0]

    async with pbot.interact(f"!p {num1} <@{pick2.id}> {num3}", alpha_capt) as msg:
        alpha_team.append(pick1)
        alpha_team.append(pick2)

        match = matcher.match_turn(msg.content)
        assert match
        assert match.alpha_team == [p.nick for p in alpha_team]
        assert match.beta_team == [p.nick for p in beta_team]

    # Beta capt picks two, but has duplicate picks
    num1, pick1 = unpicked.popleft()
    num2, pick2 = unpicked.popleft()

    async with pbot.interact(
        f"!p <@{pick1.id}> {num1} <@{pick2.id}> {num2}", beta_capt
    ) as msg:
        beta_team.append(pick1)
        beta_team.append(pick2)

        match = matcher.match_turn(msg.content)
        assert match
        assert match.alpha_team == [p.nick for p in alpha_team]
        assert match.beta_team == [p.nick for p in beta_team]

    # Alpha capt tries to pick more than what's left
    num1, pick1 = unpicked.popleft()
    num2, pick2 = unpicked.popleft()
    num3, pick3 = unpicked.popleft()
    num4, _ = num3, pick3

    async with pbot.interact(f"!p {num1} {num2} {num3} {num4}", alpha_capt) as msg:
        alpha_team.append(pick1)
        alpha_team.append(pick2)

        # Beta team should get the last player
        beta_team.append(pick3)

        match = matcher.match_ready(msg.content)
        assert match
        assert match.alpha_team == [p.id for p in alpha_team]
        assert match.beta_team == [p.id for p in beta_team]
