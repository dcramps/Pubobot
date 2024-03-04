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

    for player in ctf_players[:-1]:
        await pbot.send_message("!j ctf", player)

    # 1 message per join, 1 message per "only 1 player needed" message
    for _ in range(18):
        await pbot.get_message()

    await pbot.send_message("!who", pbot.admin)

    # Output format should be sane
    async with pbot.message() as msg:
        assert (
            match := simple_match(
                "[**{elim_game}** ({elim_current}/{elim_total})] {elim_list}\n[**{ctf_game}** ({ctf_current}/{ctf_total})] {ctf_list}",
                msg.content,
            )
        )
        assert match["elim_game"] == "elim"
        assert match["elim_current"] == "7"
        assert match["elim_total"] == "8"
        assert match["ctf_game"] == "ctf"
        assert match["ctf_current"] == "9"
        assert match["ctf_total"] == "10"
        # Don't really care to match["elim_list"] or match["ctf_list"] since that's tested by memberformattertests
