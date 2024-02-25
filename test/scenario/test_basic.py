import pytest

from collections import deque

import discord

from matcher import PickStageMatcher


@pytest.mark.asyncio
@pytest.mark.scenario(guild="Example", channel="General", members=10)
@pytest.mark.pickup(
    name="elim",
    players=8,
    config={
        "pick_captains": "2",
        "pick_teams": "manual",
        "pick_order": "abbaab",
    },
)
async def test_basic_scenario(pbot, pickup):
    members = pbot.members
    players = []

    # Select players to participate from member pool
    for i in range(pickup.players):
        players.append(members[i])

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

    turns = [
        (alpha_capt, alpha_team),
        (beta_capt, beta_team),
        (beta_capt, beta_team),
        (alpha_capt, alpha_team),
        (alpha_capt, alpha_team),
    ]

    ready_match = None

    for i, (capt, team) in enumerate(turns):
        num, picked = unpicked.popleft()
        async with pbot.interact(f"!p {num}", capt) as msg:
            if i < len(turns) - 1:
                assert matcher.match_turn(msg.content)
            else:
                ready_match = matcher.match_ready(msg.content)
                assert ready_match

            team.append(picked)

    async with pbot.message() as msg:
        assert "please connect to steam://connect//" in msg.content

    # Add last member to beta team
    _, picked = unpicked.popleft()
    beta_team.append(picked)

    assert ready_match

    actual_alpha_team = []
    for id in ready_match.alpha_team:
        for p in players:
            if p.id == id:
                actual_alpha_team.append(p)

    actual_beta_team = []
    for id in ready_match.beta_team:
        for p in players:
            if p.id == id:
                actual_beta_team.append(p)

    assert alpha_team == actual_alpha_team
    assert beta_team == actual_beta_team


@pytest.mark.asyncio
@pytest.mark.scenario
@pytest.mark.pickup(
    name="elim",
    players=4,
    config={
        "pick_captains": "2",
        "pick_teams": "manual",
        "pick_order": "abab",
    },
)
async def test_basic_scenario_2(pbot, pickup):
    members = pbot.members
    players = []

    # Select players to participate from member pool
    for i in range(pickup.players):
        players.append(members[i])

    # Simulate join by each player
    for i, player in enumerate(players, 1):
        async with pbot.interact("!j elim", player) as msg:
            if i == pickup.players - 1:
                assert "Only 1 player left" in msg.content

            elif i < pickup.players:
                assert f"**elim** ({i}/{pickup.players})" in msg.content
