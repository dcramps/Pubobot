import pytest
import asyncio

import discord.ext.test as dpytest


@pytest.mark.asyncio(scope="session")
async def test_bot(bot):
    await dpytest.message("!enable_pickups")
    await asyncio.sleep(0.1)
    assert dpytest.verify().message().contains().content("You must have permission")
