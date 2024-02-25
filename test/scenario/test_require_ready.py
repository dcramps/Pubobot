import pytest
import asyncio

import discord

from matcher import PickStageMatcher, compile_simple_expression, simple_match


# Mark each test in this module
pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.scenario(guild="Example", channel="General", members=10),
    pytest.mark.pickup(
        name="elim",
        players=8,
        config={
            "pick_captains": "2",
            "pick_teams": "manual",
            "pick_order": "abbaab",
            "require_ready": "60s",
        },
    ),
]

id_pattern = compile_simple_expression("<@{id}>")

ready_message_pattern = compile_simple_expression(
    "__*({match_id})* **{game}** pickup is now on waiting ready state!__\r\n"
    "Waiting on: {waiting_list}.\r\n"
    "Please react with :ballot_box_with_check: to **check-in** or :no_entry: to **abort**!"
)

not_ready_message_pattern = compile_simple_expression(
    "**{user}** is not ready!\r\n" "Reverting **{game}** to gathering state..."
)


emoji_ready = "\u2611"
emoji_abort = "\u26d4"


async def test_require_ready_all_ready(pbot, pickup):
    players = pbot.members[: pickup.players]

    # Set up pug
    for player in players:
        await pbot.send_message("!j elim", player)
        await pbot.get_message()

    for _ in range(pickup.players):
        await pbot.get_message()

    await pbot.get_message()

    # Verify bot spits out a sentinel message, because reasons
    ready_msg = None
    async with pbot.message() as msg:
        match = simple_match("!spawn_message {match_id}", msg.content)
        assert match
        ready_msg = msg

    # Give the bot a bit of time to edit it's own message
    await asyncio.sleep(0.005)

    # Match ready string
    assert (match := ready_message_pattern.match(ready_msg.content))

    # Verify waiting on list only includes players that joined
    assert [p.id for p in players] == [
        int(x) for x in id_pattern.findall(match["waiting_list"])
    ]

    # React with ballot box with check mark
    for p in players:
        await pbot.react(p, ready_msg, emoji_ready)

    # Verify match has started, we can stop here.
    matcher = PickStageMatcher()
    async with pbot.message() as msg:
        assert matcher.match_start(msg.content)


async def test_require_ready_not_ready(pbot, pickup):
    players = pbot.members[: pickup.players]

    # Set up pug
    for player in players:
        await pbot.send_message("!j elim", player)
        await pbot.get_message()

    for _ in range(pickup.players):
        await pbot.get_message()

    await pbot.get_message()

    # Verify bot spits out a sentinel message, because reasons
    ready_msg = None
    async with pbot.message() as msg:
        match = simple_match("!spawn_message {match_id}", msg.content)
        assert match
        ready_msg = msg

    # Give the bot a bit of time to edit it's own message
    await asyncio.sleep(0.005)

    # Match ready string
    assert (match := ready_message_pattern.match(ready_msg.content))

    # Have at least one player react with :no_entry:
    not_ready_player = players[2]
    await pbot.react(not_ready_player, ready_msg, emoji_abort)

    # Verify reset
    async with pbot.message() as msg:
        assert (match := not_ready_message_pattern.match(msg.content))
        assert match["user"] == not_ready_player.nick

    async with pbot.message() as msg:
        assert (match := simple_match("[**{game}** ({current}/{total})]", msg.content))
        assert match["current"] == "7"
        assert match["total"] == "8"


async def test_require_ready_auto_backfill(pbot, pickup):
    players = pbot.members[: pickup.players]
    extra_player = pbot.members[pickup.players]

    # Set up pug
    for player in players:
        await pbot.send_message("!j elim", player)
        await pbot.get_message()

    for _ in range(pickup.players):
        await pbot.get_message()

    await pbot.get_message()

    # Verify bot spits out a sentinel message, because reasons
    ready_msg = None
    async with pbot.message() as msg:
        match = simple_match("!spawn_message {match_id}", msg.content)
        assert match
        ready_msg = msg

    # Give the bot a bit of time to edit it's own message
    await asyncio.sleep(0.005)

    # Match ready string
    assert ready_message_pattern.match(ready_msg.content)

    # Have an extra player join
    async with pbot.interact("!j elim", extra_player) as msg:
        assert simple_match("[**{game}** (1/{total})]", msg.content)

    # Have everyone ready but one player
    for p in players[:-1]:
        await pbot.react(p, ready_msg, emoji_ready)

    await pbot.react(players[-1], ready_msg, emoji_abort)

    async with pbot.message() as msg:
        assert not_ready_message_pattern.match(msg.content)

    # Player should get another DM
    players = players[:-1] + [extra_player]
    for player in players:
        async with pbot.message() as msg:
            assert isinstance(msg.channel, discord.DMChannel)
            assert msg.channel.recipient.id == player.id

    async with pbot.message() as msg:
        assert "[**no pickups**]" in msg.content

    # Should get a new ready message for updated players
    async with pbot.message() as msg:
        assert (match := simple_match("!spawn_message {match_id}", msg.content))
        ready_msg = msg

    # Give the bot a bit of time to edit it's own message
    await asyncio.sleep(0.005)

    # Match ready string
    assert (match := ready_message_pattern.match(ready_msg.content))

    # Verify waiting on list only includes players that joined
    assert [p.id for p in players] == [
        int(x) for x in id_pattern.findall(match["waiting_list"])
    ]
