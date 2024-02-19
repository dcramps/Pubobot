import pytest

import discord
import discord.ext.test as dpytest


@pytest.mark.asyncio(scope="session")
async def test_enable_pickups(bot, helper):
    await dpytest.message("!enable_pickups", member=0)

    resp = await helper.message()
    assert "You must have permission" in resp.content

    # Grant member 0 all permissions so they may enable pickups
    perms = discord.PermissionOverwrite.from_pair(
        discord.Permissions.all(), discord.Permissions.none()
    )

    await dpytest.set_permission_overrides(0, 0, perms)

    await dpytest.message("!enable_pickups", member=0)
    resp = await helper.message()
    assert "Pickups enabled" in resp.content


@pytest.mark.asyncio(scope="session")
async def test_add_pickup(bot, helper):
    await dpytest.message("!add_pickups elim:8", member=0)
    resp = await helper.message()
    assert "**elim** (0/8)" in resp.content

    settings = [
        ("pick_captains", "2"),
        ("pick_teams", "manual"),
        ("pick_order", "abbaab"),
    ]

    for k, v in settings:
        await dpytest.message(f"!set_pickups elim {k} {v}", member=0)
        resp = await helper.message()
        assert f"Set '{v}' {k}" in resp.content


@pytest.mark.asyncio(scope="session")
async def test_pickup_game(bot, helper):
    size = 8
    cfg = dpytest.get_config()

    # Simulate joining by members
    for m in range(size):
        await dpytest.message("!j elim", member=m)

        if m == size - 2:
            resp = await helper.message()
            assert "Only 1 player left" in resp.content

        if m < size - 1:
            resp = await helper.message()
            assert f"**elim** ({m+1}/8)" in resp.content

    # Verify DMs were sent to members
    for m in range(size):
        resp = await helper.message()
        assert "pickup has been started" in resp.content
        assert isinstance(resp.channel, discord.DMChannel)
        assert resp.channel.recipient == cfg.members[m]

    resp = await helper.message()
    assert "[**no pickups**]" in resp.content

    # TODO: Match content against a regular expression to extract random
    # captains and simulate team picking
    resp = await helper.message()
    assert "please start picking teams" in resp.content
