import pytest

import discord
import discord.ext.test as dpytest


@pytest.mark.asyncio(scope="session")
async def test_enable_pickups(bot, messenger):
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
async def test_add_pickup(bot, messenger):
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
async def test_pickup_game(bot, messenger):
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

    # TODO: Match content against a regular expression to extract random
    # captains and simulate team picking
    message = await messenger.get_message()
    assert "please start picking teams" in message.content
