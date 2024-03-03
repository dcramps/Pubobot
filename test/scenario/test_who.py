import pytest
import asyncio

import discord
from matcher import simple_match

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.scenario(guild="Example", channel="General", members=10),
]


async def test_who(pbot, pickup_factory):
    elim_config = {
        "pick_captains": "2",
        "pick_teams": "manual",
        "pick_order": "abbaab",
        "require_ready": "60s",
        "ready_expire": "5m",
    }

    ctf_config = {
        "pick_captains": "2",
        "pick_teams": "manual",
        "pick_order": "abbaabba",
        "require_ready": "60s",
        "ready_expire": "5m",
    }

    elim = await pickup_factory.create("elim", 8, elim_config)
    ctf = await pickup_factory.create("ctf", 10, ctf_config)

    elim_players = pbot.members[: elim.players]
    ctf_players = pbot.members[: ctf.players]

    for player in elim_players[:-1]:
        await pbot.send_message("!j elim", player)
        await pbot.get_message()

    await pbot.send_message("!who", pbot.admin)
    await pbot.get_message()

    # Output format should be sane
    async with pbot.message() as msg:
        assert (
            match := simple_match(
                "[**{game}** ({current}/{total})] {list}", msg.content
            )
        )
        assert match["game"] == "elim"
        assert match["current"] == "7"
        assert match["total"] == "8"
        # Don't really care to match["list"] since that's tested by memberformattertests

    for player in ctf_players[:-1]:
        await pbot.send_message("!j ctf", player)
        await pbot.get_message()

    await pbot.send_message("!who", pbot.admin)
    await pbot.get_message()

    # Use newlines for  readability
    async with pbot.message() as msg:
        assert "\n" in msg.content
