import pytest
import pytest_asyncio
import time
import asyncio

from typing import List, Optional, Iterable, Union, Any, Dict

import discord
import discord.ext.test as dpytest

from pubobot import console, scheduler, bot, stats3, config, client


@pytest_asyncio.fixture
async def pbot_client(tmp_path):
    # Recreate client with the pytest-asyncio event loop
    client.c = client.create_client(asyncio.get_running_loop())

    # Always use a clean database
    db = tmp_path / "db.sqlite3"

    console.init(enable_input=False)
    scheduler.init()
    bot.init()
    stats3.init(db)
    config.init()
    client.init()

    dpytest.configure(client.c, num_guilds=0, num_channels=0, num_members=0)

    async def run_background_tasks():
        while True:
            if not console.alive:
                await client.close()
                break

            frametime = time.time()
            bot.run(frametime)
            scheduler.run(frametime)
            console.run()

            await client.send()
            await asyncio.sleep(0.001)

    loop = asyncio.get_running_loop()
    background_task = loop.create_task(run_background_tasks())

    yield client.c

    console.terminate()
    await background_task
    await dpytest.empty_queue()


@pytest_asyncio.fixture
async def pbot(request, pbot_client):
    scenario = request.node.get_closest_marker("scenario")
    if scenario is None:
        guild = "DefaultGuild"
        channel = "General"
        members = 10
    else:
        guild = scenario.kwargs.get("guild", "DefaultGuild")
        channel = scenario.kwargs.get("channel", "General")
        members = scenario.kwargs.get("members", 10)

    context = Context.create(client.c, guild, channel, members)
    messenger = Messenger(context, pbot_client, loop=pbot_client.loop)
    return messenger


class Context:
    def __init__(
        self,
        guild: discord.Guild,
        channel: discord.TextChannel,
        admin: discord.Member,
        members: Iterable[discord.Member],
    ):
        self.guild = guild
        self.channel = channel
        self.admin = admin
        self.members = list(members)

    @classmethod
    def create(
        cls,
        client: discord.Client,
        guild_name: str,
        channel_name: str,
        member_count: int,
    ) -> "Context":
        guild = dpytest.back.make_guild(guild_name)  # type: ignore

        assert client.user
        dpytest.back.make_member(
            dpytest.back.get_state().user, guild, nick=client.user.name + f"_nick"
        )

        channel = dpytest.back.make_text_channel(channel_name, guild)

        admin_role = dpytest.back.make_role("admin", guild, permissions=8)
        admin_user = dpytest.back.make_user(f"{guild_name}Admin", "0001")
        admin = dpytest.back.make_member(
            admin_user, guild, nick=admin_user.name, roles=[admin_role]
        )

        members = []
        for i in range(member_count):
            user = dpytest.back.make_user(f"{guild_name}User{str(i)}", f"{i+1:04}")
            member = dpytest.back.make_member(
                user, guild, nick=user.name + f"_{str(i)}_nick"
            )
            members.append(member)

        return Context(guild, channel, admin, members)


class Messenger:
    def __init__(
        self,
        context: Context,
        client: discord.Client,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ):
        self.context = context
        self.client = client
        self.loop = loop or asyncio.get_running_loop()

    @property
    def guild(self) -> discord.Guild:
        return self.context.guild

    @property
    def channel(self) -> discord.TextChannel:
        return self.context.channel

    @property
    def members(self) -> Iterable[discord.Member]:
        return self.context.members

    @property
    def admin(self) -> discord.Member:
        return self.context.admin

    def interact(
        self, msg: str, member: Union[discord.Member, int] = 0, collect: int = 1
    ):
        return Interaction(msg, member, collect, self, self.loop)

    def message(self, collect: int = 1):
        return Message(collect, self, self.loop)

    async def react(
        self,
        user: Union[int, discord.user.BaseUser, discord.abc.User],
        message: discord.Message,
        emoji: str,
    ):
        if isinstance(user, int):
            user = self.context.members[user]
        return await dpytest.add_reaction(user, message, emoji)

    async def empty_queue(self):
        return await dpytest.empty_queue()

    async def send_message(self, msg: str, member: Union[discord.Member, int] = 0):
        if isinstance(member, int):
            member = self.context.members[member]

        assert isinstance(member, discord.Member)

        await dpytest.message(
            msg,
            channel=self.context.channel,
            member=member,
        )

    async def get_message(self, peek=False, timeout=0.5) -> discord.Message:
        start = time.time()
        while dpytest.sent_queue.empty() and time.time() - start < timeout:
            await asyncio.sleep(0.001)

        if dpytest.sent_queue.empty():
            raise TimeoutError()

        if peek:
            return dpytest.sent_queue.peek()

        return dpytest.sent_queue.get_nowait()


class Message:
    def __init__(
        self,
        collect: int,
        messenger: Messenger,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ):
        self.messenger = messenger
        self.loop = loop or asyncio.get_running_loop()
        self.collect = collect
        self.responses: List[discord.Message] = []

    async def __aenter__(self):
        for _ in range(self.collect):
            msg = await self.messenger.get_message()
            self.responses.append(msg)

        if self.collect == 1:
            return self.responses[0]

        return self.responses

    async def __aexit__(self, exc_type, exc_value, tb):
        pass


class Interaction(Message):
    def __init__(
        self,
        message: str,
        member: Union[discord.Member, int],
        collect: int,
        messenger: Messenger,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ):
        super().__init__(collect, messenger, loop)
        self.message = message
        self.member = member

    async def __aenter__(self):
        await self.messenger.send_message(self.message, member=self.member)
        return await super().__aenter__()


async def setup_pickup(messenger: Messenger, pickup: Any):
    name = pickup.kwargs.get("name", "game")
    count = pickup.kwargs.get("players", 8)
    config = pickup.kwargs.get("config", {})

    async with messenger.interact("!enable_pickups", messenger.admin):
        pass

    async with messenger.interact(f"!add_pickups {name}:{count}", messenger.admin):
        pass

    for k, v in config.items():
        async with messenger.interact(f"!set_pickups {name} {k} {v}", messenger.admin):
            pass


class Pickup:
    def __init__(self, name: str, players: int, config: Dict[str, str]):
        self.name = name
        self.players = players
        self.config = config


@pytest_asyncio.fixture
async def pickup(request, pbot):
    marker = request.node.get_closest_marker("pickup")
    if marker is None:
        name = "game"
        players = 8
        config = {}
    else:
        name = marker.kwargs.get("name", "game")
        players = marker.kwargs.get("players", 8)
        config = marker.kwargs.get("config", {})

    async with pbot.interact("!enable_pickups", pbot.admin):
        pass

    async with pbot.interact(f"!add_pickups {name}:{players}", pbot.admin):
        pass

    for k, v in config.items():
        async with pbot.interact(f"!set_pickups {name} {k} {v}", pbot.admin):
            pass

    return Pickup(name, players, config)
