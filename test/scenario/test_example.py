import pytest

import discord
import discord.ext.test as dpytest

from collections import deque

from matcher import PickStageMatcher


@pytest.mark.asyncio(scope="session")
async def test_enable_pickups(pbot, messenger):
    await dpytest.message("!enable_pickups", member=0)

    message = await messenger.get_message()
    assert "You must have permission" in message.content

    # Grant member 0 all permissions so they may enable pickups
    perms = discord.PermissionOverwrite.from_pair(
        discord.Permissions.all(), discord.Permissions.none()
    )

    await dpytest.set_permission_overrides(0, 0, perms)

    await dpytest.message("!enable_pickups", member=0)
    message = await messenger.get_message()
    assert "Pickups enabled" in message.content


@pytest.mark.asyncio(scope="session")
async def test_add_pickup(pbot, messenger):
    await dpytest.message("!add_pickups elim:8", member=0)
    message = await messenger.get_message()
    assert "**elim** (0/8)" in message.content

    settings = [
        ("pick_captains", "2"),
        ("pick_teams", "manual"),
        ("pick_order", "abbaab"),
    ]

    for k, v in settings:
        await dpytest.message(f"!set_pickups elim {k} {v}", member=0)
        message = await messenger.get_message()
        assert f"Set '{v}' {k}" in message.content


@pytest.mark.asyncio(scope="session")
async def test_pickup_game(pbot, messenger):
    size = 8
    cfg = dpytest.get_config()

    # Simulate joining by members
    for m in range(size):
        await dpytest.message("!j elim", member=m)

        if m == size - 2:
            message = await messenger.get_message()
            assert "Only 1 player left" in message.content

        if m < size - 1:
            message = await messenger.get_message()
            assert f"**elim** ({m+1}/8)" in message.content

    # Verify DMs were sent to members
    for m in range(size):
        message = await messenger.get_message()
        assert "pickup has been started" in message.content
        assert isinstance(message.channel, discord.DMChannel)
        assert message.channel.recipient == cfg.members[m]

    message = await messenger.get_message()
    assert "[**no pickups**]" in message.content

    # Simulate picking
    matcher = PickStageMatcher()
    message = await messenger.get_message()
    match = matcher.match_start(message.content)

    assert len(match.unpicked) == size - 2

    alpha_capt = next(m for m in cfg.members if m.id == match.alpha_capt_id)
    beta_capt = next(m for m in cfg.members if m.id == match.beta_capt_id)

    unpicked = deque()
    for num, name in match.unpicked:
        for m in cfg.members:
            if m.display_name == name:
                unpicked.append((num, m))

    alpha_team = [alpha_capt]
    beta_team = [beta_capt]

    num, picked = unpicked.popleft()
    await dpytest.message(f"!p {num}", member=alpha_capt)
    message = await messenger.get_message()
    match = matcher.match_turn(message.content)
    alpha_team.append(picked)

    num, picked = unpicked.popleft()
    await dpytest.message(f"!p {num}", member=beta_capt)
    message = await messenger.get_message()
    match = matcher.match_turn(message.content)
    beta_team.append(picked)

    num, picked = unpicked.popleft()
    await dpytest.message(f"!p {num}", member=beta_capt)
    message = await messenger.get_message()
    match = matcher.match_turn(message.content)
    beta_team.append(picked)

    num, picked = unpicked.popleft()
    await dpytest.message(f"!p {num}", member=alpha_capt)
    message = await messenger.get_message()
    match = matcher.match_turn(message.content)
    alpha_team.append(picked)

    num, picked = unpicked.popleft()
    await dpytest.message(f"!p {num}", member=alpha_capt)
    message = await messenger.get_message()
    match = matcher.match_ready(message.content)
    alpha_team.append(picked)

    # Add last member to beta team
    _, picked = unpicked.popleft()
    beta_team.append(picked)

    actual_alpha_team = []
    for id in match.alpha_team:
        for m in cfg.members:
            if m.id == id:
                actual_alpha_team.append(m)

    actual_beta_team = []
    for id in match.beta_team:
        for m in cfg.members:
            if m.id == id:
                actual_beta_team.append(m)

    assert alpha_team == actual_alpha_team
    assert beta_team == actual_beta_team
